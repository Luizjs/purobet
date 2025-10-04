# -*- coding: utf-8 -*-

# ===================================================================================
# PROJETO PUROBET - CASSINO FICTÍCIO
# Versão Final: Com Banco de Dados, Logs, Interface Gráfica Completa e Comentários.
#
# Pré-requisitos para executar:
# 1. Python instalado.
# 2. Instalar as bibliotecas necessárias:
#    pip install customtkinter Pillow
#
# Estrutura de Pastas:
# - /pasta_do_projeto/
#   |- main.py (este arquivo)
#   |- purobet.db (será criado automaticamente)
#   |- /cards/
# ===================================================================================

import customtkinter as ctk
import random
import string
import math
import time
import sqlite3
import hashlib
from datetime import datetime
from tkinter import Canvas
from PIL import Image, ImageTk
import os

# Define o nome do arquivo do banco de dados. Ele será criado na mesma pasta do script.
ARQUIVO_BD = "purobet.db"

def inicializar_banco_de_dados():
    """
    Inicializa o banco de dados, criando o arquivo .db e as tabelas caso não existam.
    Esta função é chamada uma única vez quando o programa inicia.
    """
    conexao = sqlite3.connect(ARQUIVO_BD)
    cursor = conexao.cursor()

    # Cria a tabela 'usuarios' para armazenar informações dos jogadores.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_usuario TEXT UNIQUE NOT NULL,
            hash_senha TEXT NOT NULL,
            saldo REAL NOT NULL,
            codigo_referencia TEXT UNIQUE NOT NULL
        )
    ''')

    # Cria a tabela 'configuracoes_jogo' para armazenar configurações ajustáveis pelo admin.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracoes_jogo (
            nome_configuracao TEXT PRIMARY KEY,
            valor REAL NOT NULL
        )
    ''')

    # Cria a tabela 'logs_apostas' para registrar cada aposta feita.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs_apostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_usuario TEXT NOT NULL,
            jogo TEXT NOT NULL,
            valor_aposta REAL NOT NULL,
            resultado REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')

    # Cria a tabela 'logs_transacoes' para registrar depósitos e outras transações.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs_transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_usuario TEXT NOT NULL,
            tipo_transacao TEXT NOT NULL,
            quantia REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')

    # Insere uma configuração padrão para a roleta, caso ainda não exista.
    cursor.execute("INSERT OR IGNORE INTO configuracoes_jogo (nome_configuracao, valor) VALUES (?, ?)", ('pagamento_roleta_numero', 35))

    conexao.commit()
    conexao.close()

# --- Funções de Log ---

def registrar_aposta(nome_usuario, jogo, valor_aposta, ganhos):
    """Registra uma aposta no banco de dados, na tabela 'logs_apostas'."""
    conexao = sqlite3.connect(ARQUIVO_BD)
    cursor = conexao.cursor()
    resultado = ganhos - valor_aposta
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO logs_apostas (nome_usuario, jogo, valor_aposta, resultado, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (nome_usuario, jogo, valor_aposta, resultado, timestamp))
    conexao.commit()
    conexao.close()

def registrar_transacao(nome_usuario, tipo_transacao, quantia):
    """Registra uma transação financeira na tabela 'logs_transacoes'."""
    conexao = sqlite3.connect(ARQUIVO_BD)
    cursor = conexao.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO logs_transacoes (nome_usuario, tipo_transacao, quantia, timestamp) VALUES (?, ?, ?, ?)",
                   (nome_usuario, tipo_transacao, quantia, timestamp))
    conexao.commit()
    conexao.close()

# --- Funções de Usuário e Autenticação ---

def gerar_hash_senha(senha):
    """Gera um hash SHA-256 para uma senha."""
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_senha(hash_armazenado, senha_fornecida):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return hash_armazenado == gerar_hash_senha(senha_fornecida)

def adicionar_usuario(nome_usuario, senha, saldo, codigo_referencia):
    """Adiciona um novo usuário ao banco de dados."""
    conexao = sqlite3.connect(ARQUIVO_BD)
    cursor = conexao.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (nome_usuario, hash_senha, saldo, codigo_referencia) VALUES (?, ?, ?, ?)",
                       (nome_usuario, gerar_hash_senha(senha), saldo, codigo_referencia))
        conexao.commit()
        registrar_transacao(nome_usuario, 'deposito_inicial', saldo)
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conexao.close()

def autenticar_usuario(nome_usuario, senha):
    """Autentica um usuário, verificando nome e senha."""
    conexao = sqlite3.connect(ARQUIVO_BD)
    cursor = conexao.cursor()
    cursor.execute("SELECT hash_senha FROM usuarios WHERE nome_usuario = ?", (nome_usuario,))
    resultado = cursor.fetchone()
    conexao.close()
    return bool(resultado and verificar_senha(resultado[0], senha))

def obter_dados_usuario(nome_usuario):
    """Busca e retorna os dados de um usuário."""
    conexao = sqlite3.connect(ARQUIVO_BD)
    cursor = conexao.cursor()
    cursor.execute("SELECT saldo, codigo_referencia FROM usuarios WHERE nome_usuario = ?", (nome_usuario,))
    resultado = cursor.fetchone()
    conexao.close()
    return {'saldo': resultado[0], 'codigo_referencia': resultado[1]} if resultado else None

def atualizar_saldo(nome_usuario, mudanca_quantia):
    """Atualiza o saldo de um usuário."""
    conexao = sqlite3.connect(ARQUIVO_BD)
    cursor = conexao.cursor()
    cursor.execute("UPDATE usuarios SET saldo = saldo + ? WHERE nome_usuario = ?", (mudanca_quantia, nome_usuario))
    conexao.commit()
    conexao.close()

def obter_todos_usuarios():
    """Retorna uma lista de todos os usuários e seus saldos."""
    conexao = sqlite3.connect(ARQUIVO_BD)
    cursor = conexao.cursor()
    cursor.execute("SELECT nome_usuario, saldo FROM usuarios")
    usuarios = cursor.fetchall()
    conexao.close()
    return usuarios

def deletar_usuario_bd(nome_usuario):
    """Deleta um usuário do banco de dados."""
    conexao = sqlite3.connect(ARQUIVO_BD)
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM usuarios WHERE nome_usuario = ?", (nome_usuario,))
    conexao.commit()
    conexao.close()

def encontrar_usuario_por_referencia(codigo_ref):
    """Encontra o nome de um usuário a partir do seu código de referência."""
    conexao = sqlite3.connect(ARQUIVO_BD)
    cursor = conexao.cursor()
    cursor.execute("SELECT nome_usuario FROM usuarios WHERE codigo_referencia = ?", (codigo_ref,))
    resultado = cursor.fetchone()
    conexao.close()
    return resultado[0] if resultado else None

# --- Funções de Configurações e Logs para Admin ---

def obter_configuracao_jogo(nome_configuracao):
    """Busca uma configuração de jogo no banco de dados."""
    conexao = sqlite3.connect(ARQUIVO_BD)
    cursor = conexao.cursor()
    cursor.execute("SELECT valor FROM configuracoes_jogo WHERE nome_configuracao = ?", (nome_configuracao,))
    resultado = cursor.fetchone()
    conexao.close()
    return resultado[0] if resultado else None

def definir_configuracao_jogo(nome_configuracao, valor):
    """Atualiza uma configuração de jogo no banco de dados."""
    conexao = sqlite3.connect(ARQUIVO_BD)
    cursor = conexao.cursor()
    cursor.execute("UPDATE configuracoes_jogo SET valor = ? WHERE nome_configuracao = ?", (valor, nome_configuracao))
    conexao.commit()
    conexao.close()

def obter_logs(tipo_log='logs_apostas', filtro_usuario=None):
    """Busca logs, com um filtro opcional por usuário."""
    conexao = sqlite3.connect(ARQUIVO_BD)
    cursor = conexao.cursor()
    consulta = f"SELECT * FROM {tipo_log}"
    parametros = []
    if filtro_usuario:
        consulta += " WHERE nome_usuario LIKE ?"
        parametros.append(f"%{filtro_usuario}%")
    consulta += " ORDER BY timestamp DESC LIMIT 100"
    cursor.execute(consulta, parametros)
    logs = cursor.fetchall()
    conexao.close()
    return logs

# --- SEÇÃO 2: CARREGADOR DE IMAGENS E WIDGETS CUSTOMIZADOS ---

class CarregadorImagens:
    """
    Classe Singleton para carregar e armazenar em cache as imagens, otimizando a performance.
    """
    _instancia = None
    def __new__(cls, *args, **kwargs):
        if not cls._instancia:
            cls._instancia = super(CarregadorImagens, cls).__new__(cls)
            cls._instancia.cache_ctk = {}
            cls._instancia.cache_photo = {}
        return cls._instancia

    def obter_imagem_ctk(self, nome_carta="back"):
        """Retorna uma imagem no formato CTkImage."""
        if nome_carta in self.cache_ctk:
            return self.cache_ctk[nome_carta]

        mapa_ranks = {'A': 'ace', 'K': 'king', 'Q': 'queen', 'J': 'jack', 'T': '10'}

        if nome_carta == "back":
            caminho_arquivo = os.path.join("cards", "back.png")
        else:
            naipe, rank = nome_carta.split('_')
            rank_str = mapa_ranks.get(rank, rank)
            nome_arquivo = f"{rank_str}_of_{naipe}.png"
            caminho_arquivo = os.path.join("cards", nome_arquivo)

        try:
            imagem = Image.open(caminho_arquivo)
            imagem = imagem.resize((70, 100), Image.LANCZOS)
            imagem_ctk = ctk.CTkImage(light_image=imagem, dark_image=imagem, size=(70, 100))
            self.cache_ctk[nome_carta] = imagem_ctk
            return imagem_ctk
        except FileNotFoundError:
            print(f"ERRO: Imagem não encontrada em {caminho_arquivo}.")
            return None

    def obter_imagem_photo(self, nome, tamanho=(80, 50)):
        """Retorna uma imagem no formato PhotoImage, para uso no Canvas."""
        if nome in self.cache_photo:
            return self.cache_photo[nome]

        caminho_arquivo = os.path.join("cards", f"{nome}.png")
        try:
            imagem = Image.open(caminho_arquivo).resize(tamanho, Image.LANCZOS)
            imagem_photo = ImageTk.PhotoImage(imagem)
            self.cache_photo[nome] = imagem_photo
            return imagem_photo
        except FileNotFoundError:
            print(f"ERRO: Imagem '{nome}.png' não encontrada.")
            return None

class CaixaMensagem(ctk.CTkToplevel):
    """Janela de mensagem customizada."""
    def __init__(self, parent, titulo="Mensagem", mensagem=""):
        super().__init__(parent)
        self.title(titulo)
        self.geometry("350x150")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        ctk.CTkLabel(self, text=mensagem, wraplength=320, font=ctk.CTkFont(size=14)).pack(pady=20, padx=15, expand=True, fill="both")
        ctk.CTkButton(self, text="OK", command=self.destroy, width=100).pack(pady=10)
        self.after(100, self.lift)

class CaixaDialogo(ctk.CTkToplevel):
    """Janela de entrada de dados customizada."""
    def __init__(self, parent, titulo="Entrada", texto="Insira um valor:"):
        super().__init__(parent)
        self.title(titulo)
        self.geometry("300x150")
        self.transient(parent)
        self.grab_set()
        self._resultado = None
        ctk.CTkLabel(self, text=texto).pack(pady=10, padx=10)
        self.entrada = ctk.CTkEntry(self, width=250)
        self.entrada.pack(pady=5, padx=10)
        self.entrada.focus()
        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(pady=10)
        ctk.CTkButton(frame_botoes, text="OK", command=self._evento_ok).pack(side="left", padx=10)
        ctk.CTkButton(frame_botoes, text="Cancelar", command=self._evento_cancelar, fg_color="#D32F2F", hover_color="#B71C1C").pack(side="left", padx=10)
        self.protocol("WM_DELETE_WINDOW", self._evento_cancelar)
        self.entrada.bind("<Return>", self._evento_ok)
        self.after(100, self.lift)

    def _evento_ok(self, event=None):
        self._resultado = self.entrada.get()
        self.destroy()

    def _evento_cancelar(self):
        self._resultado = None
        self.destroy()

    def obter_entrada(self):
        self.wait_window()
        try:
            return int(self._resultado) if self._resultado else None
        except (ValueError, TypeError):
            return self._resultado

# --- SEÇÃO 3: CONTROLADOR PRINCIPAL DA APLICAÇÃO ---

class AppPurobet(ctk.CTk):
    """
    Classe principal da aplicação, que gerencia a janela e a transição entre telas.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("PUROBET Cassino")
        self.geometry("450x800")
        self.minsize(420, 750)
        self.usuario_atual = None
        self.carregador_imagens = CarregadorImagens()

        container = ctk.CTkFrame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.telas = {}
        for Tela in (TelaInicial, TelaLogin, TelaRegistro, TelaPrincipal, TelaAdmin, JogoBlackjack, JogoRoleta, JogoCrash):
            tela = Tela(container, self)
            self.telas[Tela] = tela
            tela.grid(row=0, column=0, sticky="nsew")

        self.mostrar_tela(TelaInicial)

    def mostrar_tela(self, classe_tela, dados=None):
        """Traz uma tela para a frente, tornando-a visível."""
        for tela in self.telas.values():
            if tela.winfo_ismapped() and hasattr(tela, 'ao_esconder'):
                tela.ao_esconder()

        tela = self.telas[classe_tela]
        if hasattr(tela, 'ao_mostrar'):
            tela.ao_mostrar(dados)
        tela.tkraise()

    def logout(self):
        """Faz o logout do usuário e volta para a tela inicial."""
        self.usuario_atual = None
        self.mostrar_tela(TelaInicial)

    def obter_saldo_usuario(self):
        """Busca o saldo do usuário atual no banco de dados."""
        if not self.usuario_atual: return 0
        dados = obter_dados_usuario(self.usuario_atual)
        return dados['saldo'] if dados else 0

    def atualizar_saldo_usuario_bd(self, mudanca_quantia, nome_jogo=None, valor_aposta=None):
        """
        Atualiza o saldo no banco de dados e, opcionalmente, registra um log de aposta.
        """
        if self.usuario_atual:
            atualizar_saldo(self.usuario_atual, mudanca_quantia)
            if nome_jogo and valor_aposta is not None:
                ganhos = mudanca_quantia + valor_aposta
                registrar_aposta(self.usuario_atual, nome_jogo, valor_aposta, ganhos)

    def exibir_mensagem(self, titulo, mensagem):
        """Mostra uma janela de mensagem customizada."""
        CaixaMensagem(self, titulo=titulo, mensagem=mensagem)

# --- SEÇÃO 4: TELAS PRINCIPAIS (HUB, LOGIN, ADMIN, ETC) ---

class TelaInicial(ctk.CTkFrame):
    """Tela de boas-vindas com opções de Login e Registro."""
    def __init__(self, parent, controlador):
        super().__init__(parent)
        frame_central = ctk.CTkFrame(self, fg_color="transparent")
        frame_central.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(frame_central, text="PUROBET", font=ctk.CTkFont(size=50, weight="bold")).pack(pady=(0, 10))
        ctk.CTkLabel(frame_central, text="O Cassino Fictício Mais Confiável", font=ctk.CTkFont(size=14)).pack(pady=(0, 40))
        ctk.CTkButton(frame_central, text="Login", font=ctk.CTkFont(size=16, weight="bold"), height=40, command=lambda: controlador.mostrar_tela(TelaLogin)).pack(pady=10, fill="x")
        ctk.CTkButton(frame_central, text="Registrar", font=ctk.CTkFont(size=16, weight="bold"), height=40, fg_color="#10a37f", hover_color="#0e8e6f", command=lambda: controlador.mostrar_tela(TelaRegistro)).pack(pady=10, fill="x")

class TelaLogin(ctk.CTkFrame):
    """Tela de Login para usuários e administrador."""
    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.controlador = controlador
        frame_central = ctk.CTkFrame(self, width=300)
        frame_central.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(frame_central, text="Login", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=20)
        self.entrada_usuario = ctk.CTkEntry(frame_central, placeholder_text="Usuário", width=250, height=35)
        self.entrada_usuario.pack(pady=10, padx=20)
        self.entrada_senha = ctk.CTkEntry(frame_central, placeholder_text="Senha", show="*", width=250, height=35)
        self.entrada_senha.pack(pady=10, padx=20)
        ctk.CTkButton(frame_central, text="Entrar", height=40, command=self.login).pack(pady=20, padx=20, fill="x")
        ctk.CTkButton(frame_central, text="Voltar", height=30, fg_color="transparent", border_width=1, command=lambda: controlador.mostrar_tela(TelaInicial)).pack(pady=(0,20), padx=20, fill="x")

    def login(self):
        """Verifica as credenciais e direciona o usuário."""
        usuario, senha = self.entrada_usuario.get(), self.entrada_senha.get()
        if usuario == "puroadmin" and senha == "123456":
            self.controlador.usuario_atual = "puroadmin"
            self.controlador.mostrar_tela(TelaAdmin)
        elif autenticar_usuario(usuario, senha):
            self.controlador.usuario_atual = usuario
            self.controlador.mostrar_tela(TelaPrincipal)
        else:
            self.controlador.exibir_mensagem("Erro", "Usuário ou senha inválidos.")

class TelaRegistro(ctk.CTkFrame):
    """Tela de Registro de novos usuários."""
    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.controlador = controlador
        frame_central = ctk.CTkFrame(self, width=300)
        frame_central.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(frame_central, text="Criar Conta", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=20)
        self.entrada_usuario = ctk.CTkEntry(frame_central, placeholder_text="Usuário", width=250, height=35)
        self.entrada_usuario.pack(pady=10, padx=20)
        self.entrada_senha = ctk.CTkEntry(frame_central, placeholder_text="Senha", show="*", width=250, height=35)
        self.entrada_senha.pack(pady=10, padx=20)
        self.entrada_ref = ctk.CTkEntry(frame_central, placeholder_text="Código de Convite (Opcional)", width=250, height=35)
        self.entrada_ref.pack(pady=10, padx=20)
        ctk.CTkButton(frame_central, text="Registrar", height=40, fg_color="#10a37f", hover_color="#0e8e6f", command=self.registrar).pack(pady=20, padx=20, fill="x")
        ctk.CTkButton(frame_central, text="Voltar", height=30, fg_color="transparent", border_width=1, command=lambda: controlador.mostrar_tela(TelaInicial)).pack(pady=(0, 20), padx=20, fill="x")

    def gerar_codigo_referencia(self):
        """Gera um código de referência aleatório."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def registrar(self):
        """Processa o registro de um novo usuário."""
        usuario, senha, codigo_ref = self.entrada_usuario.get(), self.entrada_senha.get(), self.entrada_ref.get()
        if not usuario or not senha:
            self.controlador.exibir_mensagem("Erro", "Preencha usuário e senha."); return

        if not adicionar_usuario(usuario, senha, 1000, self.gerar_codigo_referencia()):
            self.controlador.exibir_mensagem("Erro", "Este nome de usuário já existe."); return

        if codigo_ref:
            indicador = encontrar_usuario_por_referencia(codigo_ref)
            if indicador:
                atualizar_saldo(indicador, 200)
                registrar_transacao(indicador, 'bonus_referencia', 200)
                self.controlador.exibir_mensagem("Bônus!", f"O usuário {indicador} recebeu $200 por sua indicação!")
            else:
                self.controlador.exibir_mensagem("Aviso", "Código de convite inválido.")

        self.controlador.exibir_mensagem("Sucesso", f"Usuário {usuario} registrado!"); self.controlador.mostrar_tela(TelaLogin)

class TelaPrincipal(ctk.CTkFrame):
    """O menu principal do usuário, onde ele escolhe o jogo."""
    def __init__(self, parent, controlador):
        super().__init__(parent, fg_color="#242424")
        self.controlador = controlador
        frame_superior = ctk.CTkFrame(self, corner_radius=0)
        frame_superior.pack(fill="x")
        self.label_boas_vindas = ctk.CTkLabel(frame_superior, text="", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_boas_vindas.pack(pady=(20, 5), padx=20, anchor="w")
        self.label_saldo = ctk.CTkLabel(frame_superior, text="", font=ctk.CTkFont(size=16))
        self.label_saldo.pack(pady=(0, 10), padx=20, anchor="w")
        self.label_codigo_ref = ctk.CTkLabel(frame_superior, text="", font=ctk.CTkFont(size=12, slant="italic"), text_color="gray")
        self.label_codigo_ref.pack(pady=(0, 20), padx=20, anchor="w")
        frame_jogos = ctk.CTkScrollableFrame(self, fg_color="transparent")
        frame_jogos.pack(pady=10, padx=15, fill="both", expand=True)
        ctk.CTkLabel(frame_jogos, text="Escolha um Jogo", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        botoes_jogo = [("🃏 Blackjack", JogoBlackjack, "#c0392b"), ("🌀 Roleta", JogoRoleta, "#8e44ad"), ("✈️ Aviãozinho (Crash)", JogoCrash, "#f39c12")]
        for nome, tela, cor in botoes_jogo:
            ctk.CTkButton(frame_jogos, text=nome, font=ctk.CTkFont(size=16), height=60, fg_color=cor, hover_color=self.escurecer_cor(cor), command=lambda t=tela: controlador.mostrar_tela(t)).pack(pady=10, fill="x")
        frame_acoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_acoes.pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(frame_acoes, text="💰 Adicionar Saldo", fg_color="#1abc9c", hover_color="#16a085", command=self.adicionar_saldo).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(frame_acoes, text="Sair", fg_color="#e67e22", hover_color="#d35400", command=controlador.logout).pack(side="right", expand=True, padx=5)

    def ao_mostrar(self, dados=None): self.atualizar_info()
    def escurecer_cor(self, cor_hex):
        r,g,b = int(cor_hex[1:3],16), int(cor_hex[3:5],16), int(cor_hex[5:7],16)
        return f"#{max(0,r-20):02x}{max(0,g-20):02x}{max(0,b-20):02x}"
    def atualizar_info(self):
        """Busca os dados do usuário e atualiza os textos na tela."""
        dados_usuario = obter_dados_usuario(self.controlador.usuario_atual)
        if dados_usuario:
            self.label_boas_vindas.configure(text=f"Olá, {self.controlador.usuario_atual}!")
            self.label_saldo.configure(text=f"Saldo: ${dados_usuario['saldo']:,.2f}", text_color="#4CAF50")
            self.label_codigo_ref.configure(text=f"Seu código: {dados_usuario['codigo_referencia']}")

    def adicionar_saldo(self):
        """Adiciona saldo fictício à conta do usuário."""
        quantia = CaixaDialogo(self, titulo="Adicionar Saldo", texto="Quanto saldo fictício deseja adicionar?").obter_entrada()
        if quantia and quantia > 0:
            self.controlador.atualizar_saldo_usuario_bd(quantia)
            registrar_transacao(self.controlador.usuario_atual, 'deposito', quantia)
            self.controlador.exibir_mensagem("Sucesso", f"${quantia} adicionados!")
            self.atualizar_info()

class TelaAdmin(ctk.CTkFrame):
    """Painel de controle do administrador."""
    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.controlador = controlador
        ctk.CTkLabel(self, text="PUROBET ADMIN", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)
        self.abas = ctk.CTkTabview(self)
        self.abas.pack(fill="both", expand=True, padx=10, pady=10)
        self.aba_usuarios = self.abas.add("Usuários")
        self.aba_odds = self.abas.add("Odds")
        self.aba_estatisticas = self.abas.add("Estatísticas")
        self.aba_logs = self.abas.add("📊 Logs")

        self.frame_scroll_usuarios = ctk.CTkScrollableFrame(self.aba_usuarios, label_text="Lista de Usuários")
        self.frame_scroll_usuarios.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(self.aba_odds, text="Pagamento Roleta (Número):").pack(pady=(10,0), padx=10)
        self.slider_pagamento_roleta = ctk.CTkSlider(self.aba_odds, from_=10, to=50, number_of_steps=40)
        self.slider_pagamento_roleta.pack(fill="x", padx=10)
        self.label_pagamento_roleta = ctk.CTkLabel(self.aba_odds, text="")
        self.slider_pagamento_roleta.bind("<ButtonRelease-1>", self.atualizar_label_slider)
        self.label_pagamento_roleta.pack()
        ctk.CTkButton(self.aba_odds, text="Salvar Odds", command=self.salvar_odds).pack(pady=20)

        self.frame_estatisticas = ctk.CTkFrame(self.aba_estatisticas, fg_color="transparent")
        self.frame_estatisticas.place(relx=0.5, rely=0.5, anchor="center")
        self.label_total_usuarios = ctk.CTkLabel(self.frame_estatisticas, font=ctk.CTkFont(size=16))
        self.label_total_usuarios.pack(anchor="w", padx=10, pady=5)
        self.label_saldo_total = ctk.CTkLabel(self.frame_estatisticas, font=ctk.CTkFont(size=16))
        self.label_saldo_total.pack(anchor="w", padx=10, pady=5)

        frame_filtro_log = ctk.CTkFrame(self.aba_logs)
        frame_filtro_log.pack(fill="x", padx=5, pady=5)
        self.entrada_busca_log = ctk.CTkEntry(frame_filtro_log, placeholder_text="Filtrar por usuário...")
        self.entrada_busca_log.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.entrada_busca_log.bind("<Return>", self.atualizar_logs)
        ctk.CTkButton(frame_filtro_log, text="Buscar", command=self.atualizar_logs).pack(side="left")
        self.abas_logs = ctk.CTkTabview(self.aba_logs)
        self.abas_logs.pack(fill="both", expand=True, padx=5, pady=5)
        self.aba_logs_apostas = self.abas_logs.add("Apostas")
        self.aba_logs_transacoes = self.abas_logs.add("Transações")
        self.scroll_logs_apostas = ctk.CTkScrollableFrame(self.aba_logs_apostas)
        self.scroll_logs_apostas.pack(fill="both", expand=True)
        self.scroll_logs_transacoes = ctk.CTkScrollableFrame(self.aba_logs_transacoes)
        self.scroll_logs_transacoes.pack(fill="both", expand=True)

        ctk.CTkButton(self, text="Logout", fg_color="#e67e22", hover_color="#d35400", command=controlador.logout).pack(pady=10)

    def ao_mostrar(self, data=None): self.atualizar_todas_abas()
    def atualizar_todas_abas(self):
        self.atualizar_usuarios()
        self.atualizar_estatisticas()
        self.atualizar_odds()
        self.atualizar_logs()

    def atualizar_usuarios(self):
        for widget in self.frame_scroll_usuarios.winfo_children(): widget.destroy()
        for usuario, saldo in obter_todos_usuarios():
            frame_usuario = ctk.CTkFrame(self.frame_scroll_usuarios)
            frame_usuario.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(frame_usuario, text=f"{usuario} - Saldo: ${saldo:.2f}").pack(side="left", padx=10)
            frame_botoes = ctk.CTkFrame(frame_usuario, fg_color="transparent")
            frame_botoes.pack(side="right")
            ctk.CTkButton(frame_botoes, text="+", width=30, fg_color="#27ae60", command=lambda u=usuario: self.adicionar_saldo_admin(u)).pack(side="left", padx=2)
            ctk.CTkButton(frame_botoes, text="-", width=30, fg_color="#c0392b", command=lambda u=usuario: self.remover_saldo_admin(u)).pack(side="left", padx=2)
            ctk.CTkButton(frame_botoes, text="🗑️", width=30, fg_color="#7f8c8d", command=lambda u=usuario: self.deletar_usuario(u)).pack(side="left", padx=2)

    def atualizar_estatisticas(self):
        todos_usuarios = obter_todos_usuarios()
        self.label_total_usuarios.configure(text=f"Total de usuários: {len(todos_usuarios)}")
        self.label_saldo_total.configure(text=f"Saldo total em jogo: ${sum(b for u,b in todos_usuarios):,.2f}")

    def atualizar_odds(self):
        self.slider_pagamento_roleta.set(obter_configuracao_jogo('pagamento_roleta_numero'))
        self.atualizar_label_slider()

    def atualizar_logs(self, event=None):
        filtro_usuario = self.entrada_busca_log.get() or None
        for widget in self.scroll_logs_apostas.winfo_children(): widget.destroy()
        for log in obter_logs('logs_apostas', filtro_usuario):
            _, usuario, jogo, aposta, resultado, ts = log
            cor = "#4CAF50" if resultado >= 0 else "#D32F2F"
            texto_log = f"[{ts}] {usuario} | {jogo}: apostou ${aposta:.2f}, resultado ${resultado:+.2f}"
            ctk.CTkLabel(self.scroll_logs_apostas, text=texto_log, text_color=cor, anchor="w").pack(fill="x")

        for widget in self.scroll_logs_transacoes.winfo_children(): widget.destroy()
        for log in obter_logs('logs_transacoes', filtro_usuario):
            _, usuario, tipo, quantia, ts = log
            texto_log = f"[{ts}] {usuario} | {tipo.replace('_', ' ').capitalize()}: ${quantia:,.2f}"
            ctk.CTkLabel(self.scroll_logs_transacoes, text=texto_log, anchor="w").pack(fill="x")

    def adicionar_saldo_admin(self, usuario):
        quantia = CaixaDialogo(self, titulo="Adicionar Saldo", texto=f"Adicionar para {usuario}:").obter_entrada()
        if quantia and quantia > 0:
            atualizar_saldo(usuario, quantia)
            registrar_transacao(usuario, 'deposito_admin', quantia)
            self.atualizar_usuarios()
            self.atualizar_estatisticas()

    def remover_saldo_admin(self, usuario):
        quantia = CaixaDialogo(self, titulo="Remover Saldo", texto=f"Remover de {usuario}:").obter_entrada()
        if quantia and quantia > 0:
            atualizar_saldo(usuario, -quantia)
            registrar_transacao(usuario, 'saque_admin', -quantia)
            self.atualizar_usuarios()
            self.atualizar_estatisticas()

    def deletar_usuario(self, usuario):
        from tkinter import messagebox
        if messagebox.askyesno("Confirmar", f"Excluir {usuario}?"):
            deletar_usuario_bd(usuario)
            self.atualizar_usuarios()
            self.atualizar_estatisticas()

    def atualizar_label_slider(self, event=None):
        self.label_pagamento_roleta.configure(text=f"{int(self.slider_pagamento_roleta.get())}x")

    def salvar_odds(self):
        definir_configuracao_jogo('pagamento_roleta_numero', int(self.slider_pagamento_roleta.get()))
        self.controlador.exibir_mensagem("Sucesso", "Odds atualizadas!")

# --- SEÇÃO 5: TELAS DOS JOGOS ---

class TelaJogoBase(ctk.CTkFrame):
    """Classe base para as telas de jogos."""
    def __init__(self, parent, controlador, titulo_jogo):
        super().__init__(parent)
        self.controlador = controlador
        self._id_after = None
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        frame_superior = ctk.CTkFrame(self, fg_color="transparent")
        frame_superior.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        frame_superior.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(frame_superior, text="← Voltar ao Hub", width=120, command=lambda: controlador.mostrar_tela(TelaPrincipal)).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(frame_superior, text=titulo_jogo, font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=1, sticky="ew")
        self.label_saldo = ctk.CTkLabel(frame_superior, text="", font=ctk.CTkFont(size=14))
        self.label_saldo.grid(row=0, column=2, sticky="e", padx=10)
        self.frame_jogo = ctk.CTkFrame(self)
        self.frame_jogo.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    def ao_mostrar(self, dados=None):
        self.atualizar_exibicao_saldo()

    def ao_esconder(self):
        if self._id_after:
            self.after_cancel(self._id_after)
            self._id_after = None

    def atualizar_exibicao_saldo(self, mudanca=0):
        saldo = self.controlador.obter_saldo_usuario()
        self.label_saldo.configure(text=f"Saldo: ${saldo:,.2f}")
        if mudanca != 0:
            cor = "#4CAF50" if mudanca > 0 else "#D32F2F"
            self.label_saldo.configure(text_color=cor)
            self.after(1000, lambda: self.label_saldo.configure(text_color="white"))

class JogoBlackjack(TelaJogoBase):
    """Tela e lógica do jogo Blackjack (21)."""
    def __init__(self, parent, controlador):
        super().__init__(parent, controlador, "🃏 Blackjack")
        self.baralho = []
        self.mao_jogador, self.mao_dealer = [], []
        self.valor_aposta = 0
        self.frame_jogo.grid_rowconfigure([0, 1], weight=1)
        self.frame_jogo.grid_columnconfigure(0, weight=1)
        self.frame_dealer = ctk.CTkFrame(self.frame_jogo)
        self.frame_dealer.grid(row=0, column=0, sticky="nsew", pady=5)
        self.frame_jogador = ctk.CTkFrame(self.frame_jogo)
        self.frame_jogador.grid(row=1, column=0, sticky="nsew", pady=5)
        self.label_pontos_dealer = ctk.CTkLabel(self.frame_dealer, text="Dealer: 0", font=ctk.CTkFont(size=16))
        self.label_pontos_dealer.place(relx=0.02, rely=0.05)
        self.label_pontos_jogador = ctk.CTkLabel(self.frame_jogador, text="Você: 0", font=ctk.CTkFont(size=16))
        self.label_pontos_jogador.place(relx=0.02, rely=0.05)
        self.label_status = ctk.CTkLabel(self, text="Faça sua aposta para começar", font=ctk.CTkFont(size=14))
        self.label_status.grid(row=2, column=0, pady=5)
        container_controles = ctk.CTkFrame(self)
        container_controles.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        container_controles.grid_columnconfigure(0, weight=1)
        frame_aposta = ctk.CTkFrame(container_controles, fg_color="transparent")
        frame_aposta.grid(row=0, column=0, pady=5)
        self.entrada_aposta = ctk.CTkEntry(frame_aposta, placeholder_text="Aposta", width=100)
        self.entrada_aposta.pack(side="left", padx=5)
        self.botao_apostar = ctk.CTkButton(frame_aposta, text="Apostar", command=self.distribuir_cartas)
        self.botao_apostar.pack(side="left", padx=5)
        frame_acoes_jogo = ctk.CTkFrame(container_controles, fg_color="transparent")
        frame_acoes_jogo.grid(row=1, column=0, pady=5)
        self.botao_pedir = ctk.CTkButton(frame_acoes_jogo, text="Pedir", command=self.pedir_carta, state="disabled")
        self.botao_pedir.pack(side="left", padx=10)
        self.botao_parar = ctk.CTkButton(frame_acoes_jogo, text="Parar", command=self.parar, state="disabled", fg_color="#c0392b", hover_color="#a52a1a")
        self.botao_parar.pack(side="left", padx=10)

    def ao_mostrar(self, data=None):
        super().ao_mostrar(data)
        self.reiniciar_jogo()

    def obter_valor_carta(self, carta):
        rank = carta.split('_')[1]
        if rank in ['J', 'Q', 'K', 'T']: return 10
        if rank == 'A': return 11
        return int(rank)

    def obter_valor_mao(self, mao):
        valor = sum(self.obter_valor_carta(c) for c in mao)
        num_ases = sum(1 for c in mao if c.endswith('_A'))
        while valor > 21 and num_ases:
            valor -= 10
            num_ases -= 1
        return valor

    def criar_baralho(self):
        naipes = ['hearts', 'diamonds', 'clubs', 'spades']
        ranks = [str(i) for i in range(2, 10)] + ['T', 'J', 'Q', 'K', 'A']
        self.baralho = [f"{n}_{r}" for n in naipes for r in ranks]
        random.shuffle(self.baralho)

    def distribuir_cartas(self):
        try:
            aposta = int(self.entrada_aposta.get())
        except (ValueError, TypeError):
            self.controlador.exibir_mensagem("Erro", "Aposta inválida.")
            return
        if not (0 < aposta <= self.controlador.obter_saldo_usuario()):
            self.controlador.exibir_mensagem("Erro", "Saldo insuficiente.")
            return
        self.valor_aposta = aposta
        self.controlador.atualizar_saldo_usuario_bd(-aposta)
        self.atualizar_exibicao_saldo(-aposta)
        self.criar_baralho()
        self.mao_jogador = [self.baralho.pop(), self.baralho.pop()]
        self.mao_dealer = [self.baralho.pop(), self.baralho.pop()]
        self.atualizar_interface()
        self.label_status.configure(text=f"Aposta: ${self.valor_aposta}. Sua vez.")
        self.botao_apostar.configure(state="disabled")
        self.botao_pedir.configure(state="normal")
        self.botao_parar.configure(state="normal")
        if self.obter_valor_mao(self.mao_jogador) == 21:
            self.parar()

    def pedir_carta(self):
        self.mao_jogador.append(self.baralho.pop())
        self.atualizar_interface()
        if self.obter_valor_mao(self.mao_jogador) > 21:
            self.finalizar_jogo("Você estourou! Perdeu.")

    def parar(self):
        self.botao_pedir.configure(state="disabled")
        self.botao_parar.configure(state="disabled")
        while self.obter_valor_mao(self.mao_dealer) < 17:
            self.mao_dealer.append(self.baralho.pop())
        pontos_jogador, pontos_dealer = self.obter_valor_mao(self.mao_jogador), self.obter_valor_mao(self.mao_dealer)
        self.atualizar_interface(mostrar_dealer_completo=True)
        if pontos_dealer > 21 or pontos_jogador > pontos_dealer:
            self.finalizar_jogo("Você ganhou!", self.valor_aposta * 2)
        elif pontos_jogador < pontos_dealer:
            self.finalizar_jogo("Você perdeu.")
        else:
            self.finalizar_jogo("Empate!", self.valor_aposta)

    def finalizar_jogo(self, mensagem, ganhos=0):
        self.label_status.configure(text=mensagem)
        self.controlador.atualizar_saldo_usuario_bd(ganhos, nome_jogo="Blackjack", valor_aposta=self.valor_aposta)
        if ganhos > 0:
            self.atualizar_exibicao_saldo(ganhos - self.valor_aposta)
        else:
            self.atualizar_exibicao_saldo(0)
        self.botao_apostar.configure(state="normal")
        self.botao_pedir.configure(state="disabled")
        self.botao_parar.configure(state="disabled")

    def atualizar_interface(self, mostrar_dealer_completo=False):
        for widget in self.frame_jogador.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and hasattr(widget, "eh_carta"): widget.destroy()
        for widget in self.frame_dealer.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and hasattr(widget, "eh_carta"): widget.destroy()

        for i, nome_carta in enumerate(self.mao_jogador):
            imagem_carta = self.controlador.carregador_imagens.obter_imagem_ctk(nome_carta)
            if imagem_carta:
                label_carta = ctk.CTkLabel(self.frame_jogador, image=imagem_carta, text="")
                label_carta.eh_carta = True
                label_carta.place(relx=0.25 + i*0.1, rely=0.5, anchor="center")

        if self.mao_dealer:
            mao_dealer_para_mostrar = self.mao_dealer if mostrar_dealer_completo else [self.mao_dealer[0], 'back']
            for i, nome_carta in enumerate(mao_dealer_para_mostrar):
                imagem_carta = self.controlador.carregador_imagens.obter_imagem_ctk(nome_carta)
                if imagem_carta:
                    label_carta = ctk.CTkLabel(self.frame_dealer, image=imagem_carta, text="")
                    label_carta.eh_carta = True
                    label_carta.place(relx=0.25 + i*0.1, rely=0.5, anchor="center")

        self.label_pontos_jogador.configure(text=f"Você: {self.obter_valor_mao(self.mao_jogador)}")
        if self.mao_dealer:
            pontos_dealer = self.obter_valor_mao(self.mao_dealer) if mostrar_dealer_completo else self.obter_valor_carta(self.mao_dealer[0])
            self.label_pontos_dealer.configure(text=f"Dealer: {pontos_dealer}{'' if mostrar_dealer_completo else ' + ?'}")
        else:
            self.label_pontos_dealer.configure(text="Dealer: 0")

    def reiniciar_jogo(self):
        self.mao_jogador, self.mao_dealer = [], []
        self.atualizar_interface()
        self.label_status.configure(text="Faça sua aposta para começar")
        self.botao_apostar.configure(state="normal")
        self.botao_pedir.configure(state="disabled")
        self.botao_parar.configure(state="disabled")
        self.entrada_aposta.delete(0, 'end')
        self.label_pontos_jogador.configure(text="Você: 0")
        self.label_pontos_dealer.configure(text="Dealer: 0")

class JogoRoleta(TelaJogoBase):
    """Tela e lógica do jogo da Roleta."""
    def __init__(self, parent, controlador):
        super().__init__(parent, controlador, "🌀 Roleta")
        self.numeros = {n: c for n, c in zip(range(37), (['green'] + ['red', 'black'] * 18))}
        self.mapa_cores = {"red": "#C0392B", "black": "#2C3E50", "green": "#27AE60"}
        self.historico = []
        self.apostas = []
        self.mapa_traducao = {'red':'Vermelho','black':'Preto','even':'Par','odd':'Ímpar','low':'1-18 (Menores)','high':'19-36 (Maiores)'}
        self.frame_jogo.grid_columnconfigure(0, weight=2)
        self.frame_jogo.grid_columnconfigure(1, weight=1)
        self.frame_jogo.grid_rowconfigure(0, weight=1)
        painel_tabuleiro = ctk.CTkFrame(self.frame_jogo, fg_color="transparent")
        painel_tabuleiro.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        painel_tabuleiro.grid_rowconfigure(1, weight=1)
        painel_tabuleiro.grid_columnconfigure(0, weight=1)
        frame_apostas_externas = ctk.CTkFrame(painel_tabuleiro)
        frame_apostas_externas.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        frame_apostas_externas.grid_columnconfigure(tuple(range(6)), weight=1)
        ctk.CTkButton(frame_apostas_externas, text="1-18", command=lambda: self.adicionar_aposta('range', 'low')).grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        ctk.CTkButton(frame_apostas_externas, text="Par", command=lambda: self.adicionar_aposta('parity', 'even')).grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        ctk.CTkButton(frame_apostas_externas, text="Vermelho", fg_color=self.mapa_cores['red'], command=lambda: self.adicionar_aposta('color', 'red')).grid(row=0, column=2, sticky="ew", padx=2, pady=2)
        ctk.CTkButton(frame_apostas_externas, text="Preto", fg_color=self.mapa_cores['black'], text_color="white", command=lambda: self.adicionar_aposta('color', 'black')).grid(row=0, column=3, sticky="ew", padx=2, pady=2)
        ctk.CTkButton(frame_apostas_externas, text="Ímpar", command=lambda: self.adicionar_aposta('parity', 'odd')).grid(row=0, column=4, sticky="ew", padx=2, pady=2)
        ctk.CTkButton(frame_apostas_externas, text="19-36", command=lambda: self.adicionar_aposta('range', 'high')).grid(row=0, column=5, sticky="ew", padx=2, pady=2)
        frame_grid_numeros = ctk.CTkScrollableFrame(painel_tabuleiro, label_text="Apostar em Números")
        frame_grid_numeros.grid(row=1, column=0, sticky="nsew")
        for i in range(37):
            btn = ctk.CTkButton(frame_grid_numeros, text=str(i), fg_color=self.mapa_cores[self.numeros[i]], width=40, command=lambda n=i: self.adicionar_aposta('number', n))
            btn.grid(row=(i//6), column=i%6, padx=2, pady=2)
        painel_controle = ctk.CTkFrame(self.frame_jogo)
        painel_controle.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        painel_controle.grid_columnconfigure(0, weight=1)
        painel_controle.grid_rowconfigure(2, weight=1)
        self.label_resultado = ctk.CTkLabel(painel_controle, text="?", font=ctk.CTkFont(size=60, weight="bold"), fg_color="grey", height=120, corner_radius=10)
        self.label_resultado.grid(row=0, column=0, sticky="ew", pady=10, padx=10)
        self.frame_historico = ctk.CTkFrame(painel_controle, fg_color="transparent")
        self.frame_historico.grid(row=1, column=0, pady=5, padx=10)
        self.frame_scroll_apostas = ctk.CTkScrollableFrame(painel_controle, label_text="Suas Apostas")
        self.frame_scroll_apostas.grid(row=2, column=0, sticky="nsew", pady=5, padx=10)
        self.label_aposta_total = ctk.CTkLabel(painel_controle, text="Aposta Total: $0")
        self.label_aposta_total.grid(row=3, column=0, pady=5, padx=10)
        self.botao_girar = ctk.CTkButton(painel_controle, text="Girar!", command=self.girar, state="disabled", height=40)
        self.botao_girar.grid(row=4, column=0, sticky="ew", pady=(5,2), padx=10)
        self.botao_limpar_apostas = ctk.CTkButton(painel_controle, text="Limpar Apostas", fg_color="grey", command=self.limpar_apostas)
        self.botao_limpar_apostas.grid(row=5, column=0, sticky="ew", pady=(2,10), padx=10)

    def ao_mostrar(self, data=None):
        super().ao_mostrar(data)
        self.limpar_apostas()

    def adicionar_aposta(self, tipo_aposta, valor):
        valor_exibicao = self.mapa_traducao.get(valor, str(valor))
        quantia = CaixaDialogo(self, titulo="Valor da Aposta", texto=f"Apostar em {valor_exibicao}:").obter_entrada()
        if quantia and quantia > 0:
            saldo_disponivel = self.controlador.obter_saldo_usuario() - sum(b['quantia'] for b in self.apostas)
            if quantia > saldo_disponivel:
                self.controlador.exibir_mensagem("Erro", "Saldo insuficiente.")
                return
            self.apostas.append({'tipo': tipo_aposta, 'valor': valor, 'quantia': quantia})
            self.atualizar_exibicao_apostas()

    def atualizar_exibicao_apostas(self):
        for widget in self.frame_scroll_apostas.winfo_children(): widget.destroy()
        total = sum(b['quantia'] for b in self.apostas)
        for aposta in self.apostas:
            valor_exibicao = self.mapa_traducao.get(aposta['valor'], str(aposta['valor']))
            ctk.CTkLabel(self.frame_scroll_apostas, text=f"{valor_exibicao}: ${aposta['quantia']}").pack(anchor="w", padx=5)
        self.label_aposta_total.configure(text=f"Aposta Total: ${total}")
        self.botao_girar.configure(state="normal" if total > 0 else "disabled")

    def limpar_apostas(self):
        self.apostas.clear()
        self.atualizar_exibicao_apostas()

    def girar(self):
        aposta_total = sum(b['quantia'] for b in self.apostas)
        if aposta_total <= 0: return
        self.controlador.atualizar_saldo_usuario_bd(-aposta_total)
        self.atualizar_exibicao_saldo(-aposta_total)
        self.botao_girar.configure(state="disabled")
        self.botao_limpar_apostas.configure(state="disabled")
        self.animar_giro(random.randint(0, 36), 20, 50)

    def animar_giro(self, numero_vencedor, passos, delay):
        if passos > 0:
            num = random.randint(0, 36)
            self.label_resultado.configure(text=str(num), fg_color=self.mapa_cores[self.numeros[num]])
            self._id_after = self.after(delay, lambda: self.animar_giro(numero_vencedor, passos - 1, int(delay * 1.15)))
        else:
            self.label_resultado.configure(text=str(numero_vencedor), fg_color=self.mapa_cores[self.numeros[numero_vencedor]])
            ganhos_totais = self.calcular_ganhos(numero_vencedor)
            aposta_total = sum(b['quantia'] for b in self.apostas)
            self.controlador.atualizar_saldo_usuario_bd(ganhos_totais, nome_jogo="Roleta", valor_aposta=aposta_total)
            if ganhos_totais > 0:
                self.atualizar_exibicao_saldo(ganhos_totais - aposta_total)
                self.controlador.exibir_mensagem("Você Ganhou!", f"Parabéns! Você ganhou ${ganhos_totais:,.2f}!")
            else:
                self.controlador.exibir_mensagem("Não foi desta vez", "Mais sorte na próxima rodada!")
            self.historico.append(numero_vencedor)
            self.atualizar_historico()
            self.limpar_apostas()
            self.botao_limpar_apostas.configure(state="normal")

    def calcular_ganhos(self, num_vencedor):
        ganhos_totais = 0
        cor_vencedora = self.numeros[num_vencedor]
        eh_par = (num_vencedor % 2 == 0 and num_vencedor != 0)
        eh_baixo = (1 <= num_vencedor <= 18)
        for aposta in self.apostas:
            pagamento = 0
            if aposta['tipo'] == 'number' and aposta['valor'] == num_vencedor:
                pagamento = obter_configuracao_jogo('pagamento_roleta_numero')
            elif aposta['tipo'] == 'color' and aposta['valor'] == cor_vencedora:
                pagamento = 2
            elif aposta['tipo'] == 'parity' and ((aposta['valor'] == 'even' and eh_par) or (aposta['valor'] == 'odd' and not eh_par)):
                pagamento = 2
            elif aposta['tipo'] == 'range' and ((aposta['valor'] == 'low' and eh_baixo) or (aposta['valor'] == 'high' and not eh_baixo)):
                pagamento = 2
            if pagamento > 0:
                ganhos_totais += aposta['quantia'] * pagamento
        return ganhos_totais

    def atualizar_historico(self):
        for widget in self.frame_historico.winfo_children(): widget.destroy()
        linha_historico = ctk.CTkFrame(self.frame_historico, fg_color="transparent")
        linha_historico.pack()
        for num in self.historico[-10:]:
            ctk.CTkLabel(linha_historico, text=str(num), fg_color=self.mapa_cores[self.numeros[num]], corner_radius=5, width=28, height=28).pack(side="left", padx=2)

class JogoCrash(TelaJogoBase):
    """Tela e lógica do jogo Crash (Aviãozinho)."""
    def __init__(self, parent, controlador):
        super().__init__(parent, controlador, "✈️ Aviãozinho")
        self.estado_jogo = "aguardando"
        self.multiplicador = 1.0
        self.ponto_crash = 1.0
        self.valor_aposta = 0
        self.saque_efetuado = False
        self.tempo_inicio = 0
        self.pontos_grafico = []
        self.historico = []
        self.imagem_aviao_photo = None

        self.frame_jogo.grid_columnconfigure(0, weight=3)
        self.frame_jogo.grid_columnconfigure(1, weight=1)
        self.frame_jogo.grid_rowconfigure(0, weight=1)

        self.canvas = Canvas(self.frame_jogo, bg="#2B2B2B", bd=0, highlightthickness=0, relief='ridge')
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.canvas.bind("<Configure>", self.desenhar_grafico)

        painel_controle = ctk.CTkFrame(self.frame_jogo)
        painel_controle.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        painel_controle.grid_columnconfigure(0, weight=1)
        painel_controle.grid_rowconfigure(3, weight=1)

        frame_aposta = ctk.CTkFrame(painel_controle, fg_color="transparent")
        frame_aposta.grid(row=0, column=0, pady=10, padx=10, sticky="ew")
        self.entrada_aposta = ctk.CTkEntry(frame_aposta, placeholder_text="Aposta")
        self.entrada_aposta.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.botao_apostar = ctk.CTkButton(frame_aposta, text="Apostar", command=self.fazer_aposta, width=100)
        self.botao_apostar.pack(side="left")

        self.botao_saque = ctk.CTkButton(painel_controle, text="Sacar!", font=ctk.CTkFont(size=18, weight="bold"), height=50, state="disabled", fg_color="#10a37f", hover_color="#0e8e6f", command=self.fazer_saque)
        self.botao_saque.grid(row=1, column=0, sticky="ew", pady=10, padx=10)

        self.label_status = ctk.CTkLabel(painel_controle, text="", font=ctk.CTkFont(size=16))
        self.label_status.grid(row=2, column=0, pady=10, padx=10)

        self.frame_historico = ctk.CTkScrollableFrame(painel_controle, label_text="Histórico")
        self.frame_historico.grid(row=3, column=0, sticky="nsew", pady=10, padx=10)

    def ao_mostrar(self, data=None):
        super().ao_mostrar(data)
        self.reiniciar_rodada()

    def fazer_aposta(self):
        if self.estado_jogo != "aguardando":
            self.controlador.exibir_mensagem("Aviso", "Aguarde a próxima rodada.")
            return
        try:
            aposta = int(self.entrada_aposta.get())
        except (ValueError, TypeError):
            self.controlador.exibir_mensagem("Erro", "Aposta inválida.")
            return
        if not (0 < aposta <= self.controlador.obter_saldo_usuario()):
            self.controlador.exibir_mensagem("Erro", "Saldo insuficiente.")
            return
        self.valor_aposta = aposta
        self.controlador.atualizar_saldo_usuario_bd(-aposta)
        self.atualizar_exibicao_saldo(-aposta)
        self.label_status.configure(text=f"Aposta de ${self.valor_aposta:,.2f} feita!")
        self.botao_apostar.configure(state="disabled")

    def fazer_saque(self):
        if self.estado_jogo == "correndo" and not self.saque_efetuado:
            self.saque_efetuado = True
            ganhos = self.valor_aposta * self.multiplicador
            self.controlador.atualizar_saldo_usuario_bd(ganhos, nome_jogo="Crash", valor_aposta=self.valor_aposta)
            self.atualizar_exibicao_saldo(ganhos - self.valor_aposta) # A aposta já foi subtraída
            self.label_status.configure(text=f"Você sacou com {self.multiplicador:.2f}x!")
            self.botao_saque.configure(state="disabled", text=f"GANHOU R$ {ganhos:,.2f}")

    def loop_jogo(self):
        if self.estado_jogo == "correndo":
            tempo_decorrido = time.time() - self.tempo_inicio
            self.multiplicador = math.pow(1.05, tempo_decorrido)

            if self.valor_aposta > 0 and not self.saque_efetuado:
                ganhos_potenciais = self.valor_aposta * self.multiplicador
                self.botao_saque.configure(text=f"Sacar R$ {ganhos_potenciais:,.2f}")

            if self.multiplicador >= self.ponto_crash:
                self.estado_jogo = "crashou"
                self.historico.append(self.ponto_crash)
                self.atualizar_historico()
                if self.valor_aposta > 0 and not self.saque_efetuado:
                    self.label_status.configure(text=f"CRASH! Você perdeu.")
                    registrar_aposta(self.controlador.usuario_atual, "Crash", self.valor_aposta, 0)
                else:
                    self.label_status.configure(text=f"CRASH em {self.ponto_crash:.2f}x")
                self.botao_saque.configure(state="disabled")
                self.desenhar_grafico(crashou=True)
                self._id_after = self.after(3000, self.reiniciar_rodada)
            else:
                self.desenhar_grafico()
                self._id_after = self.after(30, self.loop_jogo)

    def iniciar_corrida(self):
        self.estado_jogo = "correndo"
        self.tempo_inicio = time.time()
        self.ponto_crash = max(1.01, random.gammavariate(2, 2))
        if self.valor_aposta > 0: self.botao_saque.configure(state="normal")
        self.loop_jogo()

    def reiniciar_rodada(self):
        self.estado_jogo = "aguardando"
        self.multiplicador = 1.0
        self.valor_aposta = 0
        self.saque_efetuado = False
        self.pontos_grafico = []
        self.botao_apostar.configure(state="normal")
        self.botao_saque.configure(state="disabled", text="Sacar!")
        self.entrada_aposta.delete(0, 'end')
        self.desenhar_grafico()
        self.contagem_regressiva(5)

    def contagem_regressiva(self, contador):
        if self._id_after: self.after_cancel(self._id_after)
        if contador > 0:
            self.label_status.configure(text=f"Próxima rodada em {contador}...")
            self.desenhar_grafico()
            self._id_after = self.after(1000, lambda: self.contagem_regressiva(contador - 1))
        else:
            self.label_status.configure(text="")
            self.iniciar_corrida()

    def atualizar_historico(self):
        for widget in self.frame_historico.winfo_children(): widget.destroy()
        for m in reversed(self.historico[-10:]):
            ctk.CTkLabel(self.frame_historico, text=f"{m:.2f}x", text_color="#4CAF50" if m >= 2.0 else "#D32F2F", anchor="w").pack(fill="x")

    def desenhar_grafico(self, event=None, crashou=False):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 20 or h < 20: return

        tempo_decorrido = (time.time() - self.tempo_inicio) if self.estado_jogo == "correndo" else 0
        max_mult = max(2.0, self.multiplicador * 1.2, self.ponto_crash * 1.1)
        max_tempo = max(5.0, tempo_decorrido * 1.2)

        self.pontos_grafico = [(0, h)]
        for t_ms in range(int(tempo_decorrido * 100) + 1):
            t = t_ms / 100.0
            mult_atual = math.pow(1.05, t)
            x = (t / max_tempo) * w
            y = h - ((mult_atual - 1) / (max_mult - 1)) * h
            x = max(0, min(w, x))
            y = max(0, min(h, y))
            self.pontos_grafico.append((x, y))

        cor_linha = "#D32F2F" if crashou else "#E74C3C"

        if len(self.pontos_grafico) > 1:
            self.canvas.create_line(self.pontos_grafico, fill=cor_linha, width=4, smooth=True)

        texto_mult = f"{self.ponto_crash:.2f}x" if crashou else f"{self.multiplicador:.2f}x"
        tamanho_fonte = min(max(int(h / 5), 30), 100)
        self.canvas.create_text(w/2, h/2, text=texto_mult, font=("Roboto", tamanho_fonte, "bold"), fill="white", anchor="center")

        if self.estado_jogo == "correndo" or crashou:
            self.imagem_aviao_photo = self.controlador.carregador_imagens.obter_imagem_photo("plane", tamanho=(80, 50))
            if self.imagem_aviao_photo and self.pontos_grafico:
                aviao_x, aviao_y = self.pontos_grafico[-1]
                self.canvas.create_image(aviao_x, aviao_y, image=self.imagem_aviao_photo, anchor="center")

# --- SEÇÃO 6: EXECUÇÃO DA APLICAÇÃO ---

if __name__ == "__main__":
    inicializar_banco_de_dados()
    app = AppPurobet()
    app.mainloop()