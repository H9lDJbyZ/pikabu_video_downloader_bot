import sqlite3
from module.env import env_db_filename



def set_status(id, status_id):
    cx = sqlite3.connect(env_db_filename())
    cu = cx.cursor()
    cu.execute('UPDATE process SET status_id = ? WHERE id = ?;', (status_id, id))
    cx.commit()
    cx.close()