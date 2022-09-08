import exceptions
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
import bookmarks
import os

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(bot)

def get_keyboard_del(bookmarks_user: tuple) -> tuple:
    '''Генерация клавиатуры для удаления закладки'''
    keyboard_markup = types.InlineKeyboardMarkup(row_width=1)
    buttons = (types.InlineKeyboardButton(text=bookmark[1], callback_data=f'del_{bookmark[0]}')
               for bookmark in bookmarks_user)
    keyboard_markup.add(*buttons)
    return keyboard_markup

def get_keyboard_mangas(bookmarks_user: tuple) -> tuple:
    '''Генерация клавиатуры с ссылками на мангу'''
    keyboard_markup = types.InlineKeyboardMarkup(row_width=1)
    buttons = (types.InlineKeyboardButton(text=f'{bookmark[1]}.\nГлава {bookmark[2]}',
                                          url=bookmark[3])
            for bookmark in bookmarks_user)
    keyboard_markup.add(*buttons)
    return keyboard_markup

answers_comands = {
    'all': ('Ваш список закладок:', get_keyboard_mangas),
    'del': ('Выберите закладку, которую хотите удалить:', get_keyboard_del)
    }

@dp.message_handler(commands=['start','help'])
async def process_start_command(message: types.Message):
    await message.answer(
        "Привет! Я бот для уведомления о выходе новых главах манги\n\n"
        "Для добавления напиши мне ссылку на мангу\n"
        "Для удаления набери /del и выбери мангу, которую хочешь удалить\n"
        "Для вывода списка ваших закладок набери /all\n"
        "Приятного пользования"
        )

@dp.message_handler(commands=['del','all'])
async def get_list_bookmarks(message: types.Message):
    bookmarks_user = await bookmarks.get_bookmarks_user(message.chat.id)
    if not bookmarks_user:
        await message.answer("У вас пока нет манги в закладках =(")

    await message.answer(answers_comands[message.text[1:4]][0],
                         reply_markup=answers_comands[message.text[1:4]][1](bookmarks_user))

@dp.callback_query_handler(Text(startswith='del_'))
async def callbacks_del_bookmark(call: types.CallbackQuery):
    answer_message = await bookmarks.delete_bookmark(call.from_user.id, call.data[4:])
    await call.answer(answer_message,show_alert=True)

@dp.message_handler()
async def add_bookmark(message: types.Message):
    try:
        answer_message = await bookmarks.add_bookmark(message.chat.id, message.text)
    except (exceptions.NotCorrectMessage, exceptions.NotCorrectUrl,
            exceptions.TechnicalWorks, exceptions.MangaStoppedReleased,
            exceptions.MangaComplete) as exc:
        await message.answer(str(exc))
        return
    await message.answer(answer_message)

async def send_notify(chat_id: int, message: str):
    await bot.send_message(chat_id, message, parse_mode=types.ParseMode.HTML)

if __name__ == '__main__':
    executor.start_polling(dp)
