FROM python:3.11-slim

# FFmpeg + MariaDB client libs
RUN apt-get update \
 && apt-get -yy install libmariadb3 libmariadb-dev gcc ffmpeg \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# create data folders
RUN mkdir -p /usr/src/app/data/uploads /usr/src/app/data/outputs

CMD ["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3000"]
