# Hawkeye 🐦👁️
Бекенд-сервіс на Python, який:
- відстежує зміни у файловій системі
- відправляє події клієнтам через веб сокети
- логує події в SQLite + Console
- має глобальний Log Journal, логування в SQLite та трансляція через веб сокети 

---

## Вимоги до запуску
- Python 3.11+ (рекомендовано)
- Windows / Linux / macOS
- (опційно) SQLite viewer для перегляду бази (`hawkeye.db`)

---

## Run project
```bash
  pip install -r requirements.txt
```
```bash
  uvicorn main:fastapi_app --reload --port 8000
```

## Налаштування `.env`
Створи файл `.env` у корені проєкту:

```env
# Директорії для спостереження (розділювач ; )
WATCH_DIRS=C:\Temp;C:\Users\Maksym\Desktop\TestFolder

# Рекурсивне спостереження (true/false)
WATCH_RECURSIVE=true

# Шлях до SQLite
DB_PATH=hawkeye.db

# Максимальний розмір черги подій
QUEUE_MAXSIZE=10000

# Назва socket події для change file events
SOCKET_FILE_CHANGE_EVENT_NAME=file_change_event

# Назва socket події для логування
SOCKET_LOG_EVENT_NAME=log_event
```