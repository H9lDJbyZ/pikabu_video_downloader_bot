import asyncio
import os
from time import sleep
from module.async_database import get_queue, set_status
from module.log import log
import pycurl


async def find_video_link(filename):
    await log(f'find_video_link - {filename}')
    if not os.path.exists(filename):
        await log(f'{filename} not found', 'WARN')
        return False
    with open(filename, 'br') as f:
        page = str(f.read())
    try:
        ind_div = page.find('<div class="player"')
        if ind_div == -1:
            return False
        ind_attr = page.find('data-source=', ind_div)
        if ind_attr == -1:
            return False
        ind_1q = page.find('"', ind_attr) + 1
        if ind_1q == -1:
            return False
        ind_2q = page.find('"', ind_1q)
        if ind_2q == -1:
            return False
        res = page[ind_1q:ind_2q]+'.mp4'
    except:
        return False
    return res


def curl(out, link):
    with open(out, 'wb') as f:
        c = pycurl.Curl()
        c.setopt(c.URL, link)
        c.setopt(c.WRITEDATA, f)
        c.setopt(c.CAPATH, '/etc/ssl/certs')
        c.setopt(c.CAINFO, '/etc/ssl/certs/ca-certificates.crt')
        
        c.perform()
        c.close()


async def download():
    rows = await get_queue()
    c = len(rows)
    if c > 0:
        await log(f'В очереди: {c}')
    for row in rows:
        sleep(1)
        id, link_page = row
        await log(link_page)
        await set_status(id, 1)

        await log('Скачиваю страницу')
        html_file = f'./files/{id}.html'
        curl(html_file, link_page)

        await log('Поиск ссылки на видео')
        video = await find_video_link(html_file)
        if not video:
            await set_status(id, 7)
            return
        
        await log('Скачиваю видео')
        await set_status(id, 2)
        video_file = f'./files/{id}.mp4'
        curl(video_file, video)

        await log('Готово')
        await set_status(id, 3)


async def scheduler():
    while True:
        await download()
        await asyncio.sleep(5)

if __name__ == '__main__':
    print('Downloader started')
    asyncio.run(scheduler())
