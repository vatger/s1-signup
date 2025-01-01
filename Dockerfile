FROM python:3.12-alpine

RUN mkdir /opt/s1

WORKDIR /opt/s1

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 80

RUN chmod +x ./init.sh
RUN chmod +x S1/initial_setup.sh

RUN apk add --no-cache nginx
COPY config/default.conf /etc/nginx/http.d/default.conf

CMD ["/bin/sh", "-c", "./init.sh"]