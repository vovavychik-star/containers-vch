# Assistant

Персональный ассистент на FastAPI. Репозиторий ведётся в рамках лабораторных по Docker и Kubernetes.

Автор: Вычик Владимир, ИСУ 465463

## Как запустить

```bash
docker build -t vychik-assistant:final -f Dockerfile.optimized .
docker run -d --name vychik-assistant-final -p 5493:5493 -e APP_OWNER=vychik -e APP_SECRET=secret63vychik vychik-assistant:final
```

## Переменные окружения

| Переменная | Для чего | Пример |
| --- | --- | --- |
| `APP_OWNER` | ваша фамилия, показывается на главной | `vychik` |
| `APP_SECRET` | секретный ключ для авторизации флага | `secret63vychik` |
| `PORT` | порт приложения | `5493` |

## Как проверить

```bash
curl http://localhost:5493/health
```
