# 📝 Consent Agreement Web App

[![API CI/CD](https://github.com/software-students-spring2025/5-final-finallapis/actions/workflows/api-ci.yml/badge.svg)](https://github.com/software-students-spring2025/5-final-finallapis/actions/workflows/api-ci.yml)
[![Event Logger CI](https://github.com/software-students-spring2025/5-final-finallapis/actions/workflows/event-logger.yml/badge.svg)](https://github.com/software-students-spring2025/5-final-finallapis/actions/workflows/event-logger.yml)

---

**Consent Agreement Web App** is a containerized full-stack application that enables users to create, sign, and manage digital consent agreements securely.

**System Components:**
- 🌐 **Web App (Flask API)**: Provides user registration, login, agreement creation, signature capture, and search functionality.
- 🗄️ **MongoDB**: A NoSQL database for storing user accounts and consent agreements.

The system uses Docker, Docker Compose, and GitHub Actions for automated CI/CD pipelines. MongoDB and Flask services are deployed as independent containerized subsystems.

---

## 🚀 How to Run the Project

### ✅ Prerequisites

- Docker & Docker Compose
- Git installed
- (Optional) SSH key configured for GitHub access

---

### 🛠 Setup Instructions

#### 1. Clone the repository

```bash
git clone git@github.com:software-students-spring2025/5-final-finallapis.git
cd 5-final-finallapis
```

#### 2. Configure environment variables

Create a `.env` file in the root directory:

```bash
cp env.example .env
```

Edit the `.env` file:

```env
FLASK_SECRET_KEY=your_secret_here
MONGO_URI=mongodb://mongodb:27017/consent_data
```

✅ This environment file sets up your Flask app secret and MongoDB connection.

---

#### 3. Start the system using Docker Compose

```bash
docker-compose up --build
```

📍 Visit your app at [http://localhost:5050](http://localhost:5050)

✅ You can now register accounts, create agreements, and sign them!

---

## 🧪 Running Unit Tests

Tests are implemented using `pytest` and `pytest-cov`.

Run tests inside the running container:

```bash
docker exec -it api bash
pytest --maxfail=3 --disable-warnings --tb=short
```

Or with code coverage:

```bash
pytest --cov=.
```

✅ Minimum 80% test coverage achieved.

---

## 🧰 Developer Workflow

- ✅ All code changes should use feature branches.
- ✅ Unit tests with 80%+ coverage for each subsystem.
- ✅ CI pipelines run tests, build Docker images, and deploy on each push or PR to main.
- ✅ Docker images are built and pushed to DockerHub.

---

## 🐳 Docker Images

| Subsystem | DockerHub Image |
|:---|:---|
| Web App (Flask API) | [DockerHub Link Placeholder] |
| MongoDB | Official `mongo:latest` |

> Replace the placeholder link with your actual DockerHub repository link after uploading images.

---

## 📦 CI/CD Pipelines

Each subsystem has its own GitHub Actions workflow:

| Subsystem | Workflow |
|:---|:---|
| API | [.github/workflows/api-ci.yml](.github/workflows/api-ci.yml) |
| Event Logger | [.github/workflows/event-logger.yml](.github/workflows/event-logger.yml) |

✅ Workflows automatically:

- Run unit tests
- Build Docker images
- Push to DockerHub
- Prepare for deployment to DigitalOcean

---

## 👥 Team Members

| Name           | GitHub Profile                                     |
|----------------|----------------------------------------------------|
| **Yang Hu**    | [@younghu312](https://github.com/younghu312)       |
| **Ziqi Huang** | [@RyanH0417](https://github.com/RyanH0417)         |
| **Zirui Han**  | [@ZiruiHan](https://github.com/ZiruiHan)           |
| **Zichao Jin** | [@ZichaoJin](https://github.com/ZichaoJin)         |

---

## 🗂️ Project Structure

```plaintext
5-final-finallapis/
├── api/                  # Flask Web App
│   ├── app.py
│   ├── templates/
│   └──static/
│  
├── .github/
│   └── workflows/         # GitHub Actions workflows
├── docker-compose.yml     # Docker Compose orchestration
├── Dockerfile             # Dockerfile for API
├── env.example            # Example environment variables
├── tests/                 # Unit tests     
└── README.md              # Project documentation
```

---

## 📜 License

Developed as part of NYU’s Software Engineering course, Spring 2025.  
Not licensed for commercial use.

---
