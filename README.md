# Лабораторная №3. Ansible

Приложение заметок на Spring Boot с PostgreSQL и Nginx.
В одной Docker-сети работают четыре контейнера: `ansible`, `nginx`, `app`, `db`.
Роли `app` и `nginx` устанавливают зависимости, настраивают и запускают сервисы.

## Запуск

Нужны Linux, Git, Docker с Compose v2+, Bash, curl и `ssh-keygen` (пакет `openssh-client`).
Для загрузки образов и пакетов нужен доступ к интернету. Ansible, Java и Maven устанавливаются в контейнерах.

```bash
git clone --branch lab3 https://github.com/Yastrebonchik/SoftwareDesignPracticumLaba3.git
cd SoftwareDesignPracticumLaba3
bash scripts/prepare.sh
docker compose up -d --build
docker compose exec -T ansible ansible-playbook site.yml
bash scripts/wait-ready.sh
```

`prepare.sh` создаёт `.env` и новую пару SSH-ключей в `.ssh/`; существующие файлы сохраняются.
При запуске `ansible` копирует приватный ключ в `/root/.ssh/id_ed25519` — это путь из inventory внутри контейнера.
Контейнеры `app` и `nginx` устанавливают публичный ключ в `authorized_keys`. Дополнительная настройка SSH не требуется.
Порт и параметры БД задаются в `.env` до первого запуска.
Контейнеры `app` и `nginx` становятся `healthy` после выполнения playbook.

## Проверка

```bash
docker compose ps
docker compose exec -T ansible ansible all -m ping
curl -i http://localhost:8083/health
docker compose exec -T ansible ansible-playbook site.yml
```

Ожидаются четыре контейнера `healthy`, ответ `pong` от `app` и `nginx`, HTTP 200 и `changed=0` при повторном запуске playbook.
Открыть http://localhost:8083/, добавить и удалить заметку.

Остановка с сохранением данных: `docker compose down`.
После пересоздания контейнеров нужно снова выполнить playbook.

Исходники приложения: `app/`. Playbook и роли: `ansible/`.
Скрипт запуска приложения: `ansible/roles/app/files/app.sh`.
Скриншоты: [контейнеры](docs/screenshots/containers.jpg), [приложение](docs/screenshots/application.jpg).
