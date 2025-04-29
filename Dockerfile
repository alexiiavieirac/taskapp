# Usar uma imagem base do Python
FROM python:3.9-slim

# Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar os arquivos do projeto para o contêiner
COPY . /app

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expor a porta do app (ajuste conforme sua necessidade)
EXPOSE 5000

# Rodar o aplicativo
CMD ["python", "app.py"]
