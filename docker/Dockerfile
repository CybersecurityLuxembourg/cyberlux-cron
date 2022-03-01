ARG PYTHON_VERSION=3.8-slim-buster
FROM python:$PYTHON_VERSION

ENV PYTHONUNBUFFERED=1

ARG ENVIRONMENT=production

ENV JWT_SECRET_KEY=k3y_t0_ch4ng3_2A845
ENV DB_DRIVER=mysql+pymysql
ENV DB_NAME=CYBERLUX
ENV DB_PORT=3306
ENV DB_HOSTNAME=cyberlux-db
ENV DB_USERNAME=cyberlux
ENV DB_PASSWORD=cyberlux-pwd

WORKDIR /app

RUN pip install gunicorn[gevent]

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY db             /app/db
COPY decorator      /app/decorator
COPY exception      /app/exception
COPY migrations     /app/migrations
COPY resource       /app/resource
COPY template       /app/template
COPY utils          /app/utils

COPY routes.py      /app/
COPY app.py 		/app/app.py

COPY config         /app/config
COPY docker/entrypoint.sh /entrypoint.sh

EXPOSE 5001

CMD /entrypoint.sh