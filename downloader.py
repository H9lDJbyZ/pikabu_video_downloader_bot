import os
import subprocess
from time import sleep
import sqlite3
from module.database import set_status
from module.env import env_db_filename
from module.log import log



def find_my(filename):
    log(f'find_my - {filename}')
    if not os.path.exists(filename):
        log(f'{filename} not fount', 'WARN')
        return False
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
    cmd = f'curl -o {html_file} {link_page}'
    log(cmd)
    os.system(cmd)
    return html_file


def save_video(link_video: str, id):
    video_file = f'./files/{id}.mp4'
    cmd = f'curl -o {video_file} {link_video}'
    log(cmd)
    # os.system(cmd)
    # Выполнить команду с ожиданием завершения
    process = subprocess.Popen(cmd, shell=True)
    process.wait()  # Ожидание завершения выполнения команды
    return video_file


def download():
    cx = sqlite3.connect(env_db_filename())
    cu = cx.cursor()
    cu.execute('SELECT id, link_page FROM process WHERE status_id = 0;')
    rows = cu.fetchall()
    c = len(rows)
    if c > 0:
        log(f'В очереди: {c}')
    for row in rows:
        sleep(1)
        id, link_page = row
        log(link_page)
        log('Поиск...')
        set_status(id, 1)

        tmp_file = save_page(link_page, id)
        video = find_my(tmp_file)

        if not video:
            set_status(id, 7)
            return
        
        log('Скачивание...')
        set_status(id, 2)
        save_video(video, id)

        log('Готово')
        set_status(id, 3)
    cx.close()




if __name__ == '__main__':
    while True:
        sleep(10)
        download()