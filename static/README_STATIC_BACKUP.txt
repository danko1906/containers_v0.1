ЗАМЕТКА ПО РЕЗЕРВНОЙ КОПИИ СТАТИКИ (containers_v0.1)
Дата: 2026-02-20

Что было до изменений:
- Фронтенд-статика отдавалась IIS из папки:
  C:\inetpub\wwwroot\containers\
- URL API был захардкожен в нескольких JS-файлах:
  http://192.168.2.101:5001
- Бэкенд (main.exe / main.py) отдавал только маршруты /api и не раздавал статику.

Что было сделано:
- Добавлен единый конфиг:
  static/scripts/config.js
- Основные frontend-скрипты теперь берут BASE_URL из APP_CONFIG:
  login.js, container.js, download.js, edit.js, kit.js
- Подключение config.js добавлено перед основными скриптами в:
  static/index.html
  static/container.html
  static/download.html
  static/edit.html
  static/kit.html
- Базовый API URL по умолчанию теперь формируется от текущего хоста страницы на порту 5001:
  http://<текущий-хост>:5001

Зачем нужен бэкап старой статики:
- Если после изменений сломается навигация или запросы к API, можно быстро откатиться.

Рекомендуемый бэкап перед заменой:
1. Открыть PowerShell от имени администратора.
2. Выполнить:
   Compress-Archive -Path C:\inetpub\wwwroot\containers\* `
     -DestinationPath C:\inetpub\wwwroot\containers_backup_before_baseurl_2026-02-20.zip

Откат:
1. Остановить доступ к сайту (или сделать временное окно обслуживания).
2. Удалить текущие файлы из C:\inetpub\wwwroot\containers\
3. Восстановить файлы из backup-архива в эту же папку.
4. Сделать принудительное обновление страницы в браузере (Ctrl+F5).

Опциональное ручное переопределение:
- Если нужно, можно явно задать API URL до загрузки config.js:
  window.APP_CONFIG = { BASE_URL: "http://192.168.2.101:5001" };
