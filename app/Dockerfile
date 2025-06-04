# Use a imagem oficial do Python como base
FROM python:3.9-slim-buster

# Define o diretório de trabalho dentro do contêiner como /app
# E O Cloud Build VAI PARA /workspace/app/
WORKDIR /app

# Copia o arquivo requirements.txt da pasta 'app/' no seu repositório para a raiz do WORKDIR (/app) no contêiner
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação da pasta 'app/' para a raiz do WORKDIR (/app) no contêiner
COPY app/. .

# Define a variável de ambiente para a porta que o Cloud Run vai expor
# O Cloud Run define a porta em tempo de execução via a variável PORT
ENV PORT 8080

# Comando para executar o aplicativo Flask usando Gunicorn
# 'app:app' agora se refere ao arquivo 'app.py' e à instância 'app' dentro da pasta '/app' no contêiner
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]