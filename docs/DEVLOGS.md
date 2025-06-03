# DEVELOPMENT LOGs

## Март

### 26.03
- Создание проекта
- Установка зависимостей

### 27.03
- Моделирование общей C4 архитектуры

### 28.03
- Проектирование контейнера Backend в C4

### 29.03
- Настройка асинхронного подключения к PostgreSQL

### 31.03
- Создание моделей таблиц `User / Report / Pet` в SQLAlchemy
- Настройка Alembic

## Апрель

### 01.04
- Подключение PostgreSQL + SQLAlchemy
- Создание первой миграции
- Тесты для `User / Pet / Report` (pytest)

### 02.04
- Добавлены линтеры (ruff & mypy)
- Добавлен Makefile

### 06.04
- Исправление проблем, вызванных линтерами

### 07.04
- CI Actions workflows для linters и pytest

### 10.04
- Добавлена pydantic schema для `User`

### 11.04
- Добавлена pydantic schema для `Pet`

### 12.04
- Добавлена pydantic schema для `Report`

### 13.04
- Связи между pydantic моделями
- Фиксы линтеров

### 14.04
- FastAPI + `UserServices.get_all_users`
- First router

### 15.04
- `UserServices.create_user`
- Fix Swagger issues
- Fix linters

### 16.04
- `User` services & routers

### 18.04
- `Pet` services & routers
- `Report` services & routers

### 19.04
- Доработки предыдущих сервисов

### 22.04
- Получение всех `Pet & Report` моделей пользователя: services & routers

### 23.04
- Services & routers для `PetPhoto`

### 24.04
- Services & routers для `ReportPhoto`

### 25.04
- Fill db with `Users / Pets / Reports`
- `run_all.sh`

### 26.04
- Frontend improvements (templates / css / bootstrap)
- Routers to display templates

### 27.04
- Ngrok
- Frontend
- Telegram auth via initData

### 28.04
- initData handlers
- `User` states (created but unused yet)
- Frontend

### 29.04
- Доработки предыдущей задачи
- `User` verification handlers
- Cookie

### 30.04
- Registration system
- Pooling telegram bot

## Май

### 02.05
- Services & routers for menu: `profile / reports / health`
- Frontend

### 03.05
- Services & routers для `Pet` creation with `PetPhotos`
- `User` register

### 06.05

- [aiohttp] Работа с выгрузкой / загрузкой фото на серверах tg
  - отправка фото на сервера тг при создании модели
  - получение ссылок на фото с тг сервера по `file_id`
  - отправка в чат с пользователем с помощью pooling bot (BufferedInputFile)
- Frontend
- Первые шаги в PostGIS

### 07.05
- `Geolocation` db model & Alembic migration
- `Geolocation` schemas / routers / services

### 08.05
- Services & routers для get user `Geolocation`

### 09.05
- func & router для получения `User` city по `Geo.home_location`
- Check city exists

### 10.05
- Minor fixes
- New routers & frontend for `Geo` registration

### 11.05
- Change `Geo` type to `Geography` (to calculate in metres) 
- Separate API
- `Geo` schemas / routers / services: find all geolocations within radius

### 12.05
- Add semaphore 
- Use `asyncio.gather()`
- Frontend

### 14.05
- Upd geography city handler
- Services & routers: get and show nearest reports within `Geo` radius
- `User` settings/update profile router & templates
- Frontend

### 15.05
- `User` settings/update: geo.filter_type & radius router & templates
- `Geolocation` router & templates

### 16.05
- Add `Notification` db model & Alembic migration
- Add `Notification` schemas
- Create API `Notification` service & router
- Add `AsyncSession` initialization in TaskGroup before using parallel session to avoid new connection

### 18.05
- First steps in `RabbitMQ` learning

### 19.05
- Uploading images optimization -> `addReport.js` / `addPet.js` (to avoid server problems)
- Test func `send_notification_to_user()` via pooling bot & fix `Notification` routers/schemas

### 20.05
- `Dockerfile`
- Set up `docker-compose`: web via Dockerfile & pgadmin
- Improvements to raise Docker containers

### 21.05
- Put app to production mode:
  - add `nginx`
  - set up VPS
  - register and set up domain (dogalert.ru) & ssl certificates (HTTPS from certbot)
  - run app on VPS
- Write `Notification` to db after `Report` creation
- Change pika to aio-pika
- Test RabbitMQ for receiving and sending notifications

### 22.05
- Update `Notification` schemas / routers / handlers / broker handlers to add report URL to inline button (notification message from pooling bot)
- Recheck auth using `initData` if web mini app was opened via `Notification` url and not via index page

### 23.05
- Add GeoServices (get nearest users' telegram ids by Geo filter) & API routers
- Set up Report Notification sending by Geo filter
- Some additional fixes

### 24.05
- Add filter to menu/reports page to show nearest reports according to the chosen Geo filter

### 26.05
- Add telegram_photo to User model & schema
- Update telegram_photo_url from initData if User changed tg photo

### 27.05
- update `Pet` info (with no photos) router / template / JS / CSS

### 28.05
- `Pet` photos delete via update_pet page - router / service
- Delete `Pet` - router / template / JS
- Routers fixes & frontend

### 29.05
- Some fixes & linters

### 30.05
- update `Report` info (with no photos) router / template / JS / CSS
- `Report` photos delete via update_report page - router
- Delete `Report` - router / JS

### 1.06
- -
- Some fixes & frontend

### 2.06
- Celery set up
- Celery reminder tasks (vaccination / parasite / fleas ticks reminders)
- Add reminder task ids to `Pet` model to be able to revoke task after date updating

---

## TODO

- [ ] ERD модель (**Entity-Relationship Diagram**)
- Скрыть не API роутеры из сваггера (все равно не работают без initData и cookie)

---

## CONSIDER TO FIX

- Рассмотреть жадную загрузку для некоторых моделей (selectinload() или contains_eager() ???), а также рассмотреть select() отдельных полей вместо всей ORM модели
- в модели SQL User поменять порядок атрибутов (id - первый)
- src/services/pet_photo_service.py - в сервисах create убрать ленивую загрузку, убрать повторный запрос в бд
- телефон - unique=True
- заменить class Config на model_config = ConfigDict(from_attributes=True)
- заменить последовательные асинкс запросы на asyncio.gather() где это возможно
- В хендлерах гео можно получить тип geometry "geometry":{"type": "Point","coordinates": [37.8480995, 55.7848211]}}]}
- src/web/dependencies/city_geo_handles.py -> обрабатывать лучше Point вместо str
- строки 214 - 215 src/web/routers/views/pet_router.py, не работает одновременная отправка нескольких запросов **`asyncio.gather()`** .  
Скорее всего tg блочит одновременные запросы к своим серверам через aiohttp (возможно проблема с ssl / dns)   
Было рассмотрено добавление Семафора для отправки запросов пачками, а не сразу все разом, но это не помогло. Сейчас реализована последовательная обработка
- src/web/main.py -> ssl=False НЕ ДЛЯ ПРОДА!!!
- в сваггере заменить все возвраты на JSON 
- на все API post/put/patch запросы навесить проверку аутентификации
  - не API запросы идут через user_id из куки, что безопасно (??? проверить все равно) + проверить для API запросов на безопасное использование этих запросов
- Везде, где
```
return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
        )
```   
- * добавить redirect_url для перенаправления на no_telegram_login.html + в JS файлах в fetch запросах добавить обработку перенаправления
- удалить include footer в шаблонах, наследуемых от base.html (где нет переопределения footer)
- заменить alert(data.message || 'Text'); на window.Telegram.WebApp.showAlert(data.message || 'Text');. пример в deletePet.js

---

## WELL-KNOWN ISSUES

- При создании питомца или объявления, при выгрузке фотографий, может быть ошибка выгрузки фото из-за запросов к серверам телеграм. Фото сейчас хранятся на серверах телеграм и выгружаются оттуда же. Если хранить фото на удаленном storage, либо локально, ошибки не будет. В случае ошибки - попробовать заново отправить фото. 
- Некоторые страницы могут загружаться с небольшой задержкой, особенно если запрос к этим страницам требует несколько запросов к бд и обработки большого объема данных. В будущем рассмотреть замену html/css/js на react или vue, с подзагрузкой всех необходимых данных сразу при старте приложения для избежания дополнительных get и бд запросов. 

