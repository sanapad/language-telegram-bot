import logging

from aiogram import types, Dispatcher

import config
from create_bot import bot
from data_base import sqlite_db


async def start_handler(message: types.Message):
    # logging
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'id:{user_id} full_name:{user_full_name} action:start')

    # FOR DEVELOPMENT access is for only admin
    if config.DEBUG:
        if user_id != config.ADMIN_ID:
            print("access is not allowed")
            return

    sqlite_db.sql_start()
    sqlite_db.give_balance(user_id, user_full_name, 10000)
    sqlite_db.sql_stop()

    await message.reply(f'Hi, {user_full_name}! I\'m a bot using ChatGPT. Each new '
                        f'user will be credited with {config.STARTING_BALANCE} tokens as a gift. To '
                        f'start, just ask me anything.\n')


async def help_handler(message: types.Message):
    # noinspection PyPep8
    text = '''I'm glad you reached out for help. Here is a list of commands I can run:
🤖 /help - show a list of available commands (you're here now)
🔄 /reset - reset our conversation history. If you want to start a dialog with me from scratch, use this command
💳 /balance - current balance and top up money
💬 /support - contact support. If you have any questions or problems, don't hesitate to contact us. We are always ready to help! 😊'''

    await message.reply(text)

    # logging
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'id:{user_id} full_name:{user_full_name} action:help')


async def support_handler(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'id:{user_id} full_name:{user_full_name} action:support')

    await bot.send_message(user_id, 'Do you have any questions? Write to us, we will be happy to answer:\n\n' +
                           config.LINK_TO_SUPPORT)


async def reset_handler(message: types.Message):
    user_id = message.from_user.id

    # reset context
    sqlite_db.sql_start()
    sqlite_db.reset_context(user_id)
    sqlite_db.sql_stop()

    await message.reply('Context is dropped')

    # logging
    user_full_name = message.from_user.full_name
    logging.info(f'id:{user_id} full_name:{user_full_name} action:reset')


async def balance_handler(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'id:{user_id} full_name:{user_full_name} action:balance')

    sqlite_db.sql_start()
    balance = sqlite_db.get_balance((user_id,))
    sqlite_db.sql_stop()

    await bot.send_message(user_id, f'Your balance: {balance}')


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_handler, commands=['start'])
    dp.register_message_handler(help_handler, commands=['help'])
    dp.register_message_handler(support_handler, commands=['support'])
    dp.register_message_handler(reset_handler, commands=['reset'])
    dp.register_message_handler(balance_handler, commands=['balance'])
