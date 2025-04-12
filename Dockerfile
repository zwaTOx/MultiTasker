FROM python:3.12.8

WORKDIR /app
COPY /app .
RUN pip install -r requerements.txt

CMD ["python", "main.py"]