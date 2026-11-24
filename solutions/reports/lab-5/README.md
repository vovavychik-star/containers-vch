# Лабораторная работа №5. Оркестрация контейнеров с помощью Kubernetes

**Студент:** Вычик Владимир  
**Номер ИСУ:** 465463  
**Персональный префикс:** `vychik`  
**Ветка репозитория:** `lab-5`

---

## 1. Персональные параметры

| Параметр | Значение |
| --- | --- |
| Номер ИСУ | `465463` |
| Персональный префикс | `vychik` |
| Секретный ключ (`APP_SECRET`) | `secret63vychik` |
| Имя базы данных (`POSTGRES_DB`) | `vychik63` |
| Владелец (`APP_OWNER`) | `vychik` |
| Пользователь БД (`POSTGRES_USER`) | `user_465463` |
| Пароль БД (`POSTGRES_PASSWORD`) | `pgpass_465463` |
| Порт Uvicorn внутри контейнера | `5493` |
| Порт сервиса (`NodePort`) | `30063` (targetPort: `5493`, port: `8063`) |

---

## 2. Ход выполнения работы

### Этап 1. Запуск Minikube и сборка образа внутри кластера
* Запущен локальный кластер Kubernetes (`minikube start --driver=docker`).
* Образ `assist-py:v1` собран непосредственно в среде Minikube (`minikube image build -t assist-py:v1 .`).

> _Скриншот: `screenshots/step1-minikube-status.png`_

### Этап 2. Конфигурация приложения (ConfigMap и Secret)
* Создан `k8s/configmap.yaml` (`assist-config`) с параметрами `APP_OWNER="vychik"`, `CACHE_TTL="120"`, `REDIS_URL="redis://redis:6379/0"`.
* Создан `k8s/secret.yaml` (`assist-secret`) с секретным ключом `APP_SECRET` и реквизитами PostgreSQL.

> _Скриншот: `screenshots/step2-configmap-secret.png`_

### Этап 3. Развёртывание Redis и PostgreSQL с PersistentVolumeClaim
* Развёрнуты `Deployment` и `Service` (`ClusterIP`) для `redis` (порт `6379`) и `postgres` (порт `5432`).
* Для сохранения данных БД создан `PersistentVolumeClaim` (`postgres-pvc`, `1Gi`, `ReadWriteOnce`), который динамически связался (`Bound`) с `PersistentVolume`.

> _Скриншот: `screenshots/step3-redis-postgres-pvc.png`_

### Этап 4. Развёртывание приложения assist-py и публикация через NodePort
* Создан `k8s/deployment.yaml` с `imagePullPolicy: Never`, пробросом переменных из `assist-config` и `assist-secret`, а также настройкой `livenessProbe` и `readinessProbe` на `/health` (порт `5493`).
* Создан `k8s/service.yaml` типа `NodePort` (`nodePort: 30063` -> `targetPort: 5493`).
* Проверена работа эндпоинтов `/health`, `/`, `/me`, `/secret/secret63vychik`, `/weather/moscow` (подтверждено кэширование через кластерный Redis: `"source": "api"` -> `"source": "cache"`) и `/cache/stats`.

> _Скриншот: `screenshots/step4-app-curl-tests.png`_

### Этап 5. Масштабирование, балансировка нагрузки и Self-Healing
* Выполнено масштабирование до 4 реплик (`kubectl scale deployment assist-app --replicas=4`).
* Проверены `Endpoints` сервиса (4 IP-адреса подов) и распределение запросов в логах (`kubectl logs -l app=assist-app --prefix=true`).
* Проведена симуляция сбоя удалением пода (`kubectl delete pod ...`): контроллер `ReplicaSet` автоматически пересоздал недостающий под, восстановив целевое состояние (`4/4 Running`).

> _Скриншот: `screenshots/step5-scaling-self-healing.png`_

### Этап 6. Обновление без простоя (Rolling Update) и откат (Rollback)
* Обновлена версия API в `app/main.py` до `2.0`, собран образ `assist-py:v2`.
* Выполнено обновление `kubectl set image deployment/assist-app assist-app=assist-py:v2`, подтверждена плавная замена реплик без простоя (`"version": "2.0"`).
* Выполнен откат `kubectl rollout undo deployment/assist-app`, подтверждён возврат версии `"1.0"`.

> _Скриншот: `screenshots/step6-rolling-update-rollback.png`_

---

## 3. Ответы на контрольные вопросы

1. **В чём разница между `Pod`, `Deployment` и `Service` в Kubernetes?**
   * **`Pod`** — минимальная развёртываемая единица в Kubernetes, содержащая один или несколько тесно связанных контейнеров с общим сетевым пространством и томами; поды эфемерны и не пересоздаются сами при падении.
   * **`Deployment`** — декларативный контроллер высокого уровня, который управляет жизненным циклом подов через `ReplicaSet`: поддерживает заданное количество реплик, обеспечивает самовосстановление (Self-Healing), плавные обновления без простоя (`Rolling Update`) и откат версий (`Rollback`).
   * **`Service`** — стабильная сетевая абстракция, предоставляющая постоянный виртуальный IP-адрес и DNS-имя для динамически меняющегося набора подов (по их меткам `selector`) и балансирующая трафик между ними.

2. **Зачем в манифесте `Deployment` указывать `imagePullPolicy: Never` при работе с Minikube?**
   * По умолчанию Kubernetes пытается загрузить образ из удалённого реестра (например, Docker Hub), если тег не `:latest` (политика `IfNotPresent`) или всегда при `:latest` (`Always`). Поскольку локально собранный образ `assist-py:v1` существует только во внутреннем Docker-окружении узла Minikube и отсутствует в публичном реестре, флаг `imagePullPolicy: Never` запрещает kubelet обращаться во внешнюю сеть и заставляет использовать локальный образ, предотвращая ошибку `ImagePullBackOff` / `ErrImagePull`.

3. **Чем отличаются `ClusterIP`, `NodePort` и `LoadBalancer`?**
   * **`ClusterIP`** — тип сервиса по умолчанию; выдаёт внутренний IP-адрес, доступный только внутри кластера Kubernetes (использовался для `redis` и `postgres`).
   * **`NodePort`** — открывает статический порт (в диапазоне `30000–32767`) на IP-адресе каждого узла кластера и перенаправляет трафик на `ClusterIP` сервиса, обеспечивая доступ снаружи (использовался для `assist-service` на порту `30063`).
   * **`LoadBalancer`** — создаёт внешний балансировщик нагрузки у облачного провайдера (AWS, GCP, Yandex Cloud и др.), который получает публичный IP и маршрутизирует внешний трафик на `NodePort` узлов кластера.

4. **Как `livenessProbe` и `readinessProbe` влияют на работу приложения при обновлении (Rolling Update)?**
   * **`readinessProbe`** определяет, готов ли новый pod принимать пользовательский трафик: во время `Rolling Update` Kubernetes не включает новый pod в `Endpoints` сервиса и не останавливает старый pod, пока `readinessProbe` не вернёт успешный ответ (`200 OK` на `/health`), что исключает простой (downtime) и ошибки 502/503 при раскатке.
   * **`livenessProbe`** отслеживает «живучесть» контейнера в процессе работы: если приложение зависнет или войдёт в deadlock, kubelet автоматически перезапустит контейнер.

5. **Почему для PostgreSQL в Kubernetes нужен `PersistentVolumeClaim`, а без него данные потеряются?**
   * Файловая система контейнера внутри пода является эфемерной: при перезапуске контейнера, удалении пода (Self-Healing) или пересоздании на другом узле все данные на локальном диске контейнера уничтожаются. **`PersistentVolumeClaim` (`PVC`)** запрашивает у кластера независимое постоянное хранилище (`PersistentVolume`), жизненный цикл которого не привязан к жизни конкретного пода, поэтому после пересоздания пода PostgreSQL монтирует тот же том и сохраняет все таблицы и записи.
