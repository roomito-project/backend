# Roomito - Faculty Space Management System

Roomito is a faculty space reservation and management system developed to digitize and optimize the use of physical spaces like meeting rooms, classrooms, and auditoriums. The platform aims to eliminate the inefficiencies of traditional manual reservation processes and provides a unified solution for space booking by students, professors, staff, and academic groups.

## 🧠 Project Summary

**"A Smart System for Scheduling, Sharing, and Managing Faculty Spaces."**

Users can easily browse available spaces and make reservations based on type, date, and availability. The system improves productivity and aligns with digital transformation goals in universities and academic institutes.

---

## ⚙️ Tech Stack

- **Backend:** Django 5.2.4, Django REST Framework
- **Database:** PostgreSQL (Dockerized)
- **Authentication:** JWT (via SimpleJWT)
- **API Documentation:** Swagger (drf-spectacular)
- **Frontend:** React (not included here)
- **Containerization:** Docker & Docker Compose
- **Python Version:** 3.11

---

## 📁 Project Structure

backend/
├── roomito/               # Core Django project
│   ├── settings.py        # Configuration & DB setup
│   └── urls.py
├── professors/            # App for professor features
├── students/              # App for student features
├── space_managers/        # App for space manager features
├── manage.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt

---

## 📦 Requirements

### 🐍 Python Dependencies (`requirements.txt`)

asgiref==3.9.1
Django==5.2.4
djangorestframework==3.16.0
djangorestframework_simplejwt==5.5.0
psycopg2-binary==2.9.10
PyJWT==2.9.0
python-decouple==3.8
sqlparse==0.5.3
tzdata==2025.2
Pillow==10.3.0
drf-spectacular==0.27.1

---

## 🚀 Getting Started

### 🔧 Prerequisites

* Python 3.11+
* Docker & Docker Compose installed
* Git installed

---

### 📥 Clone the Project

git clone <repo-url>
cd backend

---

### ☁️ Setup with Docker (Recommended)

# Build and run containers
docker-compose up --build

# (Optional) Apply migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

> ✅ Database is automatically provisioned using Docker.

---

### 🐍 Local Development (Optional)

If you prefer running the project locally:

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Run Django server
python manage.py runserver


Ensure your local PostgreSQL DB is running and configured to match `settings.py`.

---

## 🔐 API Overview

Swagger UI is available at:

http://127.0.0.1:8000/api/swagger/

### Key Endpoints

* **Professors**

  * `POST /api/professor/register/`
  * `POST /api/professor/login/`
  * `POST /api/professor/verify/`

* **Students**

  * `POST /api/student/register/`
  * `POST /api/student/login/`

* **Space Managers**

  * `POST /api/spacemanager/login/`
  * `GET /api/spacemanager/profile/`
  * `POST /api/spacemanager/change-password/`

* **Events & Spaces**

  * `GET /api/events/list/`
  * `GET /api/spaces/list/`
  * `GET /api/events/{event_id}/`

---

## 🧪 Testing

> Not implemented yet (can be added using `pytest` or `Django TestCase` suite)

---

## 🧾 License

MIT License — feel free to use and modify for educational or internal purposes.

---

## 👥 Contributors

* Backend: Mahya Jafari
* Frontend: \[Mohadese Baghbani]

---

## 📌 Notes

* All environment variables are configured via `settings.py`.
* PostgreSQL container auto-creates DB with user/pass specified in `docker-compose.yml`.
* Images uploaded for events are stored in the `media/` directory, mapped inside Docker.