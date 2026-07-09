# List available commands
default:
    just --list

# Docker compose up
up:
    docker compose up -d --build

# Docker compose down
down:
    docker compose down -v

sh:
  docker exec -ti airflow-spark bash

nb:
  open http://localhost:8888

airflow:
  open http://localhost:8080

# Restart docker containers
restart:
  just down 
  just up
