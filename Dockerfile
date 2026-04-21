FROM python:3.10-slim

WORKDIR /app

# Install system dependencies necessary for compiling some python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies first to cache docker layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all projects files (backend, frontend, openenv configs)
COPY . .

# Expose backend server port
EXPOSE 8000

# Specify how to run the app
ENV PYTHONPATH=/app/backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
