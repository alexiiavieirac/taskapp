# Usa imagem leve do Python
FROM python:3.11-slim

# Evita prompts na instalação de pacotes do sistema
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependências do sistema necessárias para compilar pacotes Python
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo requirements.txt da raiz do projeto para o container
COPY requirements.txt /tmp/requirements.txt

# Instala dependências
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia todo o restante do projeto para dentro do container
COPY . .

# Expõe a porta padrão do Flask
EXPOSE 5000

# Define ambiente de produção para o Flask (opcional)
ENV FLASK_ENV=production

# Comando de inicialização da aplicação
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000", "--worker-class", "gevent"]

