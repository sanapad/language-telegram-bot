import logging
from aiogram.utils import executor
from create_bot import dp
from handlers import client, other
from data_base import sqlite_db

# set basic logging config
# noinspection SpellCheckingInspection
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    filename='logs.log'
)


# actions when the bot starts
async def on_startup(_):
    logging.info(f'Bot is online')
    sqlite_db.sql_start()

# handlers registration
client.register_handlers(dp)
other.register_handlers(dp)

# handle each message from Telegram servers: skip_updates=False. It's for payments processing
try:
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
finally:
    logging.info(f'Bot is OFF')
