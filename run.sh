#!/bin/bash

DEPLOY_PATH="./deploy"
DOCKER_FILE="${DEPLOY_PATH}/Dockerfile"
COMPOSE_FILE="${DEPLOY_PATH}/docker-compose.yml"

DB_PATH="./db"
FILE_PATH="./files"

# docker volume create 

docker compose -f $COMPOSE_FILE down
cp ./db/data.db ./db/data.db.backup_$(date '+%Y%m%d_%H%M%S')
# docker rmi pvd_bot pvd_downloader
# rm -f files/*
# mkdir $DB_PATH
# mkdir $FILE_PATH
# chmod 744 $DB_PATH
# chmod 744 $FILE_PATH

docker build -t pvd_bot_image -f $DOCKER_FILE .
# docker build -t pvd_bot_image -f https://github.com/H9lDJbyZ/pikabu_video_downloader_bot.git#master:deploy .

# docker compose -f $COMPOSE_FILE build
docker compose -f $COMPOSE_FILE up -d
docker ps