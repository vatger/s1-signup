FROM python:3.12-alpine

RUN mkdir /opt/s1

WORKDIR /opt/s1

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 8016

RUN chmod +x ./init.sh
RUN chmod +x S1/initial_setup.sh

CMD ["/bin/sh", "-c", "./init.sh"]