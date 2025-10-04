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
DB_FILE = "purobet.db"

def init_db():
    """
    Inicializa o banco de dados. Cria o arquivo .db e as tabelas caso não existam.
    Esta função é chamada uma única vez quando o programa inicia.
    """
    conn = sqlite3.connect(DB_FILE)  # Conecta ao arquivo do banco de dados.
    cursor = conn.cursor()  # Cria um cursor para executar comandos SQL.

    # Cria a tabela 'users' para armazenar informações dos jogadores.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            balance REAL NOT NULL,
            referral_code TEXT UNIQUE NOT NULL
        )
    ''')

    # Cria a tabela 'game_settings' para armazenar configurações ajustáveis pelo admin.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_settings (
            setting_name TEXT PRIMARY KEY,
            value REAL NOT NULL
        )
    ''')

    # Cria a tabela 'bet_logs' para registrar cada aposta feita.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bet_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            game TEXT NOT NULL,
            bet_amount REAL NOT NULL,
            outcome REAL NOT NULL, 
            timestamp TEXT NOT NULL
        )
    ''')

    # Cria a tabela 'transaction_logs' para registrar depósitos e outras transações.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')

    # Insere uma configuração padrão para a roleta, caso ainda não exista.
    cursor.execute("INSERT OR IGNORE INTO game_settings (setting_name, value) VALUES (?, ?)", ('roulette_payout_number', 35))
    
    conn.commit()  # Salva as alterações no banco de dados.
    conn.close()   # Fecha a conexão com o banco de dados.

# --- Funções de Log ---

def log_bet(username, game, bet_amount, winnings):
    """Registra uma aposta no banco de dados, na tabela 'bet_logs'."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    outcome = winnings - bet_amount  # Calcula o ganho/perda líquido.
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Pega a data e hora atual.
    cursor.execute("INSERT INTO bet_logs (username, game, bet_amount, outcome, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (username, game, bet_amount, outcome, timestamp))
    conn.commit()
    conn.close()

def log_transaction(username, transaction_type, amount):
    """Registra uma transação financeira (depósito, bônus) na tabela 'transaction_logs'."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO transaction_logs (username, transaction_type, amount, timestamp) VALUES (?, ?, ?, ?)",
                   (username, transaction_type, amount, timestamp))
    conn.commit()
    conn.close()

# --- Funções de Usuário e Autenticação ---

def hash_password(password):
    """Gera um hash SHA-256 para uma senha. Nunca guardamos senhas em texto puro."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return stored_hash == hash_password(provided_password)

def add_user(username, password, balance, referral_code):
    """Adiciona um novo usuário ao banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash, balance, referral_code) VALUES (?, ?, ?, ?)",
                       (username, hash_password(password), balance, referral_code))
        conn.commit()
        log_transaction(username, 'deposito_inicial', balance) # Registra o saldo inicial como uma transação.
        return True
    except sqlite3.IntegrityError:  # Ocorre se o username (que é UNIQUE) já existir.
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    """Autentica um usuário, verificando se o nome e a senha correspondem."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()  # Pega o primeiro resultado da busca.
    conn.close()
    return bool(result and verify_password(result[0], password))

def get_user_data(username):
    """Busca e retorna os dados (saldo, código de ref.) de um usuário."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, referral_code FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return {'balance': result[0], 'referral_code': result[1]} if result else None

def update_balance(username, amount_change):
    """Atualiza o saldo de um usuário, somando ou subtraindo um valor."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount_change, username))
    conn.commit()
    conn.close()

def get_all_users():
    """Retorna uma lista de todos os usuários e seus saldos."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, balance FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def delete_user_db(username):
    """Deleta um usuário do banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def find_user_by_referral(ref_code):
    """Encontra o nome de um usuário a partir do seu código de referência."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE referral_code = ?", (ref_code,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# --- Funções de Configurações e Logs para Admin ---

def get_game_setting(setting_name):
    """Busca uma configuração de jogo no banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM game_settings WHERE setting_name = ?", (setting_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def set_game_setting(setting_name, value):
    """Atualiza uma configuração de jogo no banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE game_settings SET value = ? WHERE setting_name = ?", (value, setting_name))
    conn.commit()
    conn.close()

def get_logs(log_type='bet_logs', username_filter=None):
    """Busca logs (de apostas ou transações), com um filtro opcional por usuário."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    query = f"SELECT * FROM {log_type}"
    params = []
    if username_filter:
        query += " WHERE username LIKE ?"
        params.append(f"%{username_filter}%") # Usa LIKE para buscas parciais
    query += " ORDER BY timestamp DESC LIMIT 100" # Limita a 100 resultados para performance
    cursor.execute(query, params)
    logs = cursor.fetchall()
    conn.close()
    return logs

# --- SEÇÃO 2: CARREGADOR DE IMAGENS E WIDGETS CUSTOMIZADOS ---

class CardImageLoader:
    """
    Classe Singleton para carregar e armazenar em cache as imagens das cartas.
    Isso evita carregar a mesma imagem do disco repetidamente, melhorando a performance.
    """
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CardImageLoader, cls).__new__(cls)
            cls._instance.cache = {} # O cache é um dicionário para guardar as imagens já carregadas.
            cls._instance.plane_img = None # Cache específico para a imagem do avião.
        return cls._instance

    def get(self, card_name="back"):
        """
        Recebe um nome de carta (ex: 'hearts_A') e retorna um objeto de imagem do CustomTkinter.
        """
        if card_name in self.cache:
            return self.cache[card_name] # Retorna a imagem do cache se já foi carregada antes.

        # Mapeia os ranks internos (A, K, T) para os nomes de arquivo (ace, king, 10).
        rank_map = {'A': 'ace', 'K': 'king', 'Q': 'queen', 'J': 'jack', 'T': '10'}
        
        if card_name == "back":
            filepath = os.path.join("cards", "back.png")
        elif card_name == "plane": # Adicionado para carregar a imagem do avião.
            if self._instance.plane_img: return self._instance.plane_img
            filepath = os.path.join("cards", "plane.png")
            try:
                img = Image.open(filepath)
                # Redimensiona o avião para um tamanho adequado (ex: 80x50)
                img = img.resize((80, 50), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 50))
                self._instance.plane_img = ctk_img
                return ctk_img
            except FileNotFoundError:
                print(f"ERRO: Imagem 'plane.png' não encontrada em {filepath}.")
                return None
        else:
            suit, rank = card_name.split('_')
            rank_str = rank_map.get(rank, rank) # Usa o mapa ou o próprio rank se for um número.
            filename = f"{rank_str}_of_{suit}.png"
            filepath = os.path.join("cards", filename) # Monta o caminho completo do arquivo.
        
        try:
            # Abre a imagem usando a biblioteca Pillow.
            img = Image.open(filepath)
            # Redimensiona a imagem para um tamanho padrão, garantindo a consistência do layout.
            img = img.resize((70, 100), Image.LANCZOS)
            # Converte a imagem do Pillow para um formato que o CustomTkinter entende.
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(70, 100))
            self.cache[card_name] = ctk_img # Armazena a imagem processada no cache.
            return ctk_img
        except FileNotFoundError:
            # Se uma imagem não for encontrada, imprime um erro claro no terminal.
            print(f"ERRO: Imagem não encontrada em {filepath}. Verifique o nome do arquivo e a pasta 'cards'.")
            return None

class CustomMessageBox(ctk.CTkToplevel):
    """Uma janela de mensagem customizada para manter o estilo visual do app."""
    def __init__(self, parent, title="Mensagem", message=""):
        super().__init__(parent)
        self.title(title)
        self.geometry("350x150")
        self.transient(parent) # Faz a janela aparecer sobre a janela principal.
        self.grab_set()         # Bloqueia a interação com a janela principal.
        self.resizable(False, False)
        ctk.CTkLabel(self, text=message, wraplength=320, font=ctk.CTkFont(size=14)).pack(pady=20, padx=15, expand=True, fill="both")
        ctk.CTkButton(self, text="OK", command=self.destroy, width=100).pack(pady=10)
        self.after(100, self.lift) # Garante que a janela apareça na frente.

class CustomInputDialog(ctk.CTkToplevel):
    """Uma janela de entrada de dados customizada."""
    def __init__(self, parent, title="Entrada", text="Insira um valor:"):
        super().__init__(parent); self.title(title); self.geometry("300x150"); self.transient(parent); self.grab_set(); self._result = None
        ctk.CTkLabel(self, text=text).pack(pady=10, padx=10)
        self.entry = ctk.CTkEntry(self, width=250); self.entry.pack(pady=5, padx=10); self.entry.focus()
        btn_frame = ctk.CTkFrame(self, fg_color="transparent"); btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="OK", command=self._ok_event).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancelar", command=self._cancel_event, fg_color="#D32F2F", hover_color="#B71C1C").pack(side="left", padx=10)
        self.protocol("WM_DELETE_WINDOW", self._cancel_event); self.entry.bind("<Return>", self._ok_event); self.after(100, self.lift)
    def _ok_event(self, event=None): self._result = self.entry.get(); self.destroy()
    def _cancel_event(self): self._result = None; self.destroy()
    def get_input(self):
        self.wait_window() # Espera a janela ser fechada para retornar o valor.
        try: return int(self._result) if self._result else None
        except (ValueError, TypeError): return self._result

# --- SEÇÃO 3: CONTROLADOR PRINCIPAL DA APLICAÇÃO ---

class PurobetApp(ctk.CTk):
    """
    A classe principal da aplicação. Ela gerencia a janela principal e a transição entre as diferentes telas (frames).
    Funciona como um 'controlador' central.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("PUROBET Cassino"); self.geometry("450x800"); self.minsize(420, 750)
        self.current_user = None # Armazena o nome do usuário logado.
        self.card_loader = CardImageLoader() # Instancia o carregador de imagens.
        
        # O 'container' é um frame que preenche toda a janela. As telas dos jogos são colocadas sobre ele.
        container = ctk.CTkFrame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1); container.grid_columnconfigure(0, weight=1)

        self.frames = {} # Um dicionário para guardar todas as telas da aplicação.
        # Itera sobre todas as classes de tela e as cria, armazenando-as no dicionário.
        for F in (StartPage, LoginPage, RegisterPage, MainHubPage, AdminPage, BlackjackGame, RouletteGame, CrashGame):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew") # Coloca todas as telas no mesmo lugar; a visível fica por cima.

        self.show_frame(StartPage) # Mostra a tela inicial quando o app abre.

    def show_frame(self, cont_class, data=None):
        """Traz uma tela (frame) para a frente, tornando-a visível."""
        # Antes de mostrar uma nova tela, chama o método 'on_hide' da tela atual, se ele existir.
        # Isso é útil para parar loops de animação, como no jogo Crash.
        for frame in self.frames.values():
            if frame.winfo_ismapped() and hasattr(frame, 'on_hide'):
                frame.on_hide()
        
        frame = self.frames[cont_class]
        # Chama o método 'on_show' da nova tela, se ele existir, para atualizá-la.
        if hasattr(frame, 'on_show'):
            frame.on_show(data)
        frame.tkraise() # Traz o frame para a frente.

    def logout(self):
        """Faz o logout do usuário e volta para a tela inicial."""
        self.current_user = None
        self.show_frame(StartPage)

    def get_user_balance(self):
        """Busca o saldo do usuário atual no banco de dados."""
        if not self.current_user: return 0
        data = get_user_data(self.current_user)
        return data['balance'] if data else 0

    def update_user_balance_db(self, amount_change, game_name=None, bet_amount=None):
        """
        Atualiza o saldo do usuário no banco de dados e, opcionalmente, registra um log de aposta.
        """
        if self.current_user:
            update_balance(self.current_user, amount_change)
            if game_name and bet_amount is not None:
                # O ganho real é a mudança de saldo + o valor da aposta (que foi subtraído antes).
                winnings = amount_change + bet_amount 
                log_bet(self.current_user, game_name, bet_amount, winnings)

    def show_message(self, title, message):
        """Mostra uma janela de mensagem customizada."""
        CustomMessageBox(self, title=title, message=message)

# --- SEÇÃO 4: TELAS PRINCIPAIS (HUB, LOGIN, ADMIN, ETC) ---

class StartPage(ctk.CTkFrame):
    """A tela de boas-vindas com opções de Login e Registro."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.place(relx=0.5, rely=0.5, anchor="center") # Centraliza os botões.
        ctk.CTkLabel(main_frame, text="PUROBET", font=ctk.CTkFont(size=50, weight="bold")).pack(pady=(0, 10))
        ctk.CTkLabel(main_frame, text="O Cassino Fictício Mais Confiável", font=ctk.CTkFont(size=14)).pack(pady=(0, 40))
        ctk.CTkButton(main_frame, text="Login", font=ctk.CTkFont(size=16, weight="bold"), height=40, command=lambda: controller.show_frame(LoginPage)).pack(pady=10, fill="x")
        ctk.CTkButton(main_frame, text="Registrar", font=ctk.CTkFont(size=16, weight="bold"), height=40, fg_color="#10a37f", hover_color="#0e8e6f", command=lambda: controller.show_frame(RegisterPage)).pack(pady=10, fill="x")

class LoginPage(ctk.CTkFrame):
    """A tela de Login para usuários e administrador."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        main_frame = ctk.CTkFrame(self, width=300); main_frame.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(main_frame, text="Login", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=20)
        self.entry_user = ctk.CTkEntry(main_frame, placeholder_text="Usuário", width=250, height=35); self.entry_user.pack(pady=10, padx=20)
        self.entry_pass = ctk.CTkEntry(main_frame, placeholder_text="Senha", show="*", width=250, height=35); self.entry_pass.pack(pady=10, padx=20)
        ctk.CTkButton(main_frame, text="Entrar", height=40, command=self.login).pack(pady=20, padx=20, fill="x")
        ctk.CTkButton(main_frame, text="Voltar", height=30, fg_color="transparent", border_width=1, command=lambda: controller.show_frame(StartPage)).pack(pady=(0,20), padx=20, fill="x")

    def login(self):
        """Verifica as credenciais e direciona o usuário para a tela correta."""
        user, pwd = self.entry_user.get(), self.entry_pass.get()
        # Verificação especial para o administrador (não fica na tabela de usuários comuns).
        if user == "puroadmin" and pwd == "123456":
             self.controller.current_user = "puroadmin"
             self.controller.show_frame(AdminPage)
        # Autentica um usuário normal usando o banco de dados.
        elif authenticate_user(user, pwd):
            self.controller.current_user = user
            self.controller.show_frame(MainHubPage)
        else:
            self.controller.show_message("Erro", "Usuário ou senha inválidos.")

class RegisterPage(ctk.CTkFrame):
    """A tela de Registro de novos usuários."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        main_frame = ctk.CTkFrame(self, width=300); main_frame.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(main_frame, text="Criar Conta", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=20)
        self.entry_user = ctk.CTkEntry(main_frame, placeholder_text="Usuário", width=250, height=35); self.entry_user.pack(pady=10, padx=20)
        self.entry_pass = ctk.CTkEntry(main_frame, placeholder_text="Senha", show="*", width=250, height=35); self.entry_pass.pack(pady=10, padx=20)
        self.entry_ref = ctk.CTkEntry(main_frame, placeholder_text="Código de Convite (Opcional)", width=250, height=35); self.entry_ref.pack(pady=10, padx=20)
        ctk.CTkButton(main_frame, text="Registrar", height=40, fg_color="#10a37f", hover_color="#0e8e6f", command=self.register).pack(pady=20, padx=20, fill="x")
        ctk.CTkButton(main_frame, text="Voltar", height=30, fg_color="transparent", border_width=1, command=lambda: controller.show_frame(StartPage)).pack(pady=(0, 20), padx=20, fill="x")

    def generate_referral_code(self):
        """Gera um código de referência aleatório de 6 caracteres."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def register(self):
        """Processa o registro de um novo usuário."""
        user, pwd, ref_code = self.entry_user.get(), self.entry_pass.get(), self.entry_ref.get()
        if not user or not pwd:
            self.controller.show_message("Erro", "Preencha usuário e senha."); return
        
        # Tenta adicionar o usuário ao DB, com saldo inicial de 1000.
        if not add_user(user, pwd, 1000, self.generate_referral_code()):
            self.controller.show_message("Erro", "Este nome de usuário já existe."); return

        # Se um código de referência foi usado, encontra o usuário que indicou e dá o bônus.
        if ref_code:
            referrer = find_user_by_referral(ref_code)
            if referrer:
                update_balance(referrer, 200)
                log_transaction(referrer, 'bonus_referencia', 200)
                self.controller.show_message("Bônus!", f"O usuário {referrer} recebeu $200 por sua indicação!")
            else:
                self.controller.show_message("Aviso", "Código de convite inválido.")
        
        self.controller.show_message("Sucesso", f"Usuário {user} registrado!"); self.controller.show_frame(LoginPage)

class MainHubPage(ctk.CTkFrame):
    """O menu principal do usuário, onde ele escolhe o jogo."""
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#242424"); self.controller = controller
        top_frame = ctk.CTkFrame(self, corner_radius=0); top_frame.pack(fill="x")
        self.welcome_label = ctk.CTkLabel(top_frame, text="", font=ctk.CTkFont(size=20, weight="bold")); self.welcome_label.pack(pady=(20, 5), padx=20, anchor="w")
        self.balance_label = ctk.CTkLabel(top_frame, text="", font=ctk.CTkFont(size=16)); self.balance_label.pack(pady=(0, 10), padx=20, anchor="w")
        self.ref_code_label = ctk.CTkLabel(top_frame, text="", font=ctk.CTkFont(size=12, slant="italic"), text_color="gray"); self.ref_code_label.pack(pady=(0, 20), padx=20, anchor="w")
        games_frame = ctk.CTkScrollableFrame(self, fg_color="transparent"); games_frame.pack(pady=10, padx=15, fill="both", expand=True)
        ctk.CTkLabel(games_frame, text="Escolha um Jogo", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        game_buttons = [("🃏 Blackjack", BlackjackGame, "#c0392b"), ("🌀 Roleta", RouletteGame, "#8e44ad"), ("✈️ Aviãozinho (Crash)", CrashGame, "#f39c12")]
        for name, frame, color in game_buttons:
            ctk.CTkButton(games_frame, text=name, font=ctk.CTkFont(size=16), height=60, fg_color=color, hover_color=self.darken_color(color), command=lambda f=frame: controller.show_frame(f)).pack(pady=10, fill="x")
        action_frame = ctk.CTkFrame(self, fg_color="transparent"); action_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(action_frame, text="💰 Adicionar Saldo", fg_color="#1abc9c", hover_color="#16a085", command=self.add_balance).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(action_frame, text="Sair", fg_color="#e67e22", hover_color="#d35400", command=controller.logout).pack(side="right", expand=True, padx=5)

    def on_show(self, data=None): self.update_info()
    def darken_color(self, c):
        r,g,b = int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
        return f"#{max(0,r-20):02x}{max(0,g-20):02x}{max(0,b-20):02x}"
    def update_info(self):
        """Busca os dados do usuário no DB e atualiza os textos na tela."""
        user_data = get_user_data(self.controller.current_user)
        if user_data:
            self.welcome_label.configure(text=f"Olá, {self.controller.current_user}!")
            self.balance_label.configure(text=f"Saldo: ${user_data['balance']:,.2f}", text_color="#4CAF50")
            self.ref_code_label.configure(text=f"Seu código: {user_data['referral_code']}")

    def add_balance(self):
        """Adiciona saldo fictício à conta do usuário."""
        amount = CustomInputDialog(self, title="Adicionar Saldo", text="Quanto saldo fictício deseja adicionar?").get_input()
        if amount and amount > 0:
            self.controller.update_user_balance_db(amount)
            log_transaction(self.controller.current_user, 'deposito', amount) # Registra o depósito no log.
            self.controller.show_message("Sucesso", f"${amount} adicionados!")
            self.update_info()

class AdminPage(ctk.CTkFrame):
    """O painel de controle do administrador."""
    def __init__(self, parent, controller):
        super().__init__(parent); self.controller = controller
        ctk.CTkLabel(self, text="PUROBET ADMIN", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)
        self.tab_view = ctk.CTkTabview(self); self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_users = self.tab_view.add("Usuários"); self.tab_odds = self.tab_view.add("Odds")
        self.tab_stats = self.tab_view.add("Estatísticas"); self.tab_logs = self.tab_view.add("📊 Logs")
        
        # --- Aba de Usuários ---
        self.user_scroll_frame = ctk.CTkScrollableFrame(self.tab_users, label_text="Lista de Usuários")
        self.user_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- Aba de Odds ---
        ctk.CTkLabel(self.tab_odds, text="Pagamento Roleta (Número):").pack(pady=(10,0), padx=10)
        self.roulette_payout = ctk.CTkSlider(self.tab_odds, from_=10, to=50, number_of_steps=40); self.roulette_payout.pack(fill="x", padx=10)
        self.roulette_payout_label = ctk.CTkLabel(self.tab_odds, text=""); self.roulette_payout.bind("<ButtonRelease-1>", self.update_slider_label); self.roulette_payout_label.pack()
        ctk.CTkButton(self.tab_odds, text="Salvar Odds", command=self.save_odds).pack(pady=20)
        
        # --- Aba de Estatísticas ---
        self.stats_frame = ctk.CTkFrame(self.tab_stats, fg_color="transparent"); self.stats_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.total_users_label = ctk.CTkLabel(self.stats_frame, font=ctk.CTkFont(size=16)); self.total_users_label.pack(anchor="w", padx=10, pady=5)
        self.total_balance_label = ctk.CTkLabel(self.stats_frame, font=ctk.CTkFont(size=16)); self.total_balance_label.pack(anchor="w", padx=10, pady=5)
        
        # --- Aba de Logs ---
        log_filter_frame = ctk.CTkFrame(self.tab_logs); log_filter_frame.pack(fill="x", padx=5, pady=5)
        self.log_search_entry = ctk.CTkEntry(log_filter_frame, placeholder_text="Filtrar por usuário..."); self.log_search_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.log_search_entry.bind("<Return>", self.refresh_logs) # Permite buscar com a tecla Enter.
        ctk.CTkButton(log_filter_frame, text="Buscar", command=self.refresh_logs).pack(side="left")
        self.log_tab_view = ctk.CTkTabview(self.tab_logs); self.log_tab_view.pack(fill="both", expand=True, padx=5, pady=5)
        self.bet_logs_tab = self.log_tab_view.add("Apostas"); self.trans_logs_tab = self.log_tab_view.add("Transações")
        self.bet_logs_scroll = ctk.CTkScrollableFrame(self.bet_logs_tab); self.bet_logs_scroll.pack(fill="both", expand=True)
        self.trans_logs_scroll = ctk.CTkScrollableFrame(self.trans_logs_tab); self.trans_logs_scroll.pack(fill="both", expand=True)
        
        ctk.CTkButton(self, text="Logout", fg_color="#e67e22", hover_color="#d35400", command=controller.logout).pack(pady=10)

    def on_show(self, data=None): self.refresh_all_tabs()
    def refresh_all_tabs(self):
        """Atualiza os dados de todas as abas do painel de admin."""
        self.refresh_users(); self.refresh_stats(); self.refresh_odds(); self.refresh_logs()

    def refresh_users(self):
        for widget in self.user_scroll_frame.winfo_children(): widget.destroy()
        for user, balance in get_all_users():
            uf = ctk.CTkFrame(self.user_scroll_frame); uf.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(uf, text=f"{user} - Saldo: ${balance:.2f}").pack(side="left", padx=10)
            bf = ctk.CTkFrame(uf, fg_color="transparent"); bf.pack(side="right")
            ctk.CTkButton(bf, text="+", width=30, fg_color="#27ae60", command=lambda u=user: self.add_balance_admin(u)).pack(side="left", padx=2)
            ctk.CTkButton(bf, text="-", width=30, fg_color="#c0392b", command=lambda u=user: self.remove_balance_admin(u)).pack(side="left", padx=2)
            ctk.CTkButton(bf, text="🗑️", width=30, fg_color="#7f8c8d", command=lambda u=user: self.delete_user(u)).pack(side="left", padx=2)
    
    def refresh_stats(self):
        all_users = get_all_users()
        self.total_users_label.configure(text=f"Total de usuários: {len(all_users)}")
        self.total_balance_label.configure(text=f"Saldo total em jogo: ${sum(b for u,b in all_users):,.2f}")

    def refresh_odds(self):
        self.roulette_payout.set(get_game_setting('roulette_payout_number')); self.update_slider_label()

    def refresh_logs(self, event=None):
        user_filter = self.log_search_entry.get() or None
        for widget in self.bet_logs_scroll.winfo_children(): widget.destroy()
        for log in get_logs('bet_logs', user_filter):
            _, user, game, bet, outcome, ts = log
            color = "#4CAF50" if outcome >= 0 else "#D32F2F"
            log_text = f"[{ts}] {user} | {game}: apostou ${bet:.2f}, resultado ${outcome:+.2f}"
            ctk.CTkLabel(self.bet_logs_scroll, text=log_text, text_color=color, anchor="w").pack(fill="x")
        
        for widget in self.trans_logs_scroll.winfo_children(): widget.destroy()
        for log in get_logs('transaction_logs', user_filter):
            _, user, type, amount, ts = log
            log_text = f"[{ts}] {user} | {type.replace('_', ' ').capitalize()}: ${amount:,.2f}"
            ctk.CTkLabel(self.trans_logs_scroll, text=log_text, anchor="w").pack(fill="x")

    def add_balance_admin(self, user):
        amount = CustomInputDialog(self, title="Adicionar Saldo", text=f"Adicionar para {user}:").get_input()
        if amount and amount > 0: update_balance(user, amount); log_transaction(user, 'deposito_admin', amount); self.refresh_users(); self.refresh_stats()
    def remove_balance_admin(self, user):
        amount = CustomInputDialog(self, title="Remover Saldo", text=f"Remover de {user}:").get_input()
        if amount and amount > 0: update_balance(user, -amount); log_transaction(user, 'saque_admin', -amount); self.refresh_users(); self.refresh_stats()
    def delete_user(self, user):
        from tkinter import messagebox
        if messagebox.askyesno("Confirmar", f"Excluir {user}?"): delete_user_db(user); self.refresh_users(); self.refresh_stats()
    def update_slider_label(self, event=None): self.roulette_payout_label.configure(text=f"{int(self.roulette_payout.get())}x")
    def save_odds(self): set_game_setting('roulette_payout_number', int(self.roulette_payout.get())); self.controller.show_message("Sucesso", "Odds atualizadas!")

# --- SEÇÃO 5: TELAS DOS JOGOS ---

class BaseGamePage(ctk.CTkFrame):
    """Classe base para todas as telas de jogos, para evitar repetição de código."""
    def __init__(self, parent, controller, game_title):
        super().__init__(parent); self.controller = controller; self._after_id = None
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=1)
        top_frame = ctk.CTkFrame(self, fg_color="transparent"); top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        top_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(top_frame, text="← Voltar ao Hub", width=120, command=lambda: controller.show_frame(MainHubPage)).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(top_frame, text=game_title, font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=1, sticky="ew")
        self.balance_label = ctk.CTkLabel(top_frame, text="", font=ctk.CTkFont(size=14)); self.balance_label.grid(row=0, column=2, sticky="e", padx=10)
        self.game_frame = ctk.CTkFrame(self); self.game_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    def on_show(self, data=None): self.update_balance_display()
    def on_hide(self):
        if self._after_id: self.after_cancel(self._after_id); self._after_id = None
    def update_balance_display(self, change=0):
        balance = self.controller.get_user_balance()
        self.balance_label.configure(text=f"Saldo: ${balance:,.2f}")
        if change != 0:
            color = "#4CAF50" if change > 0 else "#D32F2F"
            self.balance_label.configure(text_color=color)
            self.after(1000, lambda: self.balance_label.configure(text_color="white"))

class BlackjackGame(BaseGamePage):
    """A tela e lógica do jogo Blackjack (21)."""
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "🃏 Blackjack")
        self.deck = []; self.player_hand, self.dealer_hand = [], []; self.bet_amount = 0
        self.game_frame.grid_rowconfigure([0, 1], weight=1); self.game_frame.grid_columnconfigure(0, weight=1)
        self.dealer_frame = ctk.CTkFrame(self.game_frame); self.dealer_frame.grid(row=0, column=0, sticky="nsew", pady=5)
        self.player_frame = ctk.CTkFrame(self.game_frame); self.player_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        self.dealer_score_label = ctk.CTkLabel(self.dealer_frame, text="Dealer: 0", font=ctk.CTkFont(size=16)); self.dealer_score_label.place(relx=0.02, rely=0.05)
        self.player_score_label = ctk.CTkLabel(self.player_frame, text="Você: 0", font=ctk.CTkFont(size=16)); self.player_score_label.place(relx=0.02, rely=0.05)
        self.status_label = ctk.CTkLabel(self, text="Faça sua aposta para começar", font=ctk.CTkFont(size=14)); self.status_label.grid(row=2, column=0, pady=5)
        controls_container = ctk.CTkFrame(self); controls_container.grid(row=3, column=0, sticky="ew", padx=10, pady=10); controls_container.grid_columnconfigure(0, weight=1)
        bet_frame = ctk.CTkFrame(controls_container, fg_color="transparent"); bet_frame.grid(row=0, column=0, pady=5)
        self.bet_entry = ctk.CTkEntry(bet_frame, placeholder_text="Aposta", width=100); self.bet_entry.pack(side="left", padx=5)
        self.deal_button = ctk.CTkButton(bet_frame, text="Apostar", command=self.deal); self.deal_button.pack(side="left", padx=5)
        game_actions_frame = ctk.CTkFrame(controls_container, fg_color="transparent"); game_actions_frame.grid(row=1, column=0, pady=5)
        self.hit_button = ctk.CTkButton(game_actions_frame, text="Pedir", command=self.hit, state="disabled"); self.hit_button.pack(side="left", padx=10)
        self.stand_button = ctk.CTkButton(game_actions_frame, text="Parar", command=self.stand, state="disabled", fg_color="#c0392b", hover_color="#a52a1a"); self.stand_button.pack(side="left", padx=10)
    
    def on_show(self, data=None): super().on_show(data); self.reset_game()
    def get_card_value(self, card):
        rank = card.split('_')[1]
        if rank in ['J', 'Q', 'K', 'T']: return 10
        if rank == 'A': return 11
        return int(rank)
    def get_hand_value(self, hand):
        value = sum(self.get_card_value(c) for c in hand); num_aces = sum(1 for c in hand if c.endswith('_A'))
        while value > 21 and num_aces: value -= 10; num_aces -= 1
        return value
    def create_deck(self):
        suits = ['hearts', 'diamonds', 'clubs', 'spades']; ranks = [str(i) for i in range(2, 10)] + ['T', 'J', 'Q', 'K', 'A']
        self.deck = [f"{s}_{r}" for s in suits for r in ranks]; random.shuffle(self.deck)
    def deal(self):
        try: bet = int(self.bet_entry.get())
        except (ValueError, TypeError): self.controller.show_message("Erro", "Aposta inválida."); return
        if not (0 < bet <= self.controller.get_user_balance()): self.controller.show_message("Erro", "Saldo insuficiente."); return
        self.bet_amount = bet; self.controller.update_user_balance_db(-bet); self.update_balance_display(-bet)
        self.create_deck(); self.player_hand = [self.deck.pop(), self.deck.pop()]; self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        self.update_ui(); self.status_label.configure(text=f"Aposta: ${self.bet_amount}. Sua vez.")
        self.deal_button.configure(state="disabled"); self.hit_button.configure(state="normal"); self.stand_button.configure(state="normal")
        if self.get_hand_value(self.player_hand) == 21: self.stand()
    def hit(self):
        self.player_hand.append(self.deck.pop()); self.update_ui()
        if self.get_hand_value(self.player_hand) > 21: self.end_game("Você estourou! Perdeu.")
    def stand(self):
        self.hit_button.configure(state="disabled"); self.stand_button.configure(state="disabled")
        while self.get_hand_value(self.dealer_hand) < 17: self.dealer_hand.append(self.deck.pop())
        player_score, dealer_score = self.get_hand_value(self.player_hand), self.get_hand_value(self.dealer_hand)
        self.update_ui(show_dealer_full=True)
        if dealer_score > 21 or player_score > dealer_score: self.end_game("Você ganhou!", self.bet_amount * 2)
        elif player_score < dealer_score: self.end_game("Você perdeu.")
        else: self.end_game("Empate!", self.bet_amount)
    def end_game(self, message, winnings=0):
        self.status_label.configure(text=message)
        self.controller.update_user_balance_db(winnings, game_name="Blackjack", bet_amount=self.bet_amount)
        if winnings > 0: self.update_balance_display(winnings - self.bet_amount)
        else: self.update_balance_display(0)
        self.deal_button.configure(state="normal"); self.hit_button.configure(state="disabled"); self.stand_button.configure(state="disabled")
    def update_ui(self, show_dealer_full=False):
        for widget in self.player_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and hasattr(widget, "is_card"): widget.destroy()
        for widget in self.dealer_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and hasattr(widget, "is_card"): widget.destroy()
        for i, card_name in enumerate(self.player_hand):
            card_img = self.controller.card_loader.get(card_name)
            if card_img:
                card_label = ctk.CTkLabel(self.player_frame, image=card_img, text=""); card_label.is_card = True
                card_label.place(relx=0.25 + i*0.1, rely=0.5, anchor="center")
        if self.dealer_hand:
            dealer_hand_to_show = self.dealer_hand if show_dealer_full else [self.dealer_hand[0], 'back']
            for i, card_name in enumerate(dealer_hand_to_show):
                card_img = self.controller.card_loader.get(card_name)
                if card_img:
                    card_label = ctk.CTkLabel(self.dealer_frame, image=card_img, text=""); card_label.is_card = True
                    card_label.place(relx=0.25 + i*0.1, rely=0.5, anchor="center")
        self.player_score_label.configure(text=f"Você: {self.get_hand_value(self.player_hand)}")
        if self.dealer_hand:
            dealer_score = self.get_hand_value(self.dealer_hand) if show_dealer_full else self.get_card_value(self.dealer_hand[0])
            self.dealer_score_label.configure(text=f"Dealer: {dealer_score}{'' if show_dealer_full else ' + ?'}")
        else: self.dealer_score_label.configure(text="Dealer: 0")
    def reset_game(self):
        self.player_hand, self.dealer_hand = [], []; self.update_ui()
        self.status_label.configure(text="Faça sua aposta para começar"); self.deal_button.configure(state="normal")
        self.hit_button.configure(state="disabled"); self.stand_button.configure(state="disabled"); self.bet_entry.delete(0, 'end')
        self.player_score_label.configure(text="Você: 0"); self.dealer_score_label.configure(text="Dealer: 0")

class RouletteGame(BaseGamePage):
    """A tela e a lógica do jogo da Roleta."""
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "🌀 Roleta")
        self.numbers = {n: c for n, c in zip(range(37), (['green'] + ['red', 'black'] * 18))}
        self.color_map = {"red": "#C0392B", "black": "#2C3E50", "green": "#27AE60"}
        self.history = []; self.bets = []
        self.translation_map = {'red':'Vermelho','black':'Preto','even':'Par','odd':'Ímpar','low':'1-18 (Menores)','high':'19-36 (Maiores)'}
        self.game_frame.grid_columnconfigure(0, weight=2); self.game_frame.grid_columnconfigure(1, weight=1); self.game_frame.grid_rowconfigure(0, weight=1)
        board_panel = ctk.CTkFrame(self.game_frame, fg_color="transparent"); board_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        board_panel.grid_rowconfigure(1, weight=1); board_panel.grid_columnconfigure(0, weight=1)
        outside_bets_frame = ctk.CTkFrame(board_panel); outside_bets_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        outside_bets_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        ctk.CTkButton(outside_bets_frame, text="1-18", command=lambda: self.add_bet('range', 'low')).grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        ctk.CTkButton(outside_bets_frame, text="Par", command=lambda: self.add_bet('parity', 'even')).grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        ctk.CTkButton(outside_bets_frame, text="Vermelho", fg_color=self.color_map['red'], command=lambda: self.add_bet('color', 'red')).grid(row=0, column=2, sticky="ew", padx=2, pady=2)
        ctk.CTkButton(outside_bets_frame, text="Preto", fg_color=self.color_map['black'], text_color="white", command=lambda: self.add_bet('color', 'black')).grid(row=0, column=3, sticky="ew", padx=2, pady=2)
        ctk.CTkButton(outside_bets_frame, text="Ímpar", command=lambda: self.add_bet('parity', 'odd')).grid(row=0, column=4, sticky="ew", padx=2, pady=2)
        ctk.CTkButton(outside_bets_frame, text="19-36", command=lambda: self.add_bet('range', 'high')).grid(row=0, column=5, sticky="ew", padx=2, pady=2)
        number_grid_frame = ctk.CTkScrollableFrame(board_panel, label_text="Apostar em Números"); number_grid_frame.grid(row=1, column=0, sticky="nsew")
        for i in range(37):
            btn = ctk.CTkButton(number_grid_frame, text=str(i), fg_color=self.color_map[self.numbers[i]], width=40, command=lambda n=i: self.add_bet('number', n))
            btn.grid(row=(i//6), column=i%6, padx=2, pady=2)
        control_panel = ctk.CTkFrame(self.game_frame); control_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        control_panel.grid_columnconfigure(0, weight=1); control_panel.grid_rowconfigure(2, weight=1)
        self.result_label = ctk.CTkLabel(control_panel, text="?", font=ctk.CTkFont(size=60, weight="bold"), fg_color="grey", height=120, corner_radius=10)
        self.result_label.grid(row=0, column=0, sticky="ew", pady=10, padx=10)
        self.history_frame = ctk.CTkFrame(control_panel, fg_color="transparent"); self.history_frame.grid(row=1, column=0, pady=5, padx=10)
        self.bets_scroll_frame = ctk.CTkScrollableFrame(control_panel, label_text="Suas Apostas"); self.bets_scroll_frame.grid(row=2, column=0, sticky="nsew", pady=5, padx=10)
        self.total_bet_label = ctk.CTkLabel(control_panel, text="Aposta Total: $0"); self.total_bet_label.grid(row=3, column=0, pady=5, padx=10)
        self.spin_button = ctk.CTkButton(control_panel, text="Girar!", command=self.spin, state="disabled", height=40); self.spin_button.grid(row=4, column=0, sticky="ew", pady=(5,2), padx=10)
        self.clear_bets_button = ctk.CTkButton(control_panel, text="Limpar Apostas", fg_color="grey", command=self.clear_bets); self.clear_bets_button.grid(row=5, column=0, sticky="ew", pady=(2,10), padx=10)
    def on_show(self, data=None): super().on_show(data); self.clear_bets()
    def add_bet(self, bet_type, value):
        display_value = self.translation_map.get(value, str(value))
        amount = CustomInputDialog(self, title="Valor da Aposta", text=f"Apostar em {display_value}:").get_input()
        if amount and amount > 0:
            if amount > self.controller.get_user_balance() - sum(b['amount'] for b in self.bets): self.controller.show_message("Erro", "Saldo insuficiente."); return
            self.bets.append({'type': bet_type, 'value': value, 'amount': amount}); self.update_bets_display()
    def update_bets_display(self):
        for widget in self.bets_scroll_frame.winfo_children(): widget.destroy()
        total = sum(b['amount'] for b in self.bets)
        for bet in self.bets:
            display_value = self.translation_map.get(bet['value'], str(bet['value']))
            ctk.CTkLabel(self.bets_scroll_frame, text=f"{display_value}: ${bet['amount']}").pack(anchor="w", padx=5)
        self.total_bet_label.configure(text=f"Aposta Total: ${total}"); self.spin_button.configure(state="normal" if total > 0 else "disabled")
    def clear_bets(self): self.bets.clear(); self.update_bets_display()
    def spin(self):
        total_bet = sum(b['amount'] for b in self.bets)
        if total_bet <= 0: return
        self.controller.update_user_balance_db(-total_bet); self.update_balance_display(-total_bet)
        self.spin_button.configure(state="disabled"); self.clear_bets_button.configure(state="disabled")
        self.animate_spin(random.randint(0, 36), 20, 50)
    def animate_spin(self, winning_num, steps, delay):
        if steps > 0:
            num = random.randint(0, 36); self.result_label.configure(text=str(num), fg_color=self.color_map[self.numbers[num]])
            self._after_id = self.after(delay, lambda: self.animate_spin(winning_num, steps - 1, int(delay * 1.15)))
        else:
            self.result_label.configure(text=str(winning_num), fg_color=self.color_map[self.numbers[winning_num]])
            total_winnings = self.calculate_winnings(winning_num)
            self.controller.update_user_balance_db(total_winnings, game_name="Roleta", bet_amount=sum(b['amount'] for b in self.bets))
            if total_winnings > 0: self.update_balance_display(total_winnings); self.controller.show_message("Você Ganhou!", f"Parabéns! Você ganhou ${total_winnings:,.2f}!")
            else: self.controller.show_message("Não foi desta vez", "Mais sorte na próxima rodada!")
            self.history.append(winning_num); self.update_history(); self.clear_bets(); self.clear_bets_button.configure(state="normal")
    def calculate_winnings(self, wn):
        total_winnings, wc, is_even, is_low = 0, self.numbers[wn], (wn % 2 == 0 and wn != 0), (1 <= wn <= 18)
        for bet in self.bets:
            payout = 0
            if bet['type'] == 'number' and bet['value'] == wn: payout = get_game_setting('roulette_payout_number')
            elif bet['type'] == 'color' and bet['value'] == wc: payout = 2
            elif bet['type'] == 'parity' and ((bet['value'] == 'even' and is_even) or (bet['value'] == 'odd' and not is_even)): payout = 2
            elif bet['type'] == 'range' and ((bet['value'] == 'low' and is_low) or (bet['value'] == 'high' and not is_low)): payout = 2
            if payout > 0: total_winnings += bet['amount'] * payout
        return total_winnings
    def update_history(self):
        for widget in self.history_frame.winfo_children(): widget.destroy()
        hist_row = ctk.CTkFrame(self.history_frame, fg_color="transparent"); hist_row.pack()
        for num in self.history[-10:]: ctk.CTkLabel(hist_row, text=str(num), fg_color=self.color_map[self.numbers[num]], corner_radius=5, width=28, height=28).pack(side="left", padx=2)

class CardImageLoader:
    """
    Classe Singleton para carregar e armazenar em cache as imagens.
    Agora lida com CTkImage (para widgets CTk) e PhotoImage (para o Canvas).
    """
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CardImageLoader, cls).__new__(cls)
            cls._instance.ctk_cache = {}
            cls._instance.photo_cache = {} # Cache separado para PhotoImage
        return cls._instance

    def get_ctk_image(self, card_name="back"):
        """Retorna um objeto CTkImage, ideal para widgets CustomTkinter."""
        if card_name in self.ctk_cache:
            return self.ctk_cache[card_name]

        rank_map = {'A': 'ace', 'K': 'king', 'Q': 'queen', 'J': 'jack', 'T': '10'}
        
        if card_name == "back":
            filepath = os.path.join("cards", "back.png")
        else:
            suit, rank = card_name.split('_')
            rank_str = rank_map.get(rank, rank)
            filename = f"{rank_str}_of_{suit}.png"
            filepath = os.path.join("cards", filename)
        
        try:
            img = Image.open(filepath)
            img = img.resize((70, 100), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(70, 100))
            self.ctk_cache[card_name] = ctk_img
            return ctk_img
        except FileNotFoundError:
            print(f"ERRO: Imagem não encontrada em {filepath}.")
            return None

    def get_photo_image(self, name, size=(80, 50)):
        """Retorna um objeto PhotoImage, necessário para o Canvas do Tkinter."""
        if name in self.photo_cache:
            return self.photo_cache[name]

        filepath = os.path.join("cards", f"{name}.png")
        try:
            img = Image.open(filepath).resize(size, Image.LANCZOS)
            photo_img = ImageTk.PhotoImage(img)
            self.photo_cache[name] = photo_img
            return photo_img
        except FileNotFoundError:
            print(f"ERRO: Imagem '{name}.png' não encontrada.")
            return None


class CrashGame(BaseGamePage):
    """A tela e a lógica do jogo Crash (Aviãozinho)."""
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "✈️ Aviãozinho")
        self.game_state = "waiting"
        self.multiplier = 1.0
        self.crash_point = 1.0
        self.bet_amount = 0
        self.cashed_out = False
        self.start_time = 0
        self.graph_points = []
        self.history = []
        # Mantém a referência da imagem do avião para o Canvas
        self.plane_photoimage = None

        # Layout com Grid
        self.game_frame.grid_columnconfigure(0, weight=3)
        self.game_frame.grid_columnconfigure(1, weight=1)
        self.game_frame.grid_rowconfigure(0, weight=1)

        # PAINEL DA ESQUERDA: GRÁFICO
        self.canvas = Canvas(self.game_frame, bg="#2B2B2B", bd=0, highlightthickness=0, relief='ridge')
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.canvas.bind("<Configure>", self.draw_graph)

        # PAINEL DA DIREITA: CONTROLES
        control_panel = ctk.CTkFrame(self.game_frame)
        control_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        control_panel.grid_columnconfigure(0, weight=1)
        control_panel.grid_rowconfigure(3, weight=1)
        
        bet_frame = ctk.CTkFrame(control_panel, fg_color="transparent")
        bet_frame.grid(row=0, column=0, pady=10, padx=10, sticky="ew")
        self.bet_entry = ctk.CTkEntry(bet_frame, placeholder_text="Aposta")
        self.bet_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.bet_button = ctk.CTkButton(bet_frame, text="Apostar", command=self.place_bet, width=100)
        self.bet_button.pack(side="left")
        
        self.cashout_button = ctk.CTkButton(control_panel, text="Sacar!", font=ctk.CTkFont(size=18, weight="bold"), height=50, state="disabled", fg_color="#10a37f", hover_color="#0e8e6f", command=self.cash_out)
        self.cashout_button.grid(row=1, column=0, sticky="ew", pady=10, padx=10)

        self.status_label = ctk.CTkLabel(control_panel, text="", font=ctk.CTkFont(size=16))
        self.status_label.grid(row=2, column=0, pady=10, padx=10)

        self.history_frame = ctk.CTkScrollableFrame(control_panel, label_text="Histórico")
        self.history_frame.grid(row=3, column=0, sticky="nsew", pady=10, padx=10)
    
    def on_show(self, data=None):
        super().on_show(data)
        self.reset_round()

    def place_bet(self):
        if self.game_state != "waiting":
            self.controller.show_message("Aviso", "Aguarde a próxima rodada.")
            return
        try: bet = int(self.bet_entry.get())
        except (ValueError, TypeError): self.controller.show_message("Erro", "Aposta inválida."); return
        if not (0 < bet <= self.controller.get_user_balance()):
            self.controller.show_message("Erro", "Saldo insuficiente.")
            return
        self.bet_amount = bet
        self.controller.update_user_balance_db(-bet)
        self.update_balance_display(-bet)
        self.status_label.configure(text=f"Aposta de ${self.bet_amount:,.2f} feita!")
        self.bet_button.configure(state="disabled")

    def cash_out(self):
        if self.game_state == "running" and not self.cashed_out:
            self.cashed_out = True
            winnings = self.bet_amount * self.multiplier
            self.controller.update_user_balance_db(winnings, game_name="Crash", bet_amount=self.bet_amount)
            self.update_balance_display(winnings)
            self.status_label.configure(text=f"Você sacou com {self.multiplier:.2f}x!")
            self.cashout_button.configure(state="disabled", text=f"GANHOU R$ {winnings:,.2f}")

    def game_loop(self):
        if self.game_state == "running":
            elapsed_time = time.time() - self.start_time
            self.multiplier = math.pow(1.05, elapsed_time)
            
            if self.bet_amount > 0 and not self.cashed_out:
                potential_winnings = self.bet_amount * self.multiplier
                self.cashout_button.configure(text=f"Sacar R$ {potential_winnings:,.2f}")

            if self.multiplier >= self.crash_point:
                self.game_state = "crashed"
                self.history.append(self.crash_point)
                self.update_history()
                if self.bet_amount > 0 and not self.cashed_out:
                    self.status_label.configure(text=f"CRASH! Você perdeu.")
                    log_bet(self.controller.current_user, "Crash", self.bet_amount, 0)
                else:
                    self.status_label.configure(text=f"CRASH em {self.crash_point:.2f}x")
                self.cashout_button.configure(state="disabled")
                self.draw_graph(crashed=True)
                self._after_id = self.after(3000, self.reset_round)
            else:
                self.draw_graph()
                self._after_id = self.after(30, self.game_loop)

    def start_running(self):
        self.game_state = "running"
        self.start_time = time.time()
        self.crash_point = max(1.01, random.gammavariate(2, 2))
        if self.bet_amount > 0: self.cashout_button.configure(state="normal")
        self.game_loop()

    def reset_round(self):
        self.game_state = "waiting"; self.multiplier = 1.0; self.bet_amount = 0
        self.cashed_out = False; self.graph_points = []
        self.bet_button.configure(state="normal"); self.cashout_button.configure(state="disabled", text="Sacar!")
        self.bet_entry.delete(0, 'end'); self.draw_graph(); self.countdown(5)

    def countdown(self, count):
        if self._after_id: self.after_cancel(self._after_id)
        if count > 0:
            self.status_label.configure(text=f"Próxima rodada em {count}...")
            self.draw_graph(); self._after_id = self.after(1000, lambda: self.countdown(count - 1))
        else: self.status_label.configure(text=""); self.start_running()

    def update_history(self):
        for widget in self.history_frame.winfo_children(): widget.destroy()
        for m in reversed(self.history[-10:]): 
            ctk.CTkLabel(self.history_frame, text=f"{m:.2f}x", text_color="#4CAF50" if m >= 2.0 else "#D32F2F", anchor="w").pack(fill="x")

    def draw_graph(self, event=None, crashed=False):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 20 or h < 20: return

        start_x, start_y = w * 0.05, h * 0.95
        line_color_bg = "#303030"
        for i in range(1, 15):
            angle = math.radians(i * 6); end_x = start_x + math.cos(angle) * w * 2
            end_y = start_y - math.sin(angle) * h * 2
            self.canvas.create_line(start_x, start_y, end_x, end_y, fill=line_color_bg, width=1)
        
        for i in range(1, 5):
            self.canvas.create_line(0, h-i*h/5, w, h-i*h/5, fill="#404040", dash=(2,2))

        elapsed_time = (time.time() - self.start_time) if self.game_state == "running" else 0
        max_mult = max(2.0, self.multiplier * 1.2, self.crash_point * 1.1)
        max_time = max(5.0, elapsed_time * 1.2)
        
        self.graph_points = [(0, h)]
        for t_ms in range(int(elapsed_time * 100) + 1):
            t = t_ms / 100.0; current_mult = math.pow(1.05, t)
            x = (t / max_time) * w; y = h - ((current_mult - 1) / (max_mult - 1)) * h 
            x = max(0, min(w, x)); y = max(0, min(h, y))
            self.graph_points.append((x, y))

        line_color = "#D32F2F" if crashed else "#E74C3C"
        
        if len(self.graph_points) > 1:
            polygon_points = list(self.graph_points)
            polygon_points.append((self.graph_points[-1][0], h)); polygon_points.append((self.graph_points[0][0], h))
            self.canvas.create_polygon(polygon_points, fill=line_color, outline="")
            self.canvas.create_line(self.graph_points, fill=line_color, width=4, smooth=True)

        mult_text = f"{self.crash_point:.2f}x" if crashed else f"{self.multiplier:.2f}x"
        font_size = min(max(int(h / 5), 30), 100)
        self.canvas.create_text(w/2, h/2, text=mult_text, font=("Roboto", font_size, "bold"), fill="white", anchor="center")

        if self.game_state == "running" or crashed:
            # --- CORREÇÃO: Usar get_photo_image e guardar a referência ---
            self.plane_photoimage = self.controller.card_loader.get_photo_image("plane", size=(80, 50))
            if self.plane_photoimage and self.graph_points:
                plane_x, plane_y = self.graph_points[-1]
                self.canvas.create_image(plane_x, plane_y, image=self.plane_photoimage, anchor="center")

#
# --- SEÇÃO 6: EXECUÇÃO DA APLICAÇÃO ---

if __name__ == "__main__":
    # Esta é a função principal que roda quando o script é executado.
    init_db()          # 1. Inicializa o banco de dados, criando o arquivo e as tabelas se necessário.
    app = PurobetApp() # 2. Cria a instância da aplicação principal.
    app.mainloop()     # 3. Inicia o loop de eventos da interface gráfica, que a mantém rodando e responsiva.