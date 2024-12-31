FROM python:3.12-alpine

RUN mkdir /opt/s1

WORKDIR /opt/s1

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .
# 8016
EXPOSE 8016

RUN chmod +x ./init.sh

CMD ["/bin/sh", "-c", "./init.sh"]