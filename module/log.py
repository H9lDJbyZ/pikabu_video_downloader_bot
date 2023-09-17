from datetime import datetime


def log(text, level = 'INFO'):
    print(f'{datetime.now()} {level} {text}')