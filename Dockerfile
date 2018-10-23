FROM python:2-alpine
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
ENTRYPOINT [ "python", "./main.py" ]