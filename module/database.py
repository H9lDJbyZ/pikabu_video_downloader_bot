import sqlite3
from module.env import env_db_filename


DB_TABLE_PROCESS = 'process'
DB_TABLE_FILES = 'files'
DB = env_db_filename()


def set_status(id, status_id):
    cx = sqlite3.connect(DB)
    cu = cx.cursor()
    cu.execute('UPDATE process SET status_id = ? WHERE id = ?;', (status_id, id))
    cx.commit()
    cx.close()


def get_queue_count():
    cx = sqlite3.connect(DB)
    cu = cx.cursor()
    count = cu.execute(f'SELECT COUNT(id) FROM {DB_TABLE_PROCESS};').fetchone()[0]
    cx.close()
    return count