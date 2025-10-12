FROM python:3.12-slim

# RUN groupadd -r group_aiohttp
# RUN useradd -r -g group_aiohttp user_aiohttp

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1

RUN pip install --upgrade pip

WORKDIR /app/www/photo-contest

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# USER user_aiohttp
