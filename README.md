<div align="center">
  <h3 align="center">PUROBET 🎰</h3>

  <p align="center">
    Um cassino fictício com múltiplos jogos e gerenciamento de usuários.
    <br />
    <strong>Desenvolvido para fins de estudo e diversão!</strong>
  </p>
</div>

---

## 🎲 Sobre o projeto

O **PUROBET** é uma aplicação de cassino fictício que simula jogos populares como:

- 🃏 **Blackjack (21)**
- 🌀 **Roleta**
- ✈️ **Crash (Aviãozinho)**

Além disso, conta com:
- Sistema de **login e registro de usuários** com senha criptografada.
- Banco de dados **SQLite** para armazenar usuários, transações e apostas.
- Painel **Admin** para visualizar estatísticas, gerenciar usuários e configurar odds.
- Interface gráfica moderna utilizando **CustomTkinter**.

---

## 🛠️ Construído com

[![My Skills](https://skillicons.dev/icons?i=python,sqlite)](https://skillicons.dev)

* [Python 3](https://www.python.org/)
* [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
* [Pillow](https://python-pillow.org/) (para manipulação de imagens)
* [SQLite](https://www.sqlite.org/)

---

## 🚀 Iniciando

Siga os passos abaixo para instalar e rodar o projeto localmente.

### 📋 Pré-requisitos

- [Python 3](https://www.python.org/downloads/) instalado
- Instalar as bibliotecas necessárias:
  ```sh
  pip install customtkinter Pillow
  ```

---

### ⚙️ Instalação

1. Clone o repositório
   ```sh
   git clone https://github.com/luizjs/purobet.git
   cd purobet
   ```

2. Execute o projeto:
   ```sh
   python main.py
   ```

3. O banco de dados `purobet.db` será criado automaticamente na pasta raiz.

---

## 📂 Estrutura do Projeto

```
/purobet/
│── main.py          # Arquivo principal do projeto
│── purobet.db       # Banco de dados SQLite (criado na primeira execução)
│── /cards/          # Imagens das cartas e ícones do jogo
```

---

## 👤 Usuários e Acesso

- **Admin:**  
  Usuário: `puroadmin`  
  Senha: `123456`

- **Novos jogadores** podem se registrar na tela inicial.  
- Cada novo usuário recebe **$1000 fictícios** para apostar.  
- Existe um sistema de **código de convite** para bônus de indicação.  

---

## 📊 Funcionalidades do Admin

- Gerenciar usuários (adicionar/remover saldo, deletar contas).
- Configurar odds da roleta.
- Visualizar estatísticas gerais.
- Acompanhar **logs de apostas e transações** em tempo real.

---

## 🎮 Jogos Disponíveis

- **Blackjack (21):** jogue contra o dealer e tente chegar o mais próximo de 21.  
- **Roleta:** aposte em números, cores, par/ímpar e acompanhe o giro.  
- **Crash (Aviãozinho):** faça sua aposta e saque antes que o avião caia.  

---
