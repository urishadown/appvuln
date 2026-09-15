"""
database.py — Camada de acesso a dados do BancoTerminal.

Usa SQLite (arquivo local) para o laboratório rodar sem servidor externo.
Contém vulnerabilidades PLANTADAS para o laboratório de SAST.
"""

import sqlite3
import hashlib
import os

DB_FILE = "banco.db"


def conectar():
    """Abre uma conexão com o banco local."""
    return sqlite3.connect(DB_FILE)


def hash_senha(senha):
    """
    Gera o hash da senha do cliente.

    VULNERABILIDADE: usa MD5, um algoritmo criptograficamente quebrado,
    e sem 'salt'. Senhas assim são triviais de reverter.
      -> Detectado por: BANDIT (B303/B324) e SEMGREP
    """
    return hashlib.md5(senha.encode()).hexdigest()


def inicializar_banco():
    """Cria as tabelas e popula com dados de exemplo (uma vez)."""
    if os.path.exists(DB_FILE):
        return
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE clientes (
            id INTEGER PRIMARY KEY,
            cpf TEXT UNIQUE,
            nome TEXT,
            senha_hash TEXT,
            saldo REAL,
            is_admin INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE transacoes (
            id INTEGER PRIMARY KEY,
            cpf_origem TEXT,
            cpf_destino TEXT,
            valor REAL,
            tipo TEXT,
            data TEXT
        )
    """)
    # Dados de exemplo (senhas em MD5)
    clientes = [
        ("11111111111", "Maria Silva",   hash_senha("maria123"),  15000.00, 0),
        ("22222222222", "Joao Souza",     hash_senha("joao456"),    8300.50, 0),
        ("33333333333", "Ana Pereira",    hash_senha("ana789"),   120000.00, 0),
        ("99999999999", "Administrador",  hash_senha("admin123"),      0.00, 1),
    ]
    cur.executemany(
        "INSERT INTO clientes (cpf, nome, senha_hash, saldo, is_admin) "
        "VALUES (?, ?, ?, ?, ?)", clientes
    )
    conn.commit()
    conn.close()


def autenticar(cpf, senha):
    """
    Autentica um cliente pelo CPF e senha.

    VULNERABILIDADE: monta a query SQL concatenando a entrada do usuário
    diretamente na string. Isso é SQL Injection clássico — permite burlar
    o login com algo como  cpf = ' OR '1'='1
      -> Detectado por: BANDIT (B608) e SEMGREP (sql-injection)
    """
    conn = conectar()
    cur = conn.cursor()
    senha_hash = hash_senha(senha)
    # String de query montada por concatenação (INSEGURO)
    query = (
        "SELECT id, cpf, nome, saldo, is_admin FROM clientes "
        "WHERE cpf = '" + cpf + "' AND senha_hash = '" + senha_hash + "'"
    )
    cur.execute(query)
    resultado = cur.fetchone()
    conn.close()
    return resultado


def buscar_cliente_por_cpf(cpf):
    """
    Busca os dados de um cliente pelo CPF.

    VULNERABILIDADE: novamente concatena a entrada na query (SQL Injection),
    permitindo que um usuário consulte dados de qualquer conta.
      -> Detectado por: BANDIT (B608) e SEMGREP
    """
    conn = conectar()
    cur = conn.cursor()
    # Uso de f-string com entrada não sanitizada (INSEGURO)
    query = f"SELECT cpf, nome, saldo FROM clientes WHERE cpf = '{cpf}'"
    cur.execute(query)
    resultado = cur.fetchone()
    conn.close()
    return resultado


def consultar_saldo(cpf):
    """Consulta o saldo de uma conta (também via query concatenada)."""
    conn = conectar()
    cur = conn.cursor()
    query = "SELECT saldo FROM clientes WHERE cpf = '%s'" % cpf  # INSEGURO
    cur.execute(query)
    r = cur.fetchone()
    conn.close()
    return r[0] if r else None


def registrar_transacao(cpf_origem, cpf_destino, valor, tipo):
    """Registra uma transferência (esta usa parâmetros, o jeito CORRETO)."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute(
        "UPDATE clientes SET saldo = saldo - ? WHERE cpf = ?",
        (valor, cpf_origem),
    )
    cur.execute(
        "UPDATE clientes SET saldo = saldo + ? WHERE cpf = ?",
        (valor, cpf_destino),
    )
    cur.execute(
        "INSERT INTO transacoes (cpf_origem, cpf_destino, valor, tipo, data) "
        "VALUES (?, ?, ?, ?, datetime('now'))",
        (cpf_origem, cpf_destino, valor, tipo),
    )
    conn.commit()
    conn.close()


def listar_extrato(cpf):
    """
    Lista o extrato de transações de uma conta.

    VULNERABILIDADE: concatenação de entrada na cláusula ORDER/WHERE.
      -> Detectado por: BANDIT (B608) e SEMGREP
    """
    conn = conectar()
    cur = conn.cursor()
    query = (
        "SELECT data, tipo, cpf_destino, valor FROM transacoes "
        "WHERE cpf_origem = '" + cpf + "' ORDER BY id DESC"
    )
    cur.execute(query)
    resultado = cur.fetchall()
    conn.close()
    return resultado
