import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import MessageNotModified
import sqlite3
import aioschedule
from module.database import set_status
from module.env import env_db_filename
import cv2


bot = Bot(token=os.environ.get('BOT_TOKEN'))
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)


DB = env_db_filename()
DB_TABLE_PROCESS = 'process'
DB_TABLE_FILES = 'files'
CH_ID = '-1001889930255'


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
    count = cu.execute(f'SELECT COUNT(id) FROM {DB_TABLE_PROCESS};').fetchone()[0]
    cx.close()
    return count


def delete_files(id):
    fn_html = f'./files/{id}.html'
    fn_mp4 = f'./files/{id}.mp4'
    os.remove(fn_html)
    os.remove(fn_mp4)


@dp.message_handler(commands="start")
async def cmd_test1(message: types.Message):
    await message.reply("Пришли ссылку на страницу Пикабу с видео")


@dp.message_handler(content_types=[types.ContentType.TEXT])
async def any_text(message: types.Message):
    from_id = message.from_id
    for entity in message.entities:
        if entity.type == 'url':
            url = message.text[entity.offset:entity.offset+entity.length]
            bot_message = await message.answer(url)
            message_id = bot_message.message_id
            file_id = url_exist(url)
            if not file_id:
                await bot_message.edit_text('Ранее не скачивалось')
                count = add_new_link(url, from_id, message_id)
                await bot_message.edit_text(f'Добавлено в очередь. В очереди - {count}')
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
        try:
            await bot.edit_message_text(
                text=f'{link_page}\nСтатус: {status_id}',
                chat_id=from_id,
                message_id=message_id
            )
        except MessageNotModified:
            pass
        if status_id == 3:
            set_status(process_id, 4)
            filename = f'./files/{process_id}.mp4'
            print(f'start upload to channel {filename}')
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
            print(f'end upload {ch_id}')
            cu.execute(f'INSERT INTO {DB_TABLE_FILES} (message_id, link_page) VALUES (?,?);', (ch_id, link_page,))
            cu.execute(f'DELETE FROM {DB_TABLE_PROCESS} WHERE id = ?;', (process_id,))
            cx.commit()
            cu.execute(f'SELECT id FROM {DB_TABLE_FILES} WHERE link_page = ?;', (link_page,))
            file_id = cu.fetchone()[0]
            await send_from_channel(file_id, from_id)
    cx.close()


async def scheduler():
    aioschedule.every(10).seconds.do(update_status)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
