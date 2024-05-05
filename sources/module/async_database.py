import aiosqlite
from module.env import env_db_filename


DB_TABLE_PROCESS = 'process'
DB_TABLE_FILES = 'files'
DB = env_db_filename()


async def set_status(id, status_id):
    async with aiosqlite.connect(DB) as cx:
        await cx.execute(f'UPDATE {DB_TABLE_PROCESS} SET status_id = ? WHERE id = ?;', (status_id, id))
        await cx.commit()


async def get_queue_len():
    result = 0
    async with aiosqlite.connect(DB) as cx:
        async with cx.execute(f'SELECT COUNT(id) FROM {DB_TABLE_PROCESS} WHERE status_id in (0, 1, 2, 3, 4);') as cu:
            row = await cu.fetchone()
    if row is not None:
        result = row[0]
    return result


async def get_queue():
    async with aiosqlite.connect(DB) as cx:
        async with cx.execute(f'SELECT id, link_page FROM {DB_TABLE_PROCESS} WHERE status_id = 0;') as cu:
            result = await cu.fetchall()
    return result


async def url_exist(url: str) -> bool | int:
    async with aiosqlite.connect(DB) as cx:
        async with cx.execute(f'SELECT id FROM {DB_TABLE_FILES} WHERE link_page = ?;', (url,)) as cu:
            row = await cu.fetchone()
    if row is None:
        return False
    return row[0]


async def add_link_to_queue(url: str, from_id: int, message_id: int) -> int:
    async with aiosqlite.connect(DB) as cx:
        await cx.execute(f'INSERT INTO {DB_TABLE_PROCESS} (link_page, from_id, message_id, status_id) VALUES (?,?,?,?);', 
                         (url, from_id, message_id, 0))
        await cx.commit()


async def get_channel_message_id(file_id):
    async with aiosqlite.connect(DB) as cx:
        async with cx.execute(f'SELECT message_id FROM {DB_TABLE_FILES} WHERE id = ?;', (file_id,)) as cu:
            row = await cu.fetchone()
    if row is None:
        return None
    return row[0]


async def get_all_in_process():
    result = None
    async with aiosqlite.connect(DB) as cx:
        async with cx.execute(f'SELECT id, link_page, status_id, from_id, message_id FROM {DB_TABLE_PROCESS};') as cu:
            result = await cu.fetchall()
    return result


async def get_one_in_process():
    result = None
    try:
        async with aiosqlite.connect(DB) as cx:
            async with cx.execute(
                    f'''
                    SELECT 
                        id
                        , link_page
                        , status_id
                        , from_id
                        , message_id 
                    FROM {DB_TABLE_PROCESS} 
                    WHERE status_id in (0, 1, 2, 3, 4) 
                    LIMIT 1;'''
                ) as cu:
                result = await cu.fetchone()
    except Exception as e:
        print(e)
    return result
    

async def get_file_id(ch_id, link_page, process_id):
    async with aiosqlite.connect(DB) as cx:
        await cx.execute(f'INSERT INTO {DB_TABLE_FILES} (message_id, link_page) VALUES (?,?);', (ch_id, link_page,))
        await cx.execute(f'DELETE FROM {DB_TABLE_PROCESS} WHERE id = ?;', (process_id,))
        await cx.commit()
        async with cx.execute(f'SELECT id FROM {DB_TABLE_FILES} WHERE link_page = ?;', (link_page,)) as cu:
            row = await cu.fetchone()
        file_id = row[0]
        return file_id
    