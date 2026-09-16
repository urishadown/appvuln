"""
config.py — Configurações do sistema BancoTerminal.

ATENÇÃO: este arquivo contém vulnerabilidades PLANTADAS DE PROPÓSITO
para um laboratório de análise estática (SAST). NÃO use em produção.

O erro clássico do desenvolvedor apressado: deixar segredos no código.
"""

# =====================================================================
# CREDENCIAIS DO BANCO DE DADOS (hardcoded)
#   -> Detectado por: GITLEAKS (segredo) e BANDIT (B105/B106)
# =====================================================================
DB_HOST = "10.0.2.50"
DB_USER = "svc_corebanking"
DB_PASSWORD = "C0reB@nk!ng_Prod_2024"          # senha em texto claro
DB_NAME = "banco_producao"

# Connection string completa (outra forma comum de vazar credencial)
#   -> Detectado por: GITLEAKS
DATABASE_URL = "postgresql://svc_corebanking:C0reB@nk!ng_Prod_2024@10.0.2.50:5432/banco_producao"

# =====================================================================
# CHAVES E TOKENS (hardcoded)
#   -> Detectado por: GITLEAKS
# =====================================================================
# Chave secreta usada para assinar os tokens de sessão (JWT)
JWT_SECRET = "banco-jwt-super-secret-key-nao-compartilhe-2026"

# Chave de API do provedor de Pix (formato realista de chave viva)
PIX_API_KEY = "sk_live_51H8xQe2eZvKYlo2CqR8kL9mN4pT7wX3yB6vD1fG0hJ2kL5mN8pQf"

# Credenciais de acesso à nuvem (formato AWS)
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# Token do serviço de mensageria (webhook de notificações)
SLACK_WEBHOOK = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"

# =====================================================================
# CONFIGURAÇÃO DE SERVIÇO
# =====================================================================
# Bind em todas as interfaces expõe o serviço à rede inteira
#   -> Detectado por: BANDIT (B104)
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 8080

# Modo de depuração ligado (vaza informação em erros)
DEBUG = True

# Senha padrão do administrador (nunca faça isso)
#   -> Detectado por: BANDIT (B105) e GITLEAKS
ADMIN_DEFAULT_PASSWORD = "admin123"
