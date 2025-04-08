import os
import json
import asyncio
import logging
from datetime import datetime
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 🔧 Настройка логгирования
logging.basicConfig(level=logging.INFO)

# 🔐 Переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
SPREADSHEET_ID = "1DpbYJ5f6zdhIl1zDtn6Z3aCHZRDFTaqhsCrkzNM9Iqo"

# 👥 Список пользователей, которым можно отправлять уведомления
ALLOWED_USERS = [929686990, 6066119769]

# 🧠 Храним последние известные записи, чтобы избежать дублей
known_log_entries = set()

# 📊 Подключение к Google Sheets
def get_log_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS, [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ])
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return spreadsheet.worksheet("Changes Log")

# 🔁 Проверка новых записей
async def check_for_updates(context):
    try:
        log_sheet = get_log_sheet()
        rows = log_sheet.get_all_values()[1:]  # пропускаем заголовки
        new_entries = []

        for row in rows:
            if len(row) < 4:
                continue

            log_date, change_type, app_number, package_name = row

            # Проверка на новый тип записи
            if change_type == "Приложение вернулось в стор":
                unique_key = f"{log_date}-{change_type}-{app_number}-{package_name}"
                if unique_key not in known_log_entries:
                    known_log_entries.add(unique_key)
                    new_entries.append((app_number, package_name))

        # Отправка уведомлений
        for app_number, package_name in new_entries:
            message = f"📲 Приложение {app_number} вернулось в стор:\nhttps://play.google.com/store/apps/details?id={package_name}"
            for user_id in ALLOWED_USERS:
                try:
                    await context.bot.send_message(chat_id=user_id, text=message)
                    logging.info(f"✅ Отправлено сообщение пользователю {user_id}")
                except Exception as e:
                    logging.error(f"❌ Ошибка при отправке {user_id}: {e}")

    except Exception as e:
        logging.error(f"❌ Ошибка при проверке таблицы: {e}")

# 🧪 Команда /me для проверки chat_id
async def me_command(update, context):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"👤 Твой chat_id: {chat_id}")

# 🚀 Основной запуск бота
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("me", me_command))

    # Планировщик: проверка каждые 5 минут
    app.job_queue.run_repeating(check_for_updates, interval=300, first=5)

    logging.info("✅ Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())

