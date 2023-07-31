import openai
import config
from config import OPENAI_KEYS

current_index_openai_key = 0


def switch_openai_key():
    global current_index_openai_key
    current_index_openai_key += 1

    # begin the new cycle
    if current_index_openai_key >= len(config.OPENAI_KEYS):
        current_index_openai_key = 0


async def query(messages):
    openai.api_key = OPENAI_KEYS[current_index_openai_key]

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",

        # Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text
        # so far, increasing the model's likelihood to talk about new topics.
        presence_penalty=0.5,

        # Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the
        # text so far, decreasing the model's likelihood to repeat the same line verbatim.
        frequency_penalty=1.45,

        messages=messages
    )
    if config.DEBUG:
        print(messages)
        print(completion.choices[0].message.content.strip())
        print('------------------------------------------------------------------------------------------------')

    switch_openai_key()

    return completion
