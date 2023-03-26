import os
from time import sleep
import sqlite3
from module.database import set_status
from module.env import env_db_filename


def find_my(filename):
    with open(filename, 'br') as f:
        page = str(f.read())
    ind_div = page.find('<div class="player"')
    ind_attr = page.find('data-source=', ind_div)
    ind_1q = page.find('"', ind_attr) + 1
    ind_2q = page.find('"', ind_1q)
    res = page[ind_1q:ind_2q]+'.mp4'
    return res


def save_page(link_page: str, id):
    html_file = f'./files/{id}.html'
    cmd = f'curl {link_page} -o {html_file}'
    print(cmd)
    os.system(cmd)
    return html_file


def save_video(link_video: str, id):
    video_file = f'./files/{id}.mp4'
    cmd = f'curl {link_video} -o {video_file}'
    print(cmd)
    os.system(cmd)
    return video_file


def download():
    cx = sqlite3.connect(env_db_filename())
    cu = cx.cursor()
    cu.execute('SELECT id, link_page FROM process WHERE status_id = 0;')
    rows = cu.fetchall()
    print(f'В очереди: {len(rows)}')
    for row in rows:
        sleep(5)
        id, link_page = row
        print(link_page)
        print('Поиск')
        set_status(id, 1)

        tmp_file = save_page(link_page, id)
        video = find_my(tmp_file)
        
        print('Скачивание')
        set_status(id, 2)
        save_video(video, id)

        print('Готово')
        set_status(id, 3)
    cx.close()




if __name__ == '__main__':
    while True:
        sleep(10)
        download()