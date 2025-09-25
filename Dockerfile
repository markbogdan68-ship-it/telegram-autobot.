FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# кладём весь код из репозитория в контейнер
COPY . .

ENV TZ=Europe/Berlin
EXPOSE 8080

# у тебя файлы лежат в корне (main.py), запускаем как модуль
CMD ["python", "-m", "main"]
