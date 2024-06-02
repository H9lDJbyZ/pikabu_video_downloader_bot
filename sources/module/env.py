from dotenv import load_dotenv
from os import environ

load_dotenv('.env')

def env_db_filename():
    return environ.get('DATABASE_FILE')


def env_ch_id():
    return environ.get('CH_ID')


def env_bot_token():
    return environ.get('BOT_TOKEN')


def env_bot_version():
    return environ.get('BOT_VERSION')