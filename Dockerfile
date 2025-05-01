FROM python:3.11-slim

# Evita prompts do apt
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    curl \
    && apt-get clean

# Cria diretório de trabalho
WORKDIR /app

# Copia os requisitos primeiro para aproveitar cache do Docker
COPY requirements.txt .

# Instala a versão mais recente do pip e as dependências
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Expõe a porta que a app Flask irá rodar
EXPOSE 5000

# Comando para iniciar a aplicação (ajuste para seu script real)
CMD ["python", "app.py"]
