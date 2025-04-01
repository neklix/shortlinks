FROM python:3.11

WORKDIR /app

COPY src/ /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
