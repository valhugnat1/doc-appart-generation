# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY agent_recup_info/requirements.txt ./agent_recup_info/requirements.txt
COPY fastapi_app/requirements.txt ./fastapi_app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r agent_recup_info/requirements.txt
RUN pip install --no-cache-dir -r fastapi_app/requirements.txt

# Copy the application code
COPY agent_recup_info ./agent_recup_info
COPY bail_generation_script ./bail_generation_script
COPY fastapi_app ./fastapi_app
COPY data ./data

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "fastapi_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
