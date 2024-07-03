DEPLOY_PATH="./deploy"
DOCKER_FILE="${DEPLOY_PATH}/Dockerfile"
COMPOSE_FILE="${DEPLOY_PATH}/docker-compose.yml"
docker compose -f $COMPOSE_FILE down