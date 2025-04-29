# Final Project

An exercise to put to practice software development teamwork, subsystem communication, containers, deployment, and CI/CD pipelines. See [instructions](./instructions.md) for details.

# Consent Agreement Web App

![API CI/CD](https://github.com/software-students-spring2025/5-final-finallapis/actions/workflows/api-ci.yml/badge.svg)

---

## Project Overview

This project is a full-stack web application that allows users to create, sign, and manage consent agreements online.

The system consists of two containerized subsystems:

- **Web App (Flask, Python)**: Provides the frontend and backend for user registration, authentication, agreement creation, and signature collection.
- **MongoDB Database**: Stores user data and agreements securely.

Both subsystems are containerized using Docker and integrated with CI/CD pipelines using GitHub Actions.  
This project demonstrates database integration, container orchestration, and full software development workflows.

---

## Team Members

- [Zirui Han](https://github.com/ZiruiHan)

---

## Architecture

- Python 3.9 (Flask API)
- MongoDB (NoSQL database)
- Docker & Docker Compose
- GitHub Actions (CI/CD for both subsystems)

Each subsystem is deployed and maintained independently.

---

## Docker Images

| Subsystem | DockerHub Image |
|:---|:---|
| Web App (API) | [DockerHub Link Placeholder] |
| MongoDB | Official `mongo:latest` image |

> **Note**: Replace "Placeholder" with your real DockerHub image link after you push your image.

---

## How to Run Locally

### Prerequisites

- Docker installed
- Docker Compose installed
- Git installed
- SSH access set up for GitHub (optional but recommended)

### Setup Instructions

1. Clone the repository:

```bash
git clone git@github.com:software-students-spring2025/5-final-finallapis.git
cd 5-final-finallapis
```

2. Create a real `.env` file from the provided example:

```bash
cp env.example .env
```

Edit `.env` to set any secrets.

Example `.env`:

```env
FLASK_SECRET_KEY=your_secret_key_here
MONGO_URI=mongodb://mongodb:27017/consent_data
```

3. Build and start all services:

```bash
docker-compose up --build
```

4. Open your browser and navigate to:

```
http://localhost:5050
```

✅ You can now register, login, create agreements, and sign them!

---

## Running Unit Tests

To run tests inside the Docker container:

```bash
docker exec -it api bash
pytest --maxfail=3 --disable-warnings --tb=short
```

or with coverage:

```bash
pytest --cov=.
```

✅ Minimum 80%+ coverage is achieved as required.

---

## Environment Variables

| Variable | Description |
|:---|:---|
| `FLASK_SECRET_KEY` | Secret key for session management |
| `MONGO_URI` | MongoDB connection URI |

> You must create a `.env` file based on `env.example` before running locally.

---

## Example of `env.example`

```env
FLASK_SECRET_KEY=changeme123
MONGO_URI=mongodb://mongodb:27017/consent_data
```

✅ Never commit real secrets to GitHub.  
✅ `.env` is listed in `.gitignore`.

---

## Deployment

The API and MongoDB containers are ready to deploy on DigitalOcean or any cloud provider using Docker Compose.

GitHub Actions automatically:

- Build Docker images
- Run unit tests
- Push images to DockerHub
- Prepare for deployment

CI/CD is triggered by any push or pull request to `main` or `master`.

---

## CI/CD Workflows

Two GitHub Actions workflows are configured:

| Subsystem | CI/CD Workflow |
|:---|:---|
| API | [.github/workflows/api-ci.yml](.github/workflows/api-ci.yml) |
| Event Logger | [.github/workflows/event-logger.yml](.github/workflows/event-logger.yml) |

✅ Separate workflows for each subsystem  
✅ Badges displayed at top of README

---

## 📋 Important Notes

- If you update the `.env` file, restart your containers (`docker-compose down && docker-compose up --build`).
- Always run tests inside the container, not your local machine directly.
- MongoDB service name must match `mongodb` inside Docker Compose networking.

---

# 🚀 Thanks for checking out our project!

This project demonstrates full software engineering workflows, from containerization and database integration to CI/CD pipelines and automated deployment readiness.
