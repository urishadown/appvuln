FROM python:3.13-alpine

WORKDIR /app

COPY app/ /app/

RUN pip install --no-cache-dir flask

EXPOSE 8080

CMD ["python", "app.py"]
