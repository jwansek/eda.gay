FROM ubuntu:22.04
MAINTAINER Eden Attenborough "eden.attenborough@outlook.com"
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential clang libffi-dev libxml2-dev libxslt-dev libjpeg-dev zlib1g-dev
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3"]
CMD ["app.py", "--production"]
