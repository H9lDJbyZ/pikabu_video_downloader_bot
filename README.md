# pikabu_video_downloader_bot
Запущен https://t.me/pikabu_video_downloader_bot
Заливает через канал https://t.me/pikabu_videos

## Права доступа
$ chmod 666 db
$ chmod 666 files

## Запуск
 $ docker build . -t pikabu_bot
 $ docker compose build
 $ docker compose up -d

 ## Литература
 https://mastergroosha.github.io/telegram-tutorial-2/

 install pycurl: pip install --compile --global-option="--with-openssl" --no-cache-dir pycurl 