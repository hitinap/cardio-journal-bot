FROM python:3.12

WORKDIR /usr/src/app/
COPY . /usr/src/app/

RUN pip install --user pytelegrambotapi
RUN pip install --user APScheduler

CMD ["python", "main.py"]

EXPOSE 80 443
