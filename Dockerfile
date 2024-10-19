
FROM python:3.10.8-slim-buster

WORKDIR /code

ADD . /code

RUN pip install --no-cache-dir -r requirements.txt

COPY .env /code/.env

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
