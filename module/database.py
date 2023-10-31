import sqlite3
from module.env import env_db_filename


DB_TABLE_PROCESS = 'process'
DB_TABLE_FILES = 'files'
DB = env_db_filename()


def set_status(id, status_id):
    with sqlite3.connect(DB) as cx:
        cu = cx.cursor()
        cu.execute('UPDATE process SET status_id = ? WHERE id = ?;', (status_id, id))
        cx.commit()
        # cx.close()


def get_queue_count():
    # cx = sqlite3.connect(DB)
    with sqlite3.connect(DB) as cx:
        cu = cx.cursor()
        count = cu.execute(f'SELECT COUNT(id) FROM {DB_TABLE_PROCESS};').fetchone()[0]
    # cx.close()
    return count


def get_queue():
    # cx = sqlite3.connect(DB)
    with sqlite3.connect(DB) as cx:
        cu = cx.cursor()
        cu.execute(f'SELECT id, link_page FROM {DB_TABLE_PROCESS} WHERE status_id = 0;')
        rows = cu.fetchall()
    # cx.close()
    return rows