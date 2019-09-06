import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import filters, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import API_TOKEN
import json
import os
import threading
from urllib.parse import urlsplit
import subprocess

logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

ADMINS = filters.IDFilter(['495172638', '475495684'])
CONFIG = json.load(open('config.json'))
PATH = State(CONFIG['path'])
MONGO_URI = State(CONFIG['mongo_uri'])
LOCK = threading.Lock()
UPLOAD = State()


def message_handler_admin(*args, **kwargs):
    args = tuple([ADMINS]+list(args))
    func = dp.message_handler(*args, **kwargs)
    return func

# You can use state '*' if you need to handle all states
@message_handler_admin(state='*', commands='cancel')
@message_handler_admin(filters.Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return
    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@message_handler_admin(commands=['ll'])
async def ll(message: types.Message):
    pth = os.path.expanduser(os.path.expandvars(CONFIG['path']))
    r = subprocess.run(['ls -alF'],text=True, capture_output=True, cwd=pth, shell=True)
    await message.reply(r.stdout)

@message_handler_admin(commands=['ls'])
async def ls(message: types.Message):
    pth = os.path.expanduser(os.path.expandvars(CONFIG['path']))
    r = subprocess.run(['ls'],text=True, capture_output=True, cwd=pth, shell=True)
    await message.reply(r.stdout)


@message_handler_admin(commands=['settings'])
async def settings(message: types.Message):
    btn = types.KeyboardButton(text='Path')
    btn2 = types.KeyboardButton(text='MongoDB URI')
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    mk.insert(btn)
    mk.insert(btn2)
    await message.answer('PATH: {0}\nMongoDB URI: {1}'.format(CONFIG['path'],CONFIG['mongo_uri']), reply_markup=mk)

@message_handler_admin(lambda message: message.text=='Path')
async def settings_path(message: types.Message):
    await PATH.set()
    await message.answer('Set path:')

@message_handler_admin(state=PATH)
async def process_path(message: types.Message, state: FSMContext):
    """
    Process user path
    """
    global CONFIG
    current_state = await state.get_state()
    if current_state is None:
        return
    async with state.proxy() as data:
        if not os.path.exists(os.path.expanduser(os.path.expandvars(message.text))):
            return await message.reply('Path don\'t exist in server.')
        with LOCK:
            data.state = message.text
            CONFIG['path'] = message.text
            json.dump(CONFIG, open('config.json', 'w'), indent=4)
    await message.reply('Path set correct')
    await state.finish()

@message_handler_admin(lambda message: message.text=='MongoDB URI')
async def settings_mu(message: types.Message):
    await MONGO_URI.set()
    await message.answer('Set MongoDB URI:')

@message_handler_admin(state=MONGO_URI)
async def process_mu(message: types.Message, state: FSMContext):
    """
    Process user path
    """
    global CONFIG
    current_state = await state.get_state()
    if current_state is None:
        return
    async with state.proxy() as data:
        parts = urlsplit(message.text)
        if parts.scheme=='' or parts.netloc=='':
            return await message.reply('Icorrect MongoDB URI.')
        with LOCK:
            data.state = message.text
            CONFIG['mongo_uri'] = message.text
            json.dump(CONFIG, open('config.json', 'w'), indent=4)
    await message.reply('MongoDB URI set correct')
    await state.finish()


@message_handler_admin(commands=['upload'])
async def upload(message: types.Message):
    await UPLOAD.set()
    await message.reply('Write path to upload file, can be relative tu the path in configuration.')

@message_handler_admin(state=UPLOAD)
async def process_upload(message: types.Message, state: FSMContext):
    """
    Process user path
    """
    current_state = await state.get_state()
    if current_state is None:
        return
    with LOCK:
        pth2 = os.path.join(CONFIG['path'], os.path.expanduser(os.path.expandvars(message.text)))
        pth2 = os.path.expanduser(os.path.expandvars(pth2))
    pth = message.text
    if not os.path.exists(os.path.expanduser(os.path.expandvars(message.text))):
        if not os.path.exists(pth2):
            return await message.reply('Path don\'t exist in server.')
        pth = pth2
    filee = types.InputFile(pth)
    r = await bot.send_document('-1001436529356,', filee)
    print(r)
    # agregar aqui lo de guardar en mongo el fichero subido
    await message.reply('Upload correct correct')
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
