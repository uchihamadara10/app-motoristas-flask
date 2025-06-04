import json
from flask import Flask, request, render_template_string, redirect
from datetime import datetime
import pytz
import math
import firebase_admin
from firebase_admin import credentials, firestore
import os
import re # Importar módulo de expressões regulares

# Inicialização do Firebase
if not firebase_admin._apps:
    try:
        # Tenta carregar as credenciais da variável de ambiente
        service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY')
        if service_account_json:
            cred_dict = json.loads(service_account_json)
            cred = credentials.Certificate(cred_dict)
        else:
            # Fallback para o arquivo local para desenvolvimento (OPCIONAL, mas útil para testes locais)
            # Remova/comente esta parte se você quiser FORÇAR o uso da variável de ambiente em qualquer lugar
            if os.path.exists("serviceAccountKey.json"):
                cred = credentials.Certificate("serviceAccountKey.json")
            else:
                print("ERRO: Variável de ambiente 'FIREBASE_SERVICE_ACCOUNT_KEY' ou arquivo 'serviceAccountKey.json' não encontrado.")
                print("Por favor, configure a variável de ambiente no Cloud Run.")
                exit(1)

        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"ERRO: Falha ao inicializar o Firebase. Verifique as credenciais. Detalhes: {e}")
        exit(1)

app = Flask(__name__)

# Função para calcular distância
def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371000 # Raio da Terra em metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Controle de Motoristas</title>
        <style>
            body {
                margin: 0; padding: 0;
                background-image: url('https://th.bing.com/th/id/R.187389868a8f8afba4822c152da9f40e?rik=w1Cy2wzxOuD6%2bQ&pid=ImgRaw&r=0');
                background-size: cover; background-position: center;
                height: 100vh; display: flex; justify-content: center; align-items: center;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: white;
                overflow: hidden; /* Evita scroll desnecessário */
            }
            .content {
                background: rgba(0, 0, 0, 0.8); /* Fundo mais escuro para melhor contraste */
                padding: 40px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4); /* Sombra para profundidade */
                animation: slideIn 0.8s ease-out; /* Animação de entrada */
            }
            @keyframes slideIn {
                from { opacity: 0; transform: translateY(50px); }
                to { opacity: 1; transform: translateY(0); }
            }
            h1 {
                font-size: 2.8em;
                margin-bottom: 15px;
                color: #FFD700; /* Dourado */
            }
            p {
                font-size: 1.1em;
                margin-bottom: 30px;
            }
            button {
                padding: 15px 35px;
                background-color: #FFA500; /* Laranja vibrante */
                color: #333; /* Texto escuro */
                font-size: 1.3em;
                font-weight: bold;
                border: none;
                border-radius: 30px;
                cursor: pointer;
                transition: transform 0.3s ease, background-color 0.3s ease; /* Transição suave */
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            }
            button:hover {
                transform: scale(1.05); /* Leve aumento no hover */
                background-color: #FF8C00; /* Laranja mais escuro */
            }
            #mensagem {
                color: #FF6347; /* Tomate */
                margin-top: 20px;
                font-weight: bold;
                font-size: 1.1em;
            }
        </style>
    </head>
    <body>
        <div class="content">
            <h1>Controle de Motoristas</h1>
            <p>Registre a entrada ou saída da frota de forma rápida e segura.</p>
            <button onclick="verificarLocalizacao()">Clique aqui para iniciar</button>
            <p id="mensagem"></p>
        </div>
        <script>
            function verificarLocalizacao() {
                document.getElementById('mensagem').innerText = "Obtendo sua localização...";
                if (!navigator.geolocation) {
                    document.getElementById('mensagem').innerText = "Seu navegador não suporta geolocalização. Por favor, utilize um navegador moderno.";
                    return;
                }

                navigator.geolocation.getCurrentPosition(function(pos) {
                    const userLat = pos.coords.latitude;
                    const userLon = pos.coords.longitude;

                    // Coordenadas de referência (atualizadas para Itapevi/SP, conforme sua localização)
                    // Você pode ajustar essas coordenadas para o ponto exato da sua portaria/local de controle.
                    const refLat = -23.516185; 
                    const refLon = -46.965741; 

                    const R = 6371000; // Raio da Terra em metros
                    const toRad = angle => angle * Math.PI / 180;

                    const dLat = toRad(refLat - userLat);
                    const dLon = toRad(refLon - userLon);
                    const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(userLat)) * Math.cos(toRad(refLat)) * Math.sin(dLon / 2) ** 2;
                    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
                    const distancia = R * c;

                    const raioPermitido = 300; // Distância em metros (200m de raio)

                    if (distancia <= raioPermitido) {
                        window.location.href = "/pergunta";
                    } else {
                        document.getElementById('mensagem').innerText = "Você está fora da área permitida. Distância: " + distancia.toFixed(0) + " metros.";
                    }
                }, function(error) {
                    let errorMessage = "Erro ao obter localização.";
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            errorMessage += " Permissão negada. Ative a localização nas configurações do seu navegador.";
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMessage += " Localização indisponível. Tente novamente mais tarde.";
                            break;
                        case error.TIMEOUT:
                            errorMessage += " Tempo limite excedido. Verifique sua conexão ou tente novamente.";
                            break;
                        case error.UNKNOWN_ERROR:
                            errorMessage += " Erro desconhecido. Por favor, tente novamente.";
                            break;
                    }
                    document.getElementById('mensagem').innerText = errorMessage;
                }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }); // Opções para melhor precisão
            }
        </script>
    </body>
    </html>
    '''

@app.route('/pergunta')
def pergunta():
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Você está entrando ou saindo?</title>
        <style>
            body {
                background-color: #1c1c1c; color: white;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex;
                justify-content: center; align-items: center;
                height: 100vh; flex-direction: column;
                animation: fadeIn 1s ease-out;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            h1 {
                font-size: 2.5em;
                margin-bottom: 40px;
                color: #ADD8E6; /* Azul claro */
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }
            .button-container {
                display: flex;
                gap: 20px; /* Espaço entre os botões */
            }
            a {
                background-color: #FFA500; /* Laranja */
                color: #333;
                padding: 15px 40px;
                margin: 10px 0; /* Ajustado para flexbox */
                font-size: 1.2em;
                font-weight: bold;
                border-radius: 30px;
                text-decoration: none;
                transition: transform 0.3s ease, background-color 0.3s ease;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            }
            a:hover {
                transform: scale(1.05);
                background-color: #FF8C00;
            }
        </style>
    </head>
    <body>
        <h1>Qual o tipo de registro?</h1>
        <div class="button-container">
            <a href="/registrar?tipo=Entrada">Entrada</a>
            <a href="/registrar?tipo=Saída">Saída</a>
        </div>
    </body>
    </html>
    '''

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    tipo_predefinido = request.args.get('tipo', '')
    
    mensagem_erro = "" # Para exibir mensagens de erro no formulário
    # Variáveis para manter os valores preenchidos em caso de erro
    nome_valor = ""
    placa_valor = ""
    ordem_valor = ""
    transportadora_valor = ""
    quilometragem_valor = ""

    if request.method == 'POST':
        nome = request.form['nome'].upper().strip()
        placa_raw = request.form['placa']
        ordem_raw = request.form['ordem']
        tipo = request.form['tipo']
        transportadora = request.form['Transportadora'].upper().strip()
        quilometragem = request.form.get('quilometragem', '').strip() # Campo opcional

        # --- Validações e Normalizações no Servidor (Python) ---
        
        # Placa: remover espaços e pontuações, converter para maiúsculas
        placa = re.sub(r'[^A-Z0-9]', '', placa_raw.upper()) # Remove tudo que não for letra maiúscula ou número
        
        # Ordem de Coleta: remover espaços, obrigatório, converter para maiúsculas
        ordem = ordem_raw.strip().upper() # Remove espaços no início/fim e converte para maiúsculas
        ordem = re.sub(r'\s+', '', ordem) # Remove múltiplos espaços no meio (se houver)

        # Reatribui os valores para o formulário em caso de re-renderização
        nome_valor = nome
        placa_valor = placa_raw
        ordem_valor = ordem_raw
        transportadora_valor = transportadora
        quilometragem_valor = quilometragem

        if not nome:
            mensagem_erro = "O Nome do Motorista é obrigatório."
        elif not placa:
            mensagem_erro = "A Placa do Veículo é obrigatória e não pode estar vazia."
        elif not ordem:
            mensagem_erro = "A Ordem de Coleta é obrigatória e não pode estar vazia."
        elif not transportadora:
            mensagem_erro = "A Transportadora é obrigatória."
        
        # Validação de quilometragem (se preenchida, deve ser um número inteiro positivo)
        if not mensagem_erro and quilometragem: # Só valida se não houver erro anterior
            try:
                quilometragem_int = int(quilometragem)
                if quilometragem_int < 0:
                    mensagem_erro = "A quilometragem deve ser um número positivo."
            except ValueError:
                mensagem_erro = "A quilometragem deve ser um número válido (apenas números inteiros)."

        if mensagem_erro:
            # Se houver erro, renderiza o formulário novamente com a mensagem
            return render_template_string(template_registro_html, 
                                        tipo=tipo_predefinido, 
                                        nome_valor=nome_valor, 
                                        placa_valor=placa_valor, 
                                        ordem_valor=ordem_valor, 
                                        transportadora_valor=transportadora_valor,
                                        quilometragem_valor=quilometragem_valor, 
                                        mensagem_erro=mensagem_erro)

        horario = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            db_firestore = firestore.client()
            registros_ref = db_firestore.collection('registros')
            novo_registro = {
                'nome': nome,
                'placa': placa, # Placa normalizada
                'ordem': ordem, # Ordem normalizada
                'tipo': tipo,
                'horario': horario,
                'Transportadora': transportadora
            }
            # Adiciona a quilometragem se ela foi preenchida e é válida
            if quilometragem and not mensagem_erro: # Verifica se não houve erro na validação da quilometragem
                novo_registro['quilometragem'] = int(quilometragem)

            registros_ref.add(novo_registro)

            return '''
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="refresh" content="2;url=/" />
                <title>Sucesso!</title>
                <style>
                    body {
                        background-color: #1e1e1e; color: white;
                        display: flex; justify-content: center; align-items: center; height: 100vh;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    }
                    div {
                        text-align: center; background-color: #333; padding: 30px; border-radius: 10px;
                        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
                    }
                    h2 { color: lime; font-size: 2em; margin-bottom: 10px; }
                    p { font-size: 1.1em; }
                </style>
            </head>
            <body>
                <div>
                    <h2>✅ Registro salvo com sucesso!</h2>
                    <p>Você será redirecionado em instantes...</p>
                </div>
            </body>
            </html>
            '''
        except Exception as e:
            # Em caso de erro no Firestore, exibe a mensagem de erro no formulário
            mensagem_erro = f"Erro ao salvar no Firestore: {e}. Por favor, tente novamente."
            return render_template_string(template_registro_html, 
                                        tipo=tipo_predefinido, 
                                        nome_valor=nome_valor, 
                                        placa_valor=placa_valor, 
                                        ordem_valor=ordem_valor, 
                                        transportadora_valor=transportadora_valor,
                                        quilometragem_valor=quilometragem_valor,
                                        mensagem_erro=mensagem_erro)

    # --- HTML do Formulário (GET request ou POST com erro) ---
    template_registro_html = '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Registro</title>
        <style>
            body { 
                background-color: #2c1e1e; color: white; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; 
                text-align: center; display: flex; justify-content: center; align-items: center; 
                min-height: 100vh; margin: 0;
            }
            .form-box {
                background-color: #fff8f0; color: black; padding: 30px;
                border-radius: 12px; max-width: 500px; width: 90%; margin: auto;
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
                animation: fadeIn 0.8s ease-out;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: scale(0.9); }
                to { opacity: 1; transform: scale(1); }
            }
            h2 { 
                color: #8B4513; margin-bottom: 30px; 
                font-size: 2.2em; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
            }
            label { 
                font-weight: bold; display: block; margin-top: 20px; text-align: left; 
                color: #5a2e0e; /* Marrom mais escuro */
            }
            input[type="text"], input[type="number"], select { 
                width: calc(100% - 22px); /* Ajusta para padding */
                padding: 11px; border-radius: 6px; margin-top: 8px;
                border: 1px solid #ccc; font-size: 1em;
                box-sizing: border-box; /* Inclui padding na largura */
            }
            input[type="submit"] {
                background-color: #8B4513; color: white; border: none; cursor: pointer; margin-top: 30px;
                padding: 15px 30px; border-radius: 30px; font-size: 1.1em; font-weight: bold;
                transition: background-color 0.3s ease, transform 0.3s ease;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            }
            input[type="submit"]:hover { 
                background-color: #a0522d; 
                transform: translateY(-2px); /* Efeito de elevação */
            }
            .error-message { 
                color: #D32F2F; /* Vermelho mais forte */
                background-color: #FFCDD2; /* Fundo vermelho claro */
                border: 1px solid #EF9A9A;
                padding: 10px; border-radius: 5px;
                margin-top: 15px; font-weight: bold;
            }
            .info-message { 
                color: #616161; font-size: 0.85em; margin-top: 5px; text-align: left; 
            }
            select {
                background-color: #f0f0f0;
            }
        </style>
    </head>
    <body>
        <div class="form-box">
            <h2>📋 Registro de {{ tipo }}</h2>
            {% if mensagem_erro %}
                <p class="error-message">{{ mensagem_erro }}</p>
            {% endif %}
            <form method="post" onsubmit="return validarFormulario()">
                <label for="nome">Nome do Motorista:</label>
                <input type="text" name="nome" id="nome" value="{{ nome_valor }}" required>
                
                <label for="placa">Placa do Veículo:</label>
                <input type="text" name="placa" id="placa" value="{{ placa_valor }}" required>
                <p class="info-message">⚠️ Se for carreta, utilize a placa do Baú / Carreta. A placa será salva sem espaços e pontuações (ex: ABC1234).</p>
                
                <label for="ordem">Ordem de Coleta:</label>
                <input type="text" name="ordem" id="ordem" value="{{ ordem_valor }}" required>
                <p class="info-message">⚠️ Campo obrigatório. A ordem será salva sem espaços (ex: ORDEM123).</p>
                
                <label for="Transportadora">Transportadora:</label>
                <input type="text" name="Transportadora" id="Transportadora" value="{{ transportadora_valor }}" required>

                <label for="quilometragem">Informe a Quilometragem (Opcional):</label>
                <input type="number" name="quilometragem" id="quilometragem" value="{{ quilometragem_valor }}" placeholder="Ex: 123456" min="0">
                <p class="info-message">Campo opcional para controle da frota. Apenas números inteiros.</p>
                
                <label for="tipo">Tipo:</label>
                <select name="tipo" id="tipo">
                    <option value="Entrada" {% if tipo == "Entrada" %}selected{% endif %}>Entrada</option>
                    <option value="Saída" {% if tipo == "Saída" %}selected{% endif %}>Saída</option>
                </select>
                <input type="submit" value="Registrar">
            </form>
        </div>

        <script>
            function validarFormulario() {
                let nomeInput = document.getElementById('nome');
                let placaInput = document.getElementById('placa');
                let ordemInput = document.getElementById('ordem');
                let transportadoraInput = document.getElementById('Transportadora');
                let quilometragemInput = document.getElementById('quilometragem');
                let errorMessageDiv = document.querySelector('.error-message');

                // Se não existir, cria e insere a div de erro
                if (!errorMessageDiv) {
                    errorMessageDiv = document.createElement('p');
                    errorMessageDiv.className = 'error-message';
                    document.querySelector('.form-box form').prepend(errorMessageDiv);
                }
                errorMessageDiv.textContent = ''; // Limpa a mensagem de erro anterior

                // Validações de campos obrigatórios
                if (nomeInput.value.trim() === '') {
                    errorMessageDiv.textContent = 'O Nome do Motorista é obrigatório.';
                    nomeInput.focus();
                    return false;
                }

                // Remove espaços e pontuações da placa ANTES de validar no cliente
                placaInput.value = placaInput.value.replace(/[^A-Za-z0-9]/g, '').toUpperCase();
                if (placaInput.value === '') {
                    errorMessageDiv.textContent = 'A Placa do Veículo é obrigatória.';
                    placaInput.focus();
                    return false;
                }
                
                // Remove espaços da ordem ANTES de validar no cliente
                ordemInput.value = ordemInput.value.trim().toUpperCase().replace(/\s+/g, '');
                if (ordemInput.value === '') {
                    errorMessageDiv.textContent = 'A Ordem de Coleta é obrigatória.';
                    ordemInput.focus();
                    return false;
                }

                if (transportadoraInput.value.trim() === '') {
                    errorMessageDiv.textContent = 'A Transportadora é obrigatória.';
                    transportadoraInput.focus();
                    return false;
                }

                // Validação de quilometragem no cliente (opcional, mas boa prática)
                if (quilometragemInput.value !== '') {
                    let quilometragem = parseInt(quilometragemInput.value);
                    if (isNaN(quilometragem) || quilometragem < 0) {
                        errorMessageDiv.textContent = 'A quilometragem deve ser um número inteiro positivo válido.';
                        quilometragemInput.focus();
                        return false;
                    }
                }
                
                return true; // Se tudo estiver OK, envia o formulário
            }
        </script>
    </body>
    </html>
    '''
    # Passa valores vazios para os campos no primeiro carregamento (GET request)
    return render_template_string(template_registro_html, 
                                tipo=tipo_predefinido, 
                                nome_valor="", 
                                placa_valor="", 
                                ordem_valor="", 
                                transportadora_valor="",
                                quilometragem_valor="",
                                mensagem_erro=mensagem_erro) 

if __name__ == '__main__':
    # Usar porta 8080 que é comum para aplicações web ou outra que preferir
    app.run(host='0.0.0.0', port=8080, debug=True) # debug=True para desenvolvimento