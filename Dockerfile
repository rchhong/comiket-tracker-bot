# syntax=docker/dockerfile:1

FROM nikolaik/python-nodejs:latest


WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN npm install -g nodemon

COPY . .

CMD ["python3", "bot.py"]