FROM ubuntu:latest
MAINTAINER Eden Attenborough "eda@e.email"
RUN apt-get update -y
RUN apt-get install -y python3-pip python-dev build-essential
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3"]
CMD ["app.py", "--production"]