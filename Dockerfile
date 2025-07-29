FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app/roomito 

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY roomito/ /app/roomito/  

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]