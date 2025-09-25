FROM python:3.11-slim

#FFmpeg
RUN apt-get update \
 && apt-get -yy install ffmpeg gcc \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

#Requirements
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3000"]
