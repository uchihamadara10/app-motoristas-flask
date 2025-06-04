# Use a imagem oficial do Python como base
FROM python:3.9-slim-buster

# Define o diretório de trabalho dentro do contêiner como /app
WORKDIR /app

# Copia o arquivo requirements.txt da raiz do seu repositório para /app no contêiner
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação (que está em app/) para /app no contêiner
# Isso copiará o conteúdo de "app/" do seu repositório para o WORKDIR /app
COPY app/. .

# Define a variável de ambiente para a porta que o Cloud Run vai expor
# O Cloud Run define a porta em tempo de execução via a variável PORT
ENV PORT 8080

# Comando para executar o aplicativo Flask usando Gunicorn
# 'app:app' agora se refere ao arquivo 'app.py' e à instância 'app' dentro da pasta '/app' no contêiner
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]