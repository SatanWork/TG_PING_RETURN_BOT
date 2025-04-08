import os
import json
import gspread
import telegram
import time
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from telegram.ext import Updater, CommandHandler

# ==== Настройки ====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
SPREADSHEET_ID = "1DpbYJ5f6zdhIl1zDtn6Z3aCHZRDFTaqhsCrkzNM9Iqo"
CHECK_INTERVAL = 60  # интервал проверки в секундах
chat_ids = set()  # Сюда будут сохраняться chat_id всех, кто писал боту

# ==== Подключение к Google Sheets ====
creds_dict = json.loads(GOOGLE_CREDENTIALS)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
])
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet("Changes Log")

# ==== Telegram боты ====
bot = telegram.Bot(token=TELEGRAM_TOKEN)

def start(update, context):
    chat_id = update.effective_chat.id
    chat_ids.add(chat_id)
    context.bot.send_message(chat_id=chat_id, text="Вы подписаны на уведомления о возвращённых приложениях.")

# ==== Хранилище уже отправленных записей ====
notified = set()

# ==== Проверка Google Sheets ====
def check_for_updates():
    try:
        data = sheet.get_all_values()[1:]  # Пропускаем заголовки
        for row in data:
            if len(row) >= 4:
                date, change_type, app_number, package = row
                if change_type == "Приложение вернулось в стор":
                    key = f"{date}|{app_number}|{package}"
                    if key not in notified:
                        notified.add(key)
                        send_notification(app_number, package)
    except Exception as e:
        print(f"Ошибка при проверке таблицы: {e}")

# ==== Отправка уведомления ====
def send_notification(app_number, package_name):
    message = f"🔔 <b>{app_number}</b> вернулось в стор!\nhttps://play.google.com/store/apps/details?id={package_name}"
    for chat_id in chat_ids:
        try:
            bot.send_message(chat_id=chat_id, text=message, parse_mode=telegram.ParseMode.HTML)
        except Exception as e:
            print(f"❌ Не удалось отправить сообщение в чат {chat_id}: {e}")

# ==== Запуск Telegram бота ====
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()

    print("✅ Бот запущен и следит за таблицей.")
    while True:
        check_for_updates()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
