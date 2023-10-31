import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import MessageNotModified, MessageToEditNotFound, MessageToDeleteNotFound, BotBlocked, MessageCantBeDeleted, UserDeactivated
from module.async_database import get_all_in_process, get_file_id, get_queue_count, set_status, url_exist, add_new_link, get_channel_message_id
from module.log import log
from module.env import env_ch_id, env_bot_token
import cv2


bot = Bot(env_bot_token())
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

CH_ID = env_ch_id()


def delete_files(id):
    fn_html = f'./files/{id}.html'
    fn_mp4 = f'./files/{id}.mp4'
    if os.path.exists(fn_html):
        os.remove(fn_html)
    if os.path.exists(fn_mp4):        
        os.remove(fn_mp4)


@dp.message_handler(commands="start")
async def cmd_test1(message: types.Message):
    await message.reply(f'Пришли ссылку на страницу Пикабу с видео\nОчередь: {await get_queue_count()}')


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
            file_id = await url_exist(url)
            if not file_id:
                await bot_message.edit_text('Ранее не скачивалось')
                await add_new_link(url, from_id, message_id)
                await bot_message.edit_text(f'Добавлено в очередь. В очереди - {await get_queue_count()}')
            else:
                await bot_message.edit_text('Ранее скачивалось')
                await send_from_channel(file_id, from_id)
            


async def send_from_channel(file_id, from_id):
    message_id = await get_channel_message_id(file_id)
    await bot.forward_message(
                chat_id=from_id,
                from_chat_id=CH_ID,
                message_id=message_id
            )


async def update_status():
    rows = await get_all_in_process()
    for row in rows:
        process_id, link_page, status_id, from_id, message_id = row
        if status_id < 5:
            try:
                await bot.edit_message_text(
                    text=f'{link_page}\nСтатус: {status_id}\nОчередь: {await get_queue_count()}',
                    chat_id=from_id,
                    message_id=message_id
                )
            except MessageNotModified:
                pass
            except (MessageToEditNotFound, MessageToDeleteNotFound, UserDeactivated) as error:
                log(error, 'ERROR')
                await set_status(process_id, 6)
                status_id = 6
        if status_id == 3:
            await set_status(process_id, 4)
            filename = f'./files/{process_id}.mp4'
            if not os.path.exists(filename):
                log(f'{filename} не найден', 'WARN')
                await set_status(process_id, 7)
                return
            filesize = os.stat(filename).st_size / (1024 * 1024)
            if filesize >= 50:
                await set_status(process_id, 5)
            else:
                log(f'Загружаю на канал {filename}')
                cv2video = cv2.VideoCapture(filename)
                height = cv2video.get(cv2.CAP_PROP_FRAME_HEIGHT)
                width  = cv2video.get(cv2.CAP_PROP_FRAME_WIDTH)
                # TODO получить продолжительность видео и передавать её в тг при загрузке
                # dur = cv2video.get(cv2.CAP_PROP_)
                
                ch_message = await bot.send_video(
                    chat_id=CH_ID,
                    video=open(filename, 'rb'),
                    caption=f'{link_page}', # TODO добавить ссылку на бота
                    height=height,
                    width=width
                )
                delete_files(process_id)
                ch_id = ch_message.message_id
                log(f'Загрузил {ch_id}')
                file_id = await get_file_id(ch_id, link_page, process_id)
                try:
                    await bot.delete_message(chat_id=from_id, message_id=message_id)
                    await send_from_channel(file_id, from_id)
                except (BotBlocked, MessageCantBeDeleted):
                    pass


async def scheduler():
    while True:
        await update_status()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
