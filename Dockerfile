# 1) Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend .
RUN npm run build

# 2) Backend runtime
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    IPC_SQLITE_PATH=/app/data/ipc_perfcalc.db

WORKDIR /app

# system deps for building wheels (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
# copy built frontend to static directory
COPY --from=frontend-build /app/frontend/dist ./static

RUN mkdir -p /app/data

EXPOSE 3154

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3154"]
