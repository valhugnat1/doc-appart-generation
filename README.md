# Bail Generator Project

This project is an AI-powered tool for generating French rental lease documents (Bail de location). It consists of a FastAPI backend with an AI agent and a Vue.js frontend.

## Project Structure

- **`backend/`**: Contains the FastAPI application, AI agent, and PDF generation scripts.
- **`frontend/`**: Contains the Vue.js web interface.
- **`docker-compose.yml`**: Orchestrates the application services.

## Prerequisites

- Docker and Docker Compose
- OpenAI API Key (or compatible LLM provider)

## Installation & Usage

### 1. Environment Setup

Create a `.env` file in the root directory (or ensure it exists) with your API key:

```bash
OPENAI_API_KEY=your_api_key_here
```

### 2. Build and Run with Docker

The easiest way to run the application is using Docker Compose.

**Build the images:**
```bash
docker-compose build
```

**Start the application:**
```bash
docker-compose up
```

### 3. Access the Application

- **Frontend**: Open [http://localhost:8080](http://localhost:8080) in your browser.
- **Backend API**: Accessible at [http://localhost:8000](http://localhost:8000).
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs).

## Manual Development

If you prefer to run the services locally without Docker:

### Backend
```bash
cd backend
pip install -r fastapi_app/requirements.txt
python -m fastapi_app.main
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
