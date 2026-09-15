"""
auth.py — Módulo de autenticação e sessão do BancoTerminal.

Contém vulnerabilidades PLANTADAS para o laboratório de SAST.
"""

import hashlib
import random
import base64
import json

from config import JWT_SECRET, ADMIN_DEFAULT_PASSWORD


def gerar_token_sessao(cpf, is_admin):
    """
    Gera um 'token' de sessão simplificado (pseudo-JWT) para o cliente.

    VULNERABILIDADE 1: a chave secreta (JWT_SECRET) está hardcoded no
    código (importada de config.py).
      -> Detectado por: GITLEAKS e BANDIT

    VULNERABILIDADE 2: usa MD5 para a assinatura.
      -> Detectado por: BANDIT (B303/B324) e SEMGREP
    """
    payload = {"cpf": cpf, "is_admin": is_admin}
    corpo = base64.b64encode(json.dumps(payload).encode()).decode()
    # Assinatura fraca com MD5 e segredo hardcoded
    assinatura = hashlib.md5((corpo + JWT_SECRET).encode()).hexdigest()
    return corpo + "." + assinatura


def gerar_codigo_2fa():
    """
    Gera o código de verificação em duas etapas (2FA) enviado ao cliente.

    VULNERABILIDADE: usa o módulo 'random' comum, que NÃO é
    criptograficamente seguro e é previsível. Para segurança deve-se
    usar o módulo 'secrets'.
      -> Detectado por: BANDIT (B311) e SEMGREP
    """
    return str(random.randint(100000, 999999))


def gerar_id_transacao():
    """Gera um ID de transação (também com random inseguro)."""
    return "TX" + str(random.randint(10000000, 99999999))  # B311


def verificar_senha_admin(senha_digitada):
    """
    Verifica a senha do administrador.

    VULNERABILIDADE: compara com uma senha padrão hardcoded.
      -> Detectado por: BANDIT (B105) e GITLEAKS
    """
    # Comparação direta com senha embutida no código
    senha_mestra = "SuperAdmin@Banco#2024"        # hardcoded password
    if senha_digitada == senha_mestra:
        return True
    if senha_digitada == ADMIN_DEFAULT_PASSWORD:
        return True
    return False
