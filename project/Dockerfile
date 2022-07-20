FROM python:3
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
COPY . /app
WORKDIR /app
# CMD ["gunicorn", "-k", "eventlet", "-w", "1", "--reload", "-b", "0.0.0.0:80", "app:app"]
# CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w", "1", "--reload", "-b", "0.0.0.0:8000", "app:app"]
# CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w", "1", "--reload", "-b", "0.0.0.0:8000", "app:app"]
# CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w", "1", "--reload", "app:app"]
CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w", "1", "--reload", "-b", "0.0.0.0:8000", "app:app"]
# CMD gunicorn --bind 0.0.0.0:8000 -w 1 app:app
# ENTRYPOINT gunicorn app:app -b 0.0.0.0:80