import os
import subprocess
from time import sleep
import sqlite3
from module.database import get_queue, set_status
from module.env import env_db_filename
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
    # cmd = f'curl -s -o {out} {link}'
    # log(cmd)
    # process = subprocess.Popen(cmd, shell=True)
    # process.wait()
    with open(out, 'wb') as f:
        c = pycurl.Curl()
        c.setopt(c.URL, link)
        c.setopt(c.WRITEDATA, f)
        c.perform()
        c.close()


# def save_page(link_page: str, id):
#     html_file = f'./files/{id}.html'
#     # cmd = f'curl -o {html_file} {link_page}'
#     curl(html_file, link_page)
#     return html_file


# def save_video(link_video: str, id):
#     video_file = f'./files/{id}.mp4'
#     # cmd = f'curl -o {video_file} {link_video}'
#     curl(video_file, link_video)
#     return video_file


def download():
    rows = get_queue()
    c = len(rows)
    if c > 0:
        log(f'В очереди: {c}')
    for row in rows:
        sleep(1)
        id, link_page = row
        log(link_page)
        set_status(id, 1)

        # save page
        # tmp_file = save_page(link_page, id)
        log('Скачиваю страницу')
        html_file = f'./files/{id}.html'
        curl(html_file, link_page)

        log('Поиск ссылки на видео')
        video = find_my(html_file)
        if not video:
            set_status(id, 7)
            return
        
        log('Скачиваю видео')
        set_status(id, 2)
        # save_video(video, id)
        video_file = f'./files/{id}.mp4'
        curl(video_file, video)

        log('Готово')
        set_status(id, 3)


if __name__ == '__main__':
    while True:
        sleep(10)
        download()