import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
# from aiogram.exceptions import MessageNotModified, MessageToEditNotFound, MessageToDeleteNotFound, BotBlocked, MessageCantBeDeleted, UserDeactivated
from aiogram.exceptions import TelegramAPIError, TelegramNotFound, TelegramBadRequest
from aiogram.types import FSInputFile, BotName
from module.async_database import get_all_in_process, get_file_id, get_one_in_process, get_queue_len, set_status, url_exist, add_link_to_queue, get_channel_message_id, delete_from_files
from module.log import log
from module.env import env_ch_id, env_bot_token
import cv2
from random import random

logging.basicConfig(level=logging.INFO)


bot = Bot(env_bot_token())
dp = Dispatcher()
CH_ID = env_ch_id()
status = {
    0: "Added",
    1: "Finding",
    2: "Downloading",
    3: "Downloaded",
    4: "Uploading"
}


def delete_files(id):
    fn_html = f'./files/{id}.html'
    fn_mp4 = f'./files/{id}.mp4'
    if os.path.exists(fn_html):
        os.remove(fn_html)
    if os.path.exists(fn_mp4):        
        os.remove(fn_mp4)


@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    await message.reply(f'Пришли ТОЛЬКО ссылку на пост Пикабу с видео\nОчередь: {await get_queue_len()}')


@dp.message(F.text)
async def any_text(message: types.Message):
    if message.entities is None: 
        return
    if message.entities[0].type != 'url':
        return
    url = message.entities[0].extract_from(message.text)

    if not url.startswith('https://pikabu.ru/story/'):
        await message.answer('Это ссылка не на пост Пикабу, а что-то ещё...')
        return
    
    # Отрезаем хвост урла с параметрами 
    pos_question = url.find('?')
    if pos_question != -1:
        url = url[:pos_question]
    
    # await message.answer(url)
    bot_message = await message.answer('Работаем...')
    
    from_id = message.from_user.id
    
    file_id = await url_exist(url)
    if file_id is None:
        await add_link_to_queue(url, from_id, bot_message.message_id)
        await bot_message.edit_text(f'Добавлено в очередь\nВ очереди {await get_queue_len()}, придётся немного подождать')
    else:
        await bot_message.delete()
        await send_from_channel(file_id, from_id)
            


async def send_from_channel(file_id, from_id):
    message_id = await get_channel_message_id(file_id)
    try:
        await bot.forward_message(
                    chat_id=from_id,
                    from_chat_id=CH_ID,
                    message_id=message_id
                )
    except TelegramBadRequest as e:
        if e.message == 'Bad Request: MESSAGE_ID_INVALID': # не найдено на канале
            bot_message = await bot.send_message(
                from_id, 'oops, i did it again'
            )
            # Удалить из бд
            url = await delete_from_files(file_id)
            # Добавить в очередь на загрузку
            if url is not None:
                await add_link_to_queue(url, from_id, bot_message.message_id)
            


async def update_status():
    row = await get_one_in_process()
    if row is None:
        return
    
    process_id, link_page, status_id, from_id, message_id = row
    
    await log(f'В работе: {process_id}, статус {status_id}...')
    try:
        await bot.edit_message_text(
            text=f'{link_page}\nСтатус: {status_id}\nОчередь: {await get_queue_len()}\n{random()}',
            chat_id=from_id,
            message_id=message_id
        )
    except TelegramBadRequest as e:
        print(e)
        if e.message == 'Bad Request: message to edit not found':
            await set_status(process_id, 13)
        return

    if status_id == 3:
        await set_status(process_id, 4)
        filename = f'./files/{process_id}.mp4'
        if not os.path.exists(filename):
            await log(f'{filename} не найден', 'WARN')
            await set_status(process_id, 7)
            return
        filesize = os.stat(filename).st_size / (1024 * 1024)
        if filesize >= 50:
            await set_status(process_id, 5)
            return
        await log(f'Загружаю на канал {filename}')
        cv2video = cv2.VideoCapture(filename)
        height = cv2video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        width  = cv2video.get(cv2.CAP_PROP_FRAME_WIDTH)
        # TODO получить продолжительность видео и передавать её в тг при загрузке
        # dur = cv2video.get(cv2.CAP_PROP_)
        ch_message = None
        try:
            bot_me = await bot.get_me()
            ch_message = await bot.send_video(
                chat_id=CH_ID,
                video=FSInputFile(path=filename),
                caption=f'{link_page}\n@{bot_me.username}', # TODO добавить ссылку на бота
                height=height,
                width=width
            )
        except Exception as e:
            await set_status(process_id, 10)
            await log(e, 'ERROR on uploading')
        delete_files(process_id)

        if ch_message is None:
            await log(f'{process_id} не был загружен в канал')
            return
        
        ch_id = ch_message.message_id
        await log(f'Загрузил {ch_id}')
        file_id = await get_file_id(ch_id, link_page, process_id)
        try:
            await bot.delete_message(chat_id=from_id, message_id=message_id)
            await send_from_channel(file_id, from_id)
        except TelegramAPIError as e:
            await log(e, 'ERROR (delete and send from channel)')
            pass


async def scheduler():
    while True:
        try:
            # await update_status()
            await update_status()
        except Exception as e:
            await log(e, 'ERROR (scheduler)')
        await asyncio.sleep(2)


async def start_bot():
    await dp.start_polling(bot)


async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(start_bot())
        tg.create_task(scheduler())


if __name__ == "__main__":
    asyncio.run(main())
