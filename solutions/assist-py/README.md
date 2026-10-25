# Assistant

Персональный ассистент на FastAPI с интеграцией СУБД PostgreSQL, персистентными томами данных и сетевой изоляцией. Репозиторий ведётся в рамках лабораторных по Docker и Kubernetes.

Автор: Вычик Владимир, ИСУ 465463

## Как запустить

```bash
# 1. Создание изолированной сети и постоянного тома данных
docker network create vychik-backend
docker volume create vychik-pgdata

# 2. Запуск СУБД PostgreSQL во внутренней сети backend
docker run -d \
  --name vychik-postgres \
  --network vychik-backend \
  -e POSTGRES_USER=user_465463 \
  -e POSTGRES_PASSWORD=pgpass_465463 \
  -e POSTGRES_DB=vychik63 \
  -v vychik-pgdata:/var/lib/postgresql/data \
  postgres:15

# 3. Запуск приложения ассистента с линковкой внешней конфигурации через Bind Mount
docker run -d \
  --name vychik-assistant \
  --network vychik-backend \
  -p 8063:5493 \
  -e APP_OWNER=vychik \
  -e APP_SECRET=secret63vychik \
  -e DATABASE_URL="postgresql://user_465463:pgpass_465463@vychik-postgres:5432/vychik63" \
  -v \$(pwd)/config:/app/config:ro \
  vychik-assistant:v3
```

## Переменные окружения

| Переменная | Для чего | Пример |
| --- | --- | --- |
| `APP_OWNER` | ваша фамилия, показывается на главной | `vychik` |
| `APP_SECRET` | секретный ключ для авторизации флага | `secret63vychik` |
| `DATABASE_URL` | строка подключения к изолированной СУБД по имени контейнера | `postgresql://user_465463:pgpass_465463@vychik-postgres:5432/vychik63` |

## Как проверить

```bash
curl http://localhost:8063/health
```
