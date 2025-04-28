# Usar a imagem oficial do Python
FROM python:3.11-slim-bullseye

# Definir diretório de trabalho
WORKDIR /app

# Copiar o conteúdo da sua aplicação para dentro do container
COPY . .

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expor a porta que o Flask vai usar
EXPOSE 5000

# Comando para rodar o app
CMD ["python", "app.py"]