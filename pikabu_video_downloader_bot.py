import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import MessageNotModified, MessageToEditNotFound, MessageToDeleteNotFound, BotBlocked, MessageCantBeDeleted
import sqlite3
from module.database import get_queue_count, set_status, DB_TABLE_FILES, DB_TABLE_PROCESS, DB
from module.log import log
from module.env import env_ch_id, env_bot_token
import cv2


bot = Bot(env_bot_token())
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

CH_ID = env_ch_id()


def url_exist(url: str) -> bool | int:
    cx = sqlite3.connect(DB)
    cu = cx.cursor()
    cu.execute(f'SELECT id FROM {DB_TABLE_FILES} WHERE link_page = ?;', (url,))
    row = cu.fetchone()
    cx.close()
    if row is None:
        return False
    return row[0]


def add_new_link(url: str, from_id: int, message_id: int) -> int:
    cx = sqlite3.connect(DB)
    cu = cx.cursor()
    cu.execute(f'INSERT INTO {DB_TABLE_PROCESS} (link_page, from_id, message_id, status_id) VALUES (?,?,?,?);', (url, from_id, message_id, 0))
    cx.commit()
    # return get_queue_count()


def delete_files(id):
    fn_html = f'./files/{id}.html'
    fn_mp4 = f'./files/{id}.mp4'
    os.remove(fn_html)
    os.remove(fn_mp4)


@dp.message_handler(commands="start")
async def cmd_test1(message: types.Message):
    await message.reply(f'Пришли ссылку на страницу Пикабу с видео\nОчередь: {get_queue_count()}')


def is_pikabu(url: str) -> bool:
    result = False
    if url.startswith('https://pikabu.ru/story/'):
        result = True
    return result


@dp.message_handler(content_types=[types.ContentType.TEXT])
async def any_text(message: types.Message):
    from_id = message.from_user.id
    for entity in message.entities:
        if entity.type == 'url':
            url = message.text[entity.offset:entity.offset+entity.length]
            if not is_pikabu(url):
                await message.answer('Это ссылка не на пост Пикабу, а куда-то ещё...')
                return
            bot_message = await message.answer(url)
            message_id = bot_message.message_id
            file_id = url_exist(url)
            if not file_id:
                await bot_message.edit_text('Ранее не скачивалось')
                add_new_link(url, from_id, message_id)
                await bot_message.edit_text(f'Добавлено в очередь. В очереди - {get_queue_count()}')
            else:
                await bot_message.edit_text('Ранее скачивалось')
                await send_from_channel(file_id, from_id)
            


async def send_from_channel(file_id, from_id):
    cx = sqlite3.connect(DB)
    cu = cx.cursor()
    cu.execute(f'SELECT message_id FROM {DB_TABLE_FILES} WHERE id = ?;', (file_id,))
    row = cu.fetchone()
    if row is None:
        return None
    message_id = row[0]
    await bot.forward_message(
                chat_id=from_id,
                from_chat_id=CH_ID,
                message_id=message_id
            )


async def update_status():
    cx = sqlite3.connect(DB)
    cu = cx.cursor()
    cu.execute(f'SELECT id, link_page, status_id, from_id, message_id FROM {DB_TABLE_PROCESS};')
    rows = cu.fetchall()
    for row in rows:
        process_id, link_page, status_id, from_id, message_id = row
        if status_id < 5:
            try:
                await bot.edit_message_text(
                    text=f'{link_page}\nСтатус: {status_id}\nОчередь: {get_queue_count()}',
                    chat_id=from_id,
                    message_id=message_id
                )
            except MessageNotModified:
                pass
            except (MessageToEditNotFound, MessageToDeleteNotFound) as error:
                log(error, 'ERROR')
                set_status(process_id, 6)
                status_id = 6j
        if status_id == 3:
            try:
                set_status(process_id, 4)
                filename = f'./files/{process_id}.mp4'
                filesize = os.stat(filename).st_size / (1024 * 1024)
                if filesize >= 50:
                    set_status(process_id, 5)
                else:
                    log(f'start upload to channel {filename}')
                    cv2video = cv2.VideoCapture(filename)
                    height = cv2video.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    width  = cv2video.get(cv2.CAP_PROP_FRAME_WIDTH)
                    
                    ch_message = await bot.send_video(
                        chat_id=CH_ID,
                        # chat_id=from_id,
                        video=open(filename, 'rb'),
                        caption=link_page,
                        height=height,
                        width=width
                    )
                    delete_files(process_id)
                    ch_id = ch_message.message_id
                    log(f'end upload {ch_id}')
                    cu.execute(f'INSERT INTO {DB_TABLE_FILES} (message_id, link_page) VALUES (?,?);', (ch_id, link_page,))
                    cu.execute(f'DELETE FROM {DB_TABLE_PROCESS} WHERE id = ?;', (process_id,))
                    cx.commit()
                    cu.execute(f'SELECT id FROM {DB_TABLE_FILES} WHERE link_page = ?;', (link_page,))
                    file_id = cu.fetchone()[0]
                    try:
                        await bot.delete_message(chat_id=from_id, message_id=message_id)
                        await send_from_channel(file_id, from_id)
                    except (BotBlocked, MessageCantBeDeleted):
                        pass
            except FileNotFoundError:
                log(f'{filename} не найден', 'WARN')
                set_status(process_id, 7)
    cx.close()


async def scheduler():
    while True:
        await update_status()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
