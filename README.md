# pikabu_video_downloader_bot

Запущен https://t.me/pikabu_video_downloader_bot

Заливает через канал https://t.me/pikabu_videos


## Права доступа

$ chmod 666 db

$ chmod 666 files


## Запуск
 $ docker build -t pvd_bot_image -f ./deploy/Dockerfile .
 $ docker compose -f ./deploy/docker-compose.yml build
 $ docker compose -f ./deploy/docker-compose.yml up -d

## Литература

https://mastergroosha.github.io/telegram-tutorial-2/


## Заметки
install pycurl: 
pip uninstall pycurl
pip install --compile --global-option="--with-openssl" --no-cache-dir pycurl 
pip install --compile --build-option="--with-openssl" --no-cache-dir pycurl 
pip install --compile --config-setting="--build-option=--with-openssl" --no-cache-dir pycurl 
