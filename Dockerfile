FROM python:3.9

COPY data /opt/data

COPY whatsNext /opt/whatsNext

ADD wsgi.py /opt/wsgi.py

ADD requirements.txt /

RUN pip3 install -r /requirements.txt

WORKDIR /opt

EXPOSE 8000

CMD gunicorn --bind 0.0.0.0 --timeout 600 --access-logfile - --access-logformat '%(h)s %(t)s "%(r)s" Status Code: %(s)s Response Took: %(L)s Seconds' wsgi:app