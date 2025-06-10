# DogAlert 🐶
Telegram web application for finding lost pets with geolocation notifications  
[![Author](https://img.shields.io/badge/Author-@artyombn-blue)](https://t.me/artyombn)

PHOTOS
PHOTOS

## 🐈 ABOUT
DogAlert is a Telegram web application designed to help find lost pets using geolocation-based notifications. It allows users to report about lost pets, receive alerts based on their location, send pets' health reminders to owners and connect with others to reunite pets with their owners. The application is powered by a modern tech stack and deployed on a VPS with HTTPS support for seamless integration with Telegram Web Apps.

## ✨ Features
* **Report Lost Pets:** Users can submit details about lost pets, including photos.
* **Geolocation Notifications:** Receive real-time notifications about pets reported near your location or your city using PostGIS-powered geospatial queries.
* **Telegram Web Mini App:** Seamless user experience within Telegram web apps, leveraging HTTPS for secure communication.
* **Asynchronous Backend:** Fast and scalable API with FastAPI and async SQLAlchemy for efficient data handling.
* **Task Queue:** Background tasks (e.g., notifications, reminders) managed by Celery, Celery Beat and RabbitMQ.
* **Responsive Frontend:** Built with Bootstrap and internal Telegram theme for a mobile-friendly interface.

## ⚙️ System dependencies
- **Python 3.12**
- **Docker** and **Docker Compose**
- **Make** (for running Makefile commands)
- **Nginx** (with SSL certificates for production)
- **PostgreSQL** with **PostGIS** extension
- **RabbitMQ** for message brokering

## 🌐 Nginx certificates config
- **NOTE:** Receive SSL certificates to start application properly. 
- Place certificates to nginx/ssl.
- Rename `nginx/nginx-local.conf` to `nginx/nginx.conf` and configure it.

## 🐳 Start with Docker compose
- Clone the repository ```git clone https://github.com/artyombn/dogalert.git```  
- Rename `.copy_env` to `.env` and configure it.
- Run `docker compose build` command then `docker compose up -d` to start the app.
- **NOTE:** Comment migration commands in `run_all.sh` after first successful applying migrations.

Make sure that SSL certificates is configured correctly  
Check `Makefile` to see all available commands.  

## 🚀 Start locally
* Ensure `PostgreSQL` and `RabbitMQ` are running locally.
* Change `Docker=False` in `.env` file.
* Use `run_all.sh` to apply migrations and fill db
* Run Celery ```celery --app src.celery_app.config worker --loglevel INFO```
* Run RMQ consumer ```python3 src/broker/consumer.py```
* Run app ```python3 -m src.app```
* Telegram Web Apps require HTTPS. Use `ngrok` for local running
  * ```ngrok http 8001 --url https://your_ngrok_url```


## 🛠️ Tech Stack
#### Backend:
* **Python 3.12** — Core programming language.
* **FastAPI:** — High-performance web framework for building APIs.
* **Uvicorn:** — ASGI server for running FastAPI.
* **SQLAlchemy (async):** — ORM for database interactions.
* **GeoAlchemy 2:** — Support for geospatial data via PostGIS.
* **PostgreSQL + PostGIS:** — Relational database with geospatial extensions.
* **Alembic:** — Lightweight database migration tool.
* **Pydantic v2:** — Data validation and settings management.
* **aiohttp:** — Asynchronous HTTP client for external API calls.

#### Telegram Pooling Bot:
* **Aiogram 3:** — Framework for building Telegram bots with async support.

#### Message Broker and Background Tasks:
* **RabbitMQ + aio-pika:** — Message broker for task queue management.
* **Celery:** — Distributed task queue for handling background tasks.
* **Celery Beat:** — Scheduler within the Celery framework (launch tasks at specific times or intervals)

#### Frontend:
* **Bootstrap:** — Responsive CSS framework.
* **HTML + CSS + JavaScript:** — Lightweight frontend for Telegram Web App.

#### Инфраструктура и DevOps:
* **Docker + Docker Compose:** — Containerization for consistent development and deployment.
* **Nginx:** — Reverse proxy for serving the application with HTTPS support.

For a complete list of dependencies, check `pyproject.toml`

## 🗺️ Architecture
The project follows a modular architecture, as outlined in the C4 model diagrams:

* **Backend Diagram:** `docs/architecture/backend_diagram.drawio-2.svg`
* **Container Diagram:** `docs/architecture/container_diagram.drawio.svg`

These diagrams provide a high-level overview of the system's components and interactions.

## 📄 Other Docs
* `docs/DEVLOGS.md` — devs and change logs
* `docs/architecture/` — C4 model diagrams