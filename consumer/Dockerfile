FROM python:3.9

WORKDIR /usr/app

ADD ./requirements.txt ./
RUN pip install -r requirements.txt
ADD ./ ./

CMD gunicorn --bind 0.0.0.0:5000 --worker-class eventlet -w 1 app:app
