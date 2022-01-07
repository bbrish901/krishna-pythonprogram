FROM python:3.9.7-alpine
WORKDIR /flask-app
ADD . /flask-app
RUN pip install -r requirements.txt
CMD ["python","app.py"]
