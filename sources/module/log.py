from datetime import datetime


async def log(text, level = 'INFO'):
    print(f'{datetime.now()} {level} {text}')