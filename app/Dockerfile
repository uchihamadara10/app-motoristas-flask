# Use uma imagem base oficial do Python
FROM python:3.9-slim-buster

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo requirements.txt para o contêiner
COPY requirements.txt .

# Instala as dependências listadas no requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação para o contêiner
COPY . .

# Expõe a porta que o Gunicorn vai usar. O Cloud Run injeta a variável PORT.
ENV PORT 8080
EXPOSE $PORT

# Comando para iniciar o Gunicorn, que serve sua aplicação Flask
# Onde "app:app" significa: "app.py" (seu arquivo) e "app" (sua instância Flask)
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8080", "app:app"]