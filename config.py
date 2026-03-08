import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [1600643157]  # Список ID администраторов бота
CHANNEL_ID = "@neuralhubai" # ID канала для публикации новостей (можно указать username канала)