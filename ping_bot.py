import os
import json
import asyncio
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot
from telegram.error import TelegramError

# 🔐 Настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SPREADSHEET_ID = "1DpbYJ5f6zdhIl1zDtn6Z3aCHZRDFTaqhsCrkzNM9Iqo"
CHECK_INTERVAL = 300  # 5 минут

# ✅ Авторизация в Google Sheets
creds_json = os.getenv("GOOGLE_CREDENTIALS")
creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
])
client = gspread.authorize(creds)

log_sheet = client.open_by_key(SPREADSHEET_ID).worksheet("Changes Log")

# 📦 Переменная для хранения уже увиденных записей
seen_changes = set()

async def check_changes():
    while True:
        try:
            values = log_sheet.get_all_values()[1:]  # Пропускаем заголовок

            for row in values:
                if len(row) >= 4:
                    date, change_type, app_number, package = row

                    # Проверяем только "Приложение вернулось в стор"
                    if change_type == "Приложение вернулось в стор":
                        row_id = f"{date}-{app_number}-{package}"
                        if row_id not in seen_changes:
                            seen_changes.add(row_id)

                            message = f"📲 Приложение вернулось в стор!\n\nНомер: {app_number}\nСсылка: https://play.google.com/store/apps/details?id={package_name}"
                            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


        except Exception as e:
            print(f"❌ Ошибка при проверке изменений: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

async def send_notification(text):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode="Markdown")
        print("✅ Уведомление отправлено.")
    except TelegramError as e:
        print(f"❌ Ошибка при отправке уведомления: {e}")

if __name__ == "__main__":
    asyncio.run(check_changes())
