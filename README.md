# WorkSight

WorkSight is a comprehensive employee activity monitoring and productivity management system. It consists of two main components: a **monitoring agent** that runs on employee machines to capture activity data, and a **Django-based backend server** for processing, storing, and visualizing that data.

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [API Endpoints](#api-endpoints)
- [Database](#database)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

WorkSight enables organizations to:
- Monitor employee activities on monitored machines
- Capture periodic screenshots and recordings
- Track heartbeats and system information
- Upload data to cloud storage
- Analyze productivity trends through a web dashboard

The system consists of:
- **Agent**: A lightweight Python application that runs on monitored machines
- **Server**: A Django-based REST API and web dashboard for data management and visualization

## Project Structure

```
WorkSight/
├── agent/                          # Monitoring agent application
│   ├── main.py                     # Entry point for the agent
│   ├── config.py                   # Agent configuration
│   ├── runtime.py                  # Main agent runtime
│   ├── api_client.py               # API communication handler
│   ├── logger.py                   # Logging configuration
│   ├── system_info.py              # System information gathering
│   ├── credentials/                # Credentials and keys (version controlled)
│   │   └── credentials.json        # Google Drive credentials
│   ├── cloud/                      # Cloud storage integration
│   │   ├── drive_client.py         # Google Drive client
│   │   └── test_drive_upload.py    # Drive upload tests
│   ├── recording/                  # Screen recording module
│   │   ├── screen_capture.py       # Screenshot capture
│   │   ├── screen_recorder.py      # Video recording
│   │   └── test_recording.py       # Recording tests
│   ├── services/                   # Background services
│   │   ├── heartbeat_service.py    # Heartbeat manager
│   │   ├── recording_service.py    # Recording scheduler
│   │   └── screenshot_service.py   # Screenshot scheduler
│   └── storage/                    # Local storage management
│       ├── base.py                 # Base storage class
│       ├── local.py                # Local file storage
│       ├── cleanup.py              # Storage cleanup utility
│       ├── logs/                   # Agent logs (generated)
│       ├── screenshots/            # Captured screenshots (generated)
│       └── videos/                 # Recorded videos (generated)
├── server/                         # Django backend server
│   ├── manage.py                   # Django management script
│   ├── worksight_server/           # Django project settings
│   │   ├── settings.py             # Django configuration
│   │   ├── urls.py                 # URL routing
│   │   ├── asgi.py                 # ASGI configuration
│   │   └── wsgi.py                 # WSGI configuration
│   └── monitoring/                 # Monitoring app
│       ├── models.py               # Database models
│       ├── views.py                # API views
│       ├── urls.py                 # App URL routing
│       ├── admin.py                # Django admin configuration
│       ├── migrations/             # Database migrations
│       └── templates/
│           └── monitoring/
│               └── dashboard.html  # Web dashboard
├── docs/                           # Documentation
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- MySQL Server (for database)
- Google Cloud credentials (for Google Drive integration)
- ffmpeg (for video encoding, optional)

## Installation

### 1. Clone and Navigate to Project

```bash
cd WorkSight
```

### 2. Create Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Django Configuration
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.mysql
DB_NAME=worksight_db
DB_USER=root
DB_PASSWORD=your_db_password
DB_HOST=127.0.0.1
DB_PORT=3306

# Agent Configuration
AGENT_NAME=WorkSight-Agent
AGENT_VERSION=0.1.0
BACKEND_BASE_URL=http://127.0.0.1:8000/api

# Cloud Storage (Google Drive)
GOOGLE_DRIVE_CREDENTIALS_PATH=agent/credentials/credentials.json
```

### 5. Database Setup

```bash
# Navigate to server directory
cd server

# Apply migrations
python manage.py migrate

# Create superuser for admin panel
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## Configuration

### Agent Configuration

Edit `agent/config.py` to customize:

```python
SCREENSHOT_INTERVAL_SECONDS = 10      # Screenshot capture frequency
SCREENSHOT_FORMAT = "png"              # Image format
LOG_LEVEL = "INFO"                     # Logging level
BACKEND_BASE_URL = "http://127.0.0.1:8000/api"
```

### Server Configuration

Edit `server/worksight_server/settings.py` to customize:

```python
DEBUG = True                           # Set to False in production
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
INSTALLED_APPS = [...]                # Add/remove apps as needed
```

## Running the Application

### 1. Start the Django Server

```bash
cd server
python manage.py runserver 0.0.0.0:8000
```

The server will be available at `http://localhost:8000`

### 2. Start the Monitoring Agent

In a new terminal, with the virtual environment activated:

```bash
cd agent
python main.py
```

The agent will start capturing screenshots and sending data to the backend server.

### 3. Access the Dashboard

- **Admin Panel**: `http://localhost:8000/admin/`
- **Monitoring Dashboard**: `http://localhost:8000/monitoring/dashboard/`

## Architecture

### Agent Architecture

```
┌─────────────────────────────────────┐
│    WorkSightAgent (main.py)         │
├─────────────────────────────────────┤
│  Services:                          │
│  • HeartbeatService                 │
│  • ScreenshotService                │
│  • RecordingService                 │
├─────────────────────────────────────┤
│  Modules:                           │
│  • ScreenCapture                    │
│  • ScreenRecorder                   │
│  • DriveClient                      │
│  • APIClient                        │
├─────────────────────────────────────┤
│  Storage:                           │
│  • Local Storage (screenshots/logs) │
│  • Cloud Storage (Google Drive)     │
└─────────────────────────────────────┘
```

### Server Architecture

```
┌──────────────────────────────────┐
│    Django REST API               │
├──────────────────────────────────┤
│  • ScreenshotLog endpoints       │
│  • AgentHeartbeat endpoints      │
│  • AgentToken endpoints          │
│  • Recording endpoints           │
├──────────────────────────────────┤
│  Database Models:                │
│  • Agent                         │
│  • AgentHeartbeat               │
│  • ScreenshotLog                │
│  • Recording                    │
├──────────────────────────────────┤
│  Frontend:                       │
│  • Dashboard (dashboard.html)    │
└──────────────────────────────────┘
```

## Key Features

### Agent Features

- **Screenshot Capture**: Automatic periodic screenshot capture
- **Video Recording**: Screen recording with configurable intervals
- **Heartbeat Monitoring**: Periodic heartbeat signals to server
- **System Information**: Collects system metadata
- **Cloud Integration**: Automatic upload to Google Drive
- **Logging**: Comprehensive agent activity logging
- **Credential Management**: Secure credential handling

### Server Features

- **REST API**: Full-featured API for data ingestion and retrieval
- **Database Models**: Django ORM models for agents, heartbeats, and recordings
- **Admin Interface**: Django admin for data management
- **Dashboard**: Web-based monitoring dashboard
- **User Authentication**: Agent token-based authentication
- **Data Aggregation**: Heartbeat and screenshot log aggregation

## API Endpoints

### Screenshots

- `GET /api/screenshots/` - List all screenshots
- `POST /api/screenshots/` - Create new screenshot record
- `GET /api/screenshots/{id}/` - Get screenshot details
- `DELETE /api/screenshots/{id}/` - Delete screenshot

### Heartbeats

- `GET /api/heartbeats/` - List all heartbeats
- `POST /api/heartbeats/` - Create new heartbeat
- `GET /api/heartbeats/{id}/` - Get heartbeat details

### Agents

- `GET /api/agents/` - List all agents
- `POST /api/agents/` - Register new agent
- `GET /api/agents/{id}/` - Get agent details

### Recordings

- `GET /api/recordings/` - List all recordings
- `POST /api/recordings/` - Create new recording
- `GET /api/recordings/{id}/` - Get recording details

## Database

The project uses MySQL as the default database. Key models include:

### Agent Model
- Stores agent information and metadata
- Links to heartbeats and screenshot logs

### AgentHeartbeat Model
- Periodic heartbeat from agents
- Includes timestamp and system status
- Links to parent agent

### ScreenshotLog Model
- Records screenshot metadata
- Includes capture timestamp and file path
- Links to agent

### Recording Model
- Stores video recording information
- Includes start/end times and file path

## Troubleshooting

### Agent Won't Connect to Server

1. Verify server is running: `http://localhost:8000/api/sessions/`
2. Check `BACKEND_BASE_URL` in `agent/config.py`
3. Review agent logs in `agent/storage/logs/`

### Database Connection Error

1. Verify MySQL is running
2. Check database credentials in `.env`
3. Run migrations: `python manage.py migrate`

### Google Drive Upload Fails

1. Verify `credentials.json` exists in `agent/credentials/`
2. Check Google Drive API is enabled in Google Cloud Console
3. Review drive upload logs in `agent/storage/logs/`

### Screenshot Capture Issues

1. Check disk space in `agent/storage/screenshots/`
2. Verify file permissions
3. Review screenshot service logs

### Port Already in Use

If port 8000 is in use, start the server on a different port:

```bash
python manage.py runserver 8001
```

Then update `BACKEND_BASE_URL` in `agent/config.py`.

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes and commit: `git commit -m 'Add your feature'`
3. Push to the branch: `git push origin feature/your-feature`
4. Submit a pull request

## License

This project is proprietary. All rights reserved.

---

**Last Updated**: February 2026  
**Version**: 0.1.0
