import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
# from aiogram.exceptions import MessageNotModified, MessageToEditNotFound, MessageToDeleteNotFound, BotBlocked, MessageCantBeDeleted, UserDeactivated
from aiogram.exceptions import TelegramAPIError, TelegramNotFound
from module.async_database import get_all_in_process, get_file_id, get_one_in_process, get_queue_len, set_status, url_exist, add_link_to_queue, get_channel_message_id
from module.log import log
from module.env import env_ch_id, env_bot_token
import cv2


bot = Bot(env_bot_token())
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

CH_ID = env_ch_id()


def delete_files(id):
    fn_html = f'./files/{id}.html'
    fn_mp4 = f'./files/{id}.mp4'
    if os.path.exists(fn_html):
        os.remove(fn_html)
    if os.path.exists(fn_mp4):        
        os.remove(fn_mp4)


@dp.message(Command('start'))
async def cmd_test1(message: types.Message):
    await message.reply(f'Пришли ТОЛЬКО ссылку на пост Пикабу с видео\nОчередь: {await get_queue_len()}')


def is_pikabu(url: str) -> bool:
    return url.startswith('https://pikabu.ru/story/')


@dp.message(F.text)
async def any_text(message: types.Message):
    if message.entities is None: 
        return
    if message.entities[0].type != 'url':
        return
    url = message.entities[0].extract_from(message.text)
    
    pos_question = url.find('?')
    if pos_question != -1:
        url = url[:pos_question]
    if not is_pikabu(url):
        await message.answer('Это ссылка не на пост Пикабу, а что-то ещё...')
        return
    
    await message.answer(url)
    bot_message = await message.answer('Работаем...')
    from_id = message.from_user.id
    
    file_id = await url_exist(url)
    if not file_id:
        # await bot_message.edit_text('Ранее не скачивалось')
        await add_link_to_queue(url, from_id, bot_message.message_id)
        await bot_message.edit_text(f'Добавлено в очередь\nВ очереди {await get_queue_len()}, придётся немного подождать')
    else:
        # await bot_message.edit_text('Ранее скачивалось')
        await bot_message.delete()
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
    # log(rows)
    for row in rows:
        await asyncio.sleep(2)
        process_id, link_page, status_id, from_id, message_id = row
        if status_id < 5:
            try:
                await bot.edit_message_text(
                    text=f'{link_page}\nСтатус: {status_id}\nОчередь: {await get_queue_len()}',
                    chat_id=from_id,
                    message_id=message_id
                )
            # except MessageNotModified:
            #     pass
            # except (TelegramNotFound, UserDeactivated) as error:
            #     log(error, 'ERROR')
            #     await set_status(process_id, 6)
            #     status_id = 6
            except TelegramAPIError as e:
                log(e, 'ERROR')                
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
                # except (BotBlocked, MessageCantBeDeleted):
                except TelegramAPIError as e:
                    log(e, 'ERROR')
                    pass

async def update_status_v2():
    row = get_one_in_process()
    process_id, link_page, status_id, from_id, message_id = row
    


async def scheduler():
    while True:
        try:
            # await update_status()
            await update_status_v2()
        except Exception as e:
            log(e, 'ERROR')
        await asyncio.sleep(2)


async def start_bot():
    await dp.start_polling(bot)


async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(start_bot())
        tg.create_task(scheduler())


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.create_task(scheduler())
    # executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
