import logging
import time
import openai
from aiogram import types, Dispatcher
import config
import query_to_openai
from data_base import sqlite_db

previous_request_time = {}


# any messages processing here
async def echo_send_handler(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    sqlite_db.sql_start()
    balance = sqlite_db.get_balance((user_id,))

    # check frequency queries from users
    if await spam_detect(message, user_id):
        return

    # start balance to user
    if balance is None:
        balance = config.STARTING_BALANCE

    # check the balance
    if int(balance) < 27:
        await message.reply("You do not have enough tokens. Refill your balance.")
        return

    # conditions are satisfied, the query will be continued
    await message.reply('Your request has been accepted')

    answer_from_database = sqlite_db.get_messages((user_id,))  # get current context

    # For setup GPT's role:
    if not answer_from_database:
        answer_from_database.append({"role": "system", "content": "you are an assistant"})

    answer_from_database.append({"role": "user", "content": message.text})

    # try to get the answer from OpenAI
    try:
        answer_from_openai = await query_to_openai.query(answer_from_database)

    # exception handling OpenAI
    except openai.error.InvalidRequestError as e:
        answer_from_openai = None
        if 'length' in str(e):
            await message.reply('Error: The maximum limit on the number of tokens has been exceeded.'
                                'The context has been cleared. Try again.')
            sqlite_db.reset_context(user_id)
            logging.info(f'id:{user_id} full_name:{user_full_name} OpenAI exception:maximum token limit')
        elif 'content_filter' in str(e):
            await message.reply('Error: the OpenAI filter was triggered.')
            logging.info(f'id:{user_id} full_name:{user_full_name} OpenAI exception:censorship')
        elif 'null' in str(e):
            await message.reply(
                'Error: The message is being processed by OpenAI or processing is not yet complete.')
            logging.info(f'id:{user_id} full_name:{user_full_name} OpenAI exception:processing is not finished')
        else:
            # other OpenAI API errors
            print("Error: ", e)

    # if there is a successful answer from OpenAI then continue
    if answer_from_openai:
        answer_from_database.append(
            {"role": "assistant", "content": answer_from_openai.choices[0].message.content})

        # spending tokens
        sqlite_db.spending_tokens(user_id,
                                  answer_from_database,
                                  user_full_name,
                                  balance,
                                  answer_from_openai.usage.completion_tokens,
                                  answer_from_openai.usage.prompt_tokens,
                                  answer_from_openai.usage.total_tokens)

        sqlite_db.sql_stop()

        # the answer to the user
        await message.reply(answer_from_openai.choices[0].message.content.strip())

        # logging
        logging.info(f' id:{user_id}'
                     f' full_name:{user_full_name}'
                     f' action:query'
                     f' completion_tokens:{answer_from_openai.usage.completion_tokens}'
                     f' prompt_tokens:{answer_from_openai.usage.prompt_tokens}'
                     f' total_tokens:{answer_from_openai.usage.total_tokens}'
                     f' query:{message.text}'
                     f' answer:{answer_from_openai.choices[0].message.content}')


async def spam_detect(message, user_id):
    global previous_request_time
    current_time = int(time.time())
    if user_id not in previous_request_time:
        previous_request_time[user_id] = 0
    if current_time - previous_request_time[user_id] < config.OPENAI_QUERY_TIMEOUT:
        await message.reply(f'A message cannot be sent more than once per {config.OPENAI_QUERY_TIMEOUT} seconds. '
                            f'Please, try again later.')
        return True
    else:
        previous_request_time[user_id] = current_time


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(echo_send_handler)
