# Roomito - Faculty Space Management System

Roomito is a faculty space reservation and management system developed to digitize and optimize the use of physical spaces like meeting rooms, classrooms, and auditoriums. The platform aims to eliminate the inefficiencies of traditional manual reservation processes and provides a unified solution for space booking by students, professors, staff, and academic groups.

---

## ⚙️ Tech Stack

- **Backend:** Django 5.2.4, Django REST Framework
- **Database:** PostgreSQL (Dockerized)
- **Authentication:** JWT (via SimpleJWT)
- **API Documentation:** Swagger (drf-spectacular)
- **Containerization:** Docker & Docker Compose
- **Python Version:** 3.11

---

## 🚀 Getting Started

### 🔧 Prerequisites

* Python 3.11+
* Docker installed
* Git installed

---

### 📥 Clone the Project

* git clone <https://github.com/roomito-project/backend.git>
* cd backend

---

### ☁️ Setup with Docker

# Build and run containers
docker-compose up --build

# (Optional) Apply migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

---

### 🐍 Local Development (Optional)

If you prefer running the project locally:

# Create virtual environment
* python -m venv venv
* venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Run Django server
python manage.py runserver

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