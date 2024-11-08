from tkinter import *
from pymongo import MongoClient
import customtkinter
import hashlib
import random
import string
import time

# Configurações iniciais para customtkinter
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

# Conexão com o MongoDB
client = MongoClient("mongodb+srv://root:123@cluster0.1oiip.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['banco_de_dados']
collection_usuario = db['Usuario']
collection_transacao = db['Transacao']  # Nome da coleção alterado para "Transacao"
collection_transacoes = db['Transacoes']  # Nome da coleção mantido como "Transacoes"
collection_cartao = db['Cartao']  # Nome da coleção mantido como "Cartao"

# Função para gerar o hash SHA-256
def gerar_hash(valor):
    return hashlib.sha256(valor.encode()).hexdigest()

# Função para gerar um token temporário
def gerar_token_temporario():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# Função para gerar código 2FA
def gerar_codigo_2fa():
    return ''.join(random.choices('0123456789', k=6))

# Função para realizar login com 2FA
def realizar_login():
    global email_usuario  # Definindo email_usuario como uma variável global
    email = email_entry.get().strip()
    senha = senha_entry.get().strip()       

    if login_usuario(email, senha):
        email_usuario = email  # Armazenando o email do usuário logado
        codigo_2fa = gerar_codigo_2fa()
        print(f"Código 2FA: {codigo_2fa}")

        # Criar uma janela para inserir o código 2FA
        def verificar_codigo_2fa():
            codigo_2fa_usuario = codigo_2fa_entry.get().strip()

            if codigo_2fa_usuario == codigo_2fa:
                mensagem_label.configure(text="Login bem-sucedido", text_color="#00FF00")
                abrir_tela_cartao()  # Abre a tela de cadastro de cartão após login bem-sucedido
                janela.withdraw()  # Fecha a janela de login
                codigo_2fa_window.destroy()  # Fecha a janela do código 2FA
            else:
                mensagem_label.configure(text="Código 2FA incorreto", text_color="#FF0000")

        # Janela para inserir o código 2FA
        codigo_2fa_window = Toplevel(janela)
        codigo_2fa_window.title("Digite o código 2FA")
        codigo_2fa_window.geometry("400x200")
        codigo_2fa_window.configure(bg="#1A1A2E")

        codigo_2fa_label = customtkinter.CTkLabel(codigo_2fa_window, text="Código 2FA", text_color="white")
        codigo_2fa_label.pack(pady=10)

        codigo_2fa_entry = customtkinter.CTkEntry(codigo_2fa_window, width=200, placeholder_text="Digite o código 2FA")
        codigo_2fa_entry.pack(pady=10)

        botao_verificar = customtkinter.CTkButton(codigo_2fa_window, text="Verificar Código",
                                                  command=verificar_codigo_2fa)
        botao_verificar.pack(pady=10)

    else:
        mensagem_label.configure(text="Login falhou", text_color="#FF0000")

# Função para login de usuário
def login_usuario(email, senha):
    try:
        if not email or not senha:
            return False

        email_hash = gerar_hash(email)
        senha_hash = gerar_hash(senha)

        usuario_encontrado = collection_usuario.find_one({'email': email_hash, 'senha': senha_hash})
        return usuario_encontrado is not None

    except Exception as erro:
        print(f"Erro ao realizar login: {erro}")
        return False

# Função para cadastrar usuário
def realizar_cadastro():
    email = email_entry.get().strip()
    senha = senha_entry.get().strip()

    if cadastrar_usuario(email, senha):
        mensagem_label.configure(text="Usuário cadastrado com sucesso", text_color="#00FF00")
    else:
        mensagem_label.configure(text="Erro ao cadastrar usuário", text_color="#FF0000")

# Função para cadastrar usuário
def cadastrar_usuario(email, senha):
    try:
        if len(senha) < 5 or not senha.isalnum():
            return False

        email_hash = gerar_hash(email)
        senha_hash = gerar_hash(senha)

        if collection_usuario.find_one({'email': email_hash}):
            return False

        usuario = {"email": email_hash, "senha": senha_hash}
        collection_usuario.insert_one(usuario)
        return True

    except Exception as erro:
        print(f"Erro ao cadastrar usuário: {erro}")
        return False

# Função para realizar uma transação com valor formatado em Real (R$)
def realizar_transacao(valor_entry, mensagem_label_transacao, email_usuario):
    valor = valor_entry.get().strip()
    if not valor:
        mensagem_label_transacao.configure(text="Por favor, insira o valor da transação.", text_color="#FF0000")
        return

    # Formatar valor em R$
    valor_formatado = f"R$ {float(valor):,.2f}"

    # Registrar a transação como realizada com sucesso
    token_temporario = gerar_token_temporario()
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    hash_transacao = gerar_hash(token_temporario + str(timestamp))

    # Usando SHA-256 para gerar os hashes dos dados
    valor_hash = gerar_hash(valor_formatado)

    # Inserir a transação no banco de dados
    collection_transacao.insert_one({
        "token": token_temporario,
        "hash_transacao": hash_transacao,
        "timestamp": timestamp,
        "valor": valor_formatado,  # Agora armazenando o valor já formatado em R$
        "status": "Pagamento realizado com sucesso",
        "usuario": email_usuario  # Guardando o email do usuário no banco
    })

    mensagem_label_transacao.configure(text="Pagamento realizado com sucesso!", text_color="#00FF00")

# Função para visualizar o histórico de transações
def visualizar_historico(tela_pagamento, email_usuario):
    # Gerar o hash do email para buscar as transações relacionadas ao usuário logado
    email_hash = gerar_hash(email_usuario)

    # Buscar o usuário no banco para garantir que ele existe
    usuario = collection_transacao.find_one({'usuario': email_usuario})

    if not usuario:
        print(f"Usuário com e-mail {email_usuario} não encontrado.")
        return

    # Obter as transações do banco de dados, filtrando pelo email_hash (usuário logado)
    historico = list(collection_transacao.find({"usuario": email_usuario}))
    print(historico)

    # Imprimir no console as transações recuperadas
    if len(historico) == 0:
        print(f"Nenhuma transação encontrada para o usuário com e-mail {email_usuario}")
    else:
        for transacao in historico:
            valor = transacao.get("valor", "Valor não encontrado")
            timestamp = transacao.get("timestamp", "Data não encontrada")
            status = transacao.get("status", "Status não encontrado")

            # Imprimindo detalhes da transação no console
            print(f"Transação: Valor = {valor}, Data = {timestamp}, Status = {status}")

    # Criar a janela de histórico, se desejado
    historico_janela = Toplevel(tela_pagamento)
    historico_janela.title("Histórico de Transações")
    historico_janela.geometry("600x400")
    historico_janela.configure(bg="#1A1A2E")

    titulo_historico_label = customtkinter.CTkLabel(historico_janela, text="Histórico de Transações",
                                                    font=("Arial", 16, "bold"),
                                                    text_color="#00FFFF", bg_color="#1A1A2E")
    titulo_historico_label.pack(pady=10)

    # Verifique se existe transações para mostrar na interface
    if len(historico) == 0:
        transacao_label = customtkinter.CTkLabel(historico_janela, text="Nenhuma transação realizada.",
                                                 text_color="white", bg_color="#1A1A2E")
        transacao_label.pack(pady=10)
    else:
        for transacao in historico:
            valor = transacao.get("valor", "Valor não encontrado")
            timestamp = transacao.get("timestamp", "Data não encontrada")
            status = transacao.get("status", "Status não encontrado")

            # Aqui, formatando a transação para ser exibida corretamente
            transacao_label = customtkinter.CTkLabel(historico_janela,
                                                     text=f"Valor: {valor} | Data: {timestamp} | Status: {status}",
                                                     text_color="white", bg_color="#1A1A2E")
            transacao_label.pack(pady=5)

    # Botão para fechar a janela de histórico
    botao_fechar = customtkinter.CTkButton(historico_janela, text="Fechar", command=historico_janela.destroy,
                                           fg_color="#1F4287", hover_color="#278EA5", corner_radius=10)
    botao_fechar.pack(pady=20)

# Função para cadastrar o cartão
def cadastrar_cartao(numero_cartao_entry, cvv_entry, mensagem_label_cartao, tela_cartao):
    numero_cartao = numero_cartao_entry.get().strip()
    cvv = cvv_entry.get().strip()

    if numero_cartao and cvv:
        numero_hash = gerar_hash(numero_cartao)
        cvv_hash = gerar_hash(cvv)

        if collection_cartao.find_one({'numero': numero_hash}):
            mensagem_label_cartao.configure(text="Cartão já cadastrado.", text_color="#FF0000")
        else:
            collection_cartao.insert_one({'numero': numero_hash, 'cvv': cvv_hash})
            mensagem_label_cartao.configure(text="Cartão cadastrado com sucesso.", text_color="#00FF00")
            abrir_tela_pagamento(tela_cartao)  # Abre a tela de pagamento após cadastrar o cartão
    else:
        mensagem_label_cartao.configure(text="Preencha todos os campos.", text_color="#FF0000")

# Função para abrir a tela de pagamento
def abrir_tela_pagamento(tela_cartao):
    tela_pagamento = Toplevel(tela_cartao)
    tela_pagamento.title("Tela de Pagamento")
    tela_pagamento.geometry("600x400")
    tela_pagamento.configure(bg="#1A1A2E")

    titulo_pagamento_label = Label(tela_pagamento, text="Realizar Pagamento", font=("Arial", 16, "bold"),
                                   fg="#00FFFF", bg="#1A1A2E")
    titulo_pagamento_label.pack(pady=10)

    valor_entry = customtkinter.CTkEntry(tela_pagamento, width=300, placeholder_text="Valor da transação")
    valor_entry.pack(pady=10)

    botao_pagamento = customtkinter.CTkButton(tela_pagamento, text="Realizar Pagamento",
                                              command=lambda: realizar_transacao(valor_entry, mensagem_label_transacao, email_usuario),
                                              fg_color="#1F4287", hover_color="#278EA5", corner_radius=10)
    botao_pagamento.pack(pady=20)

    mensagem_label_transacao = customtkinter.CTkLabel(tela_pagamento, text="", text_color="white")
    mensagem_label_transacao.pack(pady=20)

    botao_historico = customtkinter.CTkButton(tela_pagamento, text="Visualizar Histórico",
                                              command=lambda: visualizar_historico(tela_pagamento, email_usuario),
                                              fg_color="#1F4287", hover_color="#278EA5", corner_radius=10)
    botao_historico.pack(pady=20)

# Função para abrir a tela de cadastro do cartão
def abrir_tela_cartao():
    tela_cartao = customtkinter.CTk()
    tela_cartao.title("Cadastro de Cartão")
    tela_cartao.geometry("600x400")
    tela_cartao.configure(bg="#1A1A2E")

    titulo_cartao_label = customtkinter.CTkLabel(tela_cartao, text="Cadastro de Cartão", font=("Arial", 16, "bold"), text_color="#00FFFF", bg_color="#1A1A2E")
    titulo_cartao_label.pack(pady=10)

    numero_cartao_label = customtkinter.CTkLabel(tela_cartao, text="Número do Cartão", text_color="white")
    numero_cartao_label.pack(pady=5)
    numero_cartao_entry = customtkinter.CTkEntry(tela_cartao, width=300, placeholder_text="Número do Cartão")
    numero_cartao_entry.pack(pady=10)

    cvv_label = customtkinter.CTkLabel(tela_cartao, text="CVV", text_color="white")
    cvv_label.pack(pady=5)
    cvv_entry = customtkinter.CTkEntry(tela_cartao, width=300, placeholder_text="CVV", show="*")
    cvv_entry.pack(pady=10)

    mensagem_label_cartao = customtkinter.CTkLabel(tela_cartao, text="", text_color="white")
    mensagem_label_cartao.pack(pady=20)

    botao_cartao = customtkinter.CTkButton(tela_cartao, text="Cadastrar Cartão",
                                           command=lambda: cadastrar_cartao(numero_cartao_entry, cvv_entry,
                                                                            mensagem_label_cartao, tela_cartao),
                                           fg_color="#1F4287", hover_color="#278EA5", corner_radius=10)
    botao_cartao.pack(pady=20)

    tela_cartao.mainloop()

# Janela principal (login)
janela = customtkinter.CTk()
janela.title("Sistema de Pagamentos Seguros com Criptografia Ponta a Ponta")
janela.geometry("700x500")
janela.configure(bg="#1A1A2E")

titulo_label = customtkinter.CTkLabel(janela, text="Pagamentos Seguros com Criptografia Ponta a Ponta",
                                      font=("Arial", 24, "bold"), text_color="#00FFFF")
titulo_label.pack(pady=20)

email_label = customtkinter.CTkLabel(janela, text="Digite seu email", text_color="white")
email_label.pack(pady=5)
email_entry = customtkinter.CTkEntry(janela, width=300, placeholder_text="Email")
email_entry.pack(pady=10)

senha_label = customtkinter.CTkLabel(janela, text="Digite sua senha", text_color="white")
senha_label.pack(pady=5)
senha_entry = customtkinter.CTkEntry(janela, width=300, placeholder_text="Senha", show="*")
senha_entry.pack(pady=10)

login_button = customtkinter.CTkButton(janela, text="Login", command=realizar_login, fg_color="#1F4287",
                                       hover_color="#278EA5", corner_radius=10)
login_button.pack(pady=10)

cadastro_button = customtkinter.CTkButton(janela, text="Cadastro", command=realizar_cadastro, fg_color="#1F4287",
                                          hover_color="#278EA5", corner_radius=10)
cadastro_button.pack(pady=10)

mensagem_label = customtkinter.CTkLabel(janela, text="", text_color="white")
mensagem_label.pack(pady=20)

janela.mainloop()