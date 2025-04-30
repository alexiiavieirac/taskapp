# Usa imagem base do Python
FROM python:3.11-slim

# Instala dependências do sistema (necessárias para mysqlclient)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    libpq-dev

# Cria diretório de trabalho no container
WORKDIR /app

# Copia o arquivo requirements.txt
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do projeto
COPY . .

# Define o comando para iniciar a aplicação
CMD ["python", "app.py"]
