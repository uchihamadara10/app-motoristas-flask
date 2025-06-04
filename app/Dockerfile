# Use a imagem oficial do Python como base
FROM python:3.9-slim-buster

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo requirements.txt para o contêiner e instala as dependências
# A ordem é importante para aproveitar o cache do Docker (se requirements.txt não mudar)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação para o contêiner
COPY . .

# Define a variável de ambiente para a porta que o Cloud Run vai expor
# O Cloud Run define a porta em tempo de execução via a variável PORT
ENV PORT 8080

# Comando para executar o aplicativo Flask usando Gunicorn
# Gunicorn é um servidor WSGI leve e rápido, ideal para produção com Flask
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]