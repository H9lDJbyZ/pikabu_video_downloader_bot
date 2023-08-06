from dotenv import load_dotenv
from os import environ

load_dotenv()

def env_db_filename():
    return environ.get('DATABASE_FILE')