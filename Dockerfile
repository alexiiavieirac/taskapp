# Usa imagem leve do Python
FROM python:3.11-slim

# Evita prompts interativos
ENV DEBIAN_FRONTEND=noninteractive

# Instala pacotes essenciais do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libssl-dev \
    libffi-dev \
    default-libmysqlclient-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório de trabalho
WORKDIR /app

# Copia o requirements.txt primeiro (melhora cache)
COPY requirements.txt .

# Instala dependências em um único passo
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o restante da aplicação
COPY . .

# Expõe a porta 5000 (do Gunicorn)
EXPOSE 5000

# Comando de inicialização com Gunicorn
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000", "--worker-class", "gevent"]
