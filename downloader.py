import asyncio
import os
from time import sleep
from module.async_database import get_queue, set_status
from module.log import log
import pycurl


def find_my(filename):
    log(f'find_my - {filename}')
    if not os.path.exists(filename):
        log(f'{filename} not fount', 'WARN')
        return False
    with open(filename, 'br') as f:
        page = str(f.read())
    try:
        ind_div = page.find('<div class="player"')
        ind_attr = page.find('data-source=', ind_div)
        ind_1q = page.find('"', ind_attr) + 1
        ind_2q = page.find('"', ind_1q)
        res = page[ind_1q:ind_2q]+'.mp4'
    except:
        return False
    return res


def curl(out, link):
    with open(out, 'wb') as f:
        c = pycurl.Curl()
        c.setopt(c.URL, link)
        c.setopt(c.WRITEDATA, f)
        c.perform()
        c.close()


async def download():
    rows = await get_queue()
    c = len(rows)
    if c > 0:
        log(f'В очереди: {c}')
    for row in rows:
        sleep(1)
        id, link_page = row
        log(link_page)
        await set_status(id, 1)

        log('Скачиваю страницу')
        html_file = f'./files/{id}.html'
        curl(html_file, link_page)

        log('Поиск ссылки на видео')
        video = find_my(html_file)
        if not video:
            await set_status(id, 7)
            return
        
        log('Скачиваю видео')
        await set_status(id, 2)
        video_file = f'./files/{id}.mp4'
        curl(video_file, video)

        log('Готово')
        await set_status(id, 3)

async def scheduler():
    while True:
        await download()
        await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(scheduler())
