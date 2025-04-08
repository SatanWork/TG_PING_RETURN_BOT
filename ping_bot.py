import os
import time
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot
from telegram.ext import Updater, CommandHandler

# 🛡 Авторизованные пользователи (chat_id или user_id)
AUTHORIZED_USERS = [929686990]

# 🔐 Телеграм токен
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TELEGRAM_TOKEN)

# 🔑 Google Sheets
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS, scope)
client = gspread.authorize(creds)

SPREADSHEET_ID = "1DpbYJ5f6zdhIl1zDtn6Z3aCHZRDFTaqhsCrkzNM9Iqo"
log_sheet = client.open_by_key(SPREADSHEET_ID).worksheet("Changes Log")

# 📦 Состояние (чтобы отслеживать последние отправленные)
last_sent = set()

# 🟢 Команда старт
def start(update, context):
    user_id = update.message.chat_id
    if user_id in AUTHORIZED_USERS:
        context.bot.send_message(chat_id=user_id, text="✅ Вы подписаны на уведомления.")
    else:
        context.bot.send_message(chat_id=user_id, text="❌ У вас нет доступа к этому боту.")

# 🔁 Проверка изменений
def check_changes(context):
    try:
        values = log_sheet.get_all_values()[1:]  # пропускаем заголовки
        new_entries = []

        for row in values[-30:]:  # проверяем только последние строки
            if len(row) < 4:
                continue
            date, change_type, app_number, package = row
            unique_id = f"{date}_{app_number}_{change_type}"

            if change_type == "Приложение вернулось в стор" and unique_id not in last_sent:
                new_entries.append((app_number, package))
                last_sent.add(unique_id)

        for app_number, package in new_entries:
            message = f"📱 Приложение вернулось в стор: {app_number}\nhttps://play.google.com/store/apps/details?id={package}"
            for user_id in AUTHORIZED_USERS:
                context.bot.send_message(chat_id=user_id, text=message)

    except Exception as e:
        print(f"❌ Ошибка при проверке изменений: {e}")

# 🚀 Запуск
def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    job_queue = updater.job_queue
    job_queue.run_repeating(check_changes, interval=60, first=5)  # Проверка каждые 60 сек

    updater.start_polling()
    print("✅ Бот запущен.")
    updater.idle()

if __name__ == "__main__":
    main()
