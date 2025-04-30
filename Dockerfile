FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

# Instala pacotes do sistema necessários para compilar certas dependências
RUN apt-get update && apt-get install -y build-essential default-libmysqlclient-dev gcc

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
