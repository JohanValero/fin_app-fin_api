FROM python:3.12-slim

WORKDIR /ws

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "api.main"]