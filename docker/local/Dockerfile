# syntax=docker/dockerfile:1

FROM nikolaik/python-nodejs:latest

RUN apt-get update && apt-get install -y ca-certificates

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN npm install -g nodemon

COPY . .

CMD ["python3", "run.py"]