import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.builtin import IDFilter
from config import API_TOKEN

logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

ADMINS = IDFilter(['495172638', '475495684'])


def message_handler_admin(*args, **kwargs):
    args = tuple([ADMINS]+list(args))
    func = dp.message_handler(*args, **kwargs)
    return func


@message_handler_admin()
async def echo(message: types.Message):
    # old style:
    # await bot.send_message(message.chat.id, message.text)
    await message.reply(message.text, reply=False)



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
