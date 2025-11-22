FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip

WORKDIR /app

COPY .. /app

RUN pip3 install --break-system-packages flask requests


EXPOSE 5000

CMD ["python3", "purchase.py"]
