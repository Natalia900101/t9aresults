FROM python
ENV PORT=8000

ADD requirements.txt /
RUN pip3 install -r /requirements.txt

EXPOSE $PORT

ADD . /project
WORKDIR /project
CMD python manage.py makemigrations && \
    python manage.py migrate && \
    python manage.py runserver 0.0.0.0:$PORT