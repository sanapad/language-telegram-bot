import config
from aiogram import Bot
from aiogram.dispatcher import Dispatcher

# it allows to keep data in RAM
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()

# create bot instance
bot = Bot(token=config.TOKEN)  # You can do it through environment variable: token=os.getenv('TOKEN'))
dp = Dispatcher(bot, storage=storage)
