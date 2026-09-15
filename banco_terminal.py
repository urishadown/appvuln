#!/usr/bin/env python3
"""
banco_terminal.py — BancoTerminal
Um "Internet Banking" de linha de comando para o laboratório de SAST.

A aplicação é FUNCIONAL e roda no terminal do Debian (só stdlib).
Ela contém vulnerabilidades espalhadas pelos módulos, que serão
detectadas por Semgrep, Bandit e Gitleaks.

Uso:
    python3 banco_terminal.py

Contas de teste (CPF / senha):
    11111111111 / maria123
    22222222222 / joao456
    33333333333 / ana789
    99999999999 / admin123   (administrador)

Dica de demonstração do SQL Injection no login (bypass de senha):
    CPF:   ' OR '1'='1' --
    Senha: qualquer

    (o  --  comenta a verificação da senha; você entra como o
     primeiro cliente da tabela SEM saber a senha dele)
"""

import os
import sys
import time

import database
import auth
import utils

# ---------------------------------------------------------------------
# Cores ANSI (a "parte visual" — funciona em qualquer terminal Debian)
# ---------------------------------------------------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
AZUL = "\033[38;5;25m"
AZUL_CLR = "\033[38;5;39m"
VERDE = "\033[38;5;35m"
VERMELHO = "\033[38;5;196m"
AMARELO = "\033[38;5;220m"
CINZA = "\033[38;5;245m"
BG_AZUL = "\033[48;5;25m\033[38;5;231m"

LARGURA = 62


def limpar():
    os.system("clear" if os.name != "nt" else "cls")


def linha(c="─"):
    return CINZA + (c * LARGURA) + RESET


def moldura_topo(titulo):
    limpar()
    print(BG_AZUL + BOLD + f" {titulo}".ljust(LARGURA) + RESET)
    print(linha())


def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pausar():
    input(f"\n{CINZA}  [ Enter para continuar ]{RESET}")


def banner():
    limpar()
    print(AZUL + BOLD)
    print(r"   ____                        _____                   _             _ ")
    print(r"  | __ )  __ _ _ __   ___ ___  |_   _|__ _ __ _ __ ___ (_)_ __   __ _| |")
    print(r"  |  _ \ / _` | '_ \ / __/ _ \   | |/ _ \ '__| '_ ` _ \| | '_ \ / _` | |")
    print(r"  | |_) | (_| | | | | (_| (_) |  | |  __/ |  | | | | | | | | | | (_| | |")
    print(r"  |____/ \__,_|_| |_|\___\___/   |_|\___|_|  |_| |_| |_|_|_| |_|\__,_|_|")
    print(RESET)
    print(f"  {CINZA}Sua agência digital no terminal · v1.4.2{RESET}")
    print(f"  {VERMELHO}⚠  AMBIENTE DE LABORATÓRIO — NÃO USE EM PRODUÇÃO{RESET}\n")
    print(linha())


# ---------------------------------------------------------------------
# Fluxo de login
# ---------------------------------------------------------------------
def tela_login():
    banner()
    print(f"  {BOLD}ACESSO À CONTA{RESET}\n")
    cpf = input(f"  {AZUL_CLR}CPF:{RESET}   ").strip()
    senha = input(f"  {AZUL_CLR}Senha:{RESET} ").strip()

    print(f"\n  {CINZA}Autenticando...{RESET}")
    time.sleep(0.6)

    # Chama a autenticação (que é vulnerável a SQL Injection)
    resultado = database.autenticar(cpf, senha)

    if resultado:
        _id, cpf_ok, nome, saldo, is_admin = resultado
        # Gera um token de sessão (com segredo hardcoded + MD5)
        token = auth.gerar_token_sessao(cpf_ok, is_admin)
        print(f"  {VERDE}✔  Bem-vindo(a), {nome}!{RESET}")
        print(f"  {CINZA}Token de sessão: {token[:40]}...{RESET}")
        time.sleep(1.0)
        return {"cpf": cpf_ok, "nome": nome, "is_admin": bool(is_admin)}
    else:
        print(f"  {VERMELHO}�’  CPF ou senha inválidos.{RESET}")
        pausar()
        return None


# ---------------------------------------------------------------------
# Operações da conta
# ---------------------------------------------------------------------
def op_saldo(sessao):
    moldura_topo("SALDO EM CONTA")
    saldo = database.consultar_saldo(sessao["cpf"])
    print()
    print(f"  Titular: {BOLD}{sessao['nome']}{RESET}")
    print(f"  CPF....: {sessao['cpf']}")
    print(f"\n  Saldo disponível: {VERDE}{BOLD}{formatar_reais(saldo or 0)}{RESET}")
    pausar()


def op_transferencia(sessao):
    moldura_topo("TRANSFERÊNCIA / PIX")
    print()
    destino = input(f"  {AZUL_CLR}CPF de destino:{RESET} ").strip()
    valor_txt = input(f"  {AZUL_CLR}Valor (ex: 150.00):{RESET} ").strip()

    try:
        valor = float(valor_txt)
    except ValueError:
        print(f"\n  {VERMELHO}Valor inválido.{RESET}")
        pausar()
        return

    cliente_destino = database.buscar_cliente_por_cpf(destino)
    if not cliente_destino:
        print(f"\n  {VERMELHO}Conta de destino não encontrada.{RESET}")
        pausar()
        return

    saldo = database.consultar_saldo(sessao["cpf"]) or 0
    if valor > saldo:
        print(f"\n  {VERMELHO}Saldo insuficiente.{RESET}")
        pausar()
        return

    # Gera o ID e o código 2FA (com random inseguro)
    tx_id = auth.gerar_id_transacao()
    codigo = auth.gerar_codigo_2fa()
    print(f"\n  {AMARELO}Código de confirmação (2FA): {BOLD}{codigo}{RESET}")
    conf = input(f"  {AZUL_CLR}Digite o código para confirmar:{RESET} ").strip()

    if conf != codigo:
        print(f"\n  {VERMELHO}Código incorreto. Transferência cancelada.{RESET}")
        pausar()
        return

    database.registrar_transacao(sessao["cpf"], destino, valor, "PIX")
    # Notifica o provedor de Pix (com verify=False e chave hardcoded)
    utils.notificar_pix(valor, destino)

    print(f"\n  {VERDE}✔  Transferência {tx_id} concluída!{RESET}")
    print(f"  {VERDE}   {formatar_reais(valor)} enviados para {cliente_destino[1]}.{RESET}")
    pausar()


def op_extrato(sessao):
    moldura_topo("EXTRATO")
    transacoes = database.listar_extrato(sessao["cpf"])
    print()
    if not transacoes:
        print(f"  {CINZA}Nenhuma transação registrada.{RESET}")
    else:
        print(f"  {BOLD}{'DATA':<20}{'TIPO':<8}{'DESTINO':<14}{'VALOR':>12}{RESET}")
        print("  " + linha())
        for data, tipo, destino, valor in transacoes:
            print(f"  {data:<20}{tipo:<8}{destino:<14}"
                  f"{VERMELHO}{formatar_reais(valor):>12}{RESET}")
    pausar()


def op_consultar_conta(sessao):
    moldura_topo("CONSULTAR CONTA DE TERCEIRO")
    print(f"\n  {CINZA}Informe o CPF para consultar nome e saldo.{RESET}\n")
    cpf = input(f"  {AZUL_CLR}CPF:{RESET} ").strip()
    # buscar_cliente_por_cpf é vulnerável a SQL injection
    cliente = database.buscar_cliente_por_cpf(cpf)
    if cliente:
        print(f"\n  Nome..: {BOLD}{cliente[1]}{RESET}")
        print(f"  Saldo.: {formatar_reais(cliente[2])}")
    else:
        print(f"\n  {VERMELHO}Conta não encontrada.{RESET}")
    pausar()


# ---------------------------------------------------------------------
# Painel administrativo
# ---------------------------------------------------------------------
def painel_admin(sessao):
    moldura_topo("PAINEL ADMINISTRATIVO")
    print(f"\n  {AMARELO}Área restrita. Autenticação adicional necessária.{RESET}\n")
    senha = input(f"  {AZUL_CLR}Senha de administrador:{RESET} ").strip()

    if not auth.verificar_senha_admin(senha):
        print(f"\n  {VERMELHO}Acesso negado.{RESET}")
        pausar()
        return

    while True:
        moldura_topo("PAINEL ADMINISTRATIVO")
        print(f"""
  {VERDE}1{RESET}  Gerar backup do banco de dados
  {VERDE}2{RESET}  Calcular taxa de operação
  {VERDE}3{RESET}  Compactar relatório
  {VERDE}0{RESET}  Voltar
""")
        opc = input(f"  {AZUL_CLR}Opção:{RESET} ").strip()
        if opc == "1":
            nome = input(f"\n  {AZUL_CLR}Nome do arquivo de backup:{RESET} ").strip()
            # gerar_backup é vulnerável a command injection
            utils.gerar_backup(nome)
            print(f"  {VERDE}Backup solicitado.{RESET}")
            pausar()
        elif opc == "2":
            expr = input(f"\n  {AZUL_CLR}Expressão da taxa (ex: 1000*0.02):{RESET} ").strip()
            try:
                # calcular_taxa usa eval (execução de código arbitrário)
                r = utils.calcular_taxa(expr)
                print(f"  {VERDE}Resultado: {r}{RESET}")
            except Exception as e:
                print(f"  {VERMELHO}Erro: {e}{RESET}")
            pausar()
        elif opc == "3":
            caminho = input(f"\n  {AZUL_CLR}Caminho do relatório:{RESET} ").strip()
            utils.compactar_relatorio(caminho)  # subprocess shell=True
            print(f"  {VERDE}Relatório compactado.{RESET}")
            pausar()
        elif opc == "0":
            return


# ---------------------------------------------------------------------
# Menu principal (pós-login)
# ---------------------------------------------------------------------
def menu_principal(sessao):
    while True:
        moldura_topo(f"OLÁ, {sessao['nome'].upper()}")
        admin_item = (f"  {VERDE}6{RESET}  Painel administrativo\n"
                      if sessao["is_admin"] else "")
        print(f"""
  {VERDE}1{RESET}  Consultar saldo
  {VERDE}2{RESET}  Transferência / Pix
  {VERDE}3{RESET}  Extrato
  {VERDE}4{RESET}  Consultar conta de terceiro
{admin_item}  {VERDE}0{RESET}  Sair
""")
        opc = input(f"  {AZUL_CLR}Escolha uma opção:{RESET} ").strip()
        if opc == "1":
            op_saldo(sessao)
        elif opc == "2":
            op_transferencia(sessao)
        elif opc == "3":
            op_extrato(sessao)
        elif opc == "4":
            op_consultar_conta(sessao)
        elif opc == "6" and sessao["is_admin"]:
            painel_admin(sessao)
        elif opc == "0":
            print(f"\n  {CINZA}Encerrando sessão. Até logo!{RESET}\n")
            return


def main():
    # Garante as pastas de trabalho
    os.makedirs("backups", exist_ok=True)
    database.inicializar_banco()

    while True:
        sessao = tela_login()
        if sessao:
            menu_principal(sessao)
        else:
            banner()
            r = input(f"  {AZUL_CLR}Tentar novamente? (s/n):{RESET} ").strip().lower()
            if r != "s":
                print(f"\n  {CINZA}Até logo!{RESET}\n")
                break


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n  {CINZA}Sessão encerrada.{RESET}\n")
        sys.exit(0)
