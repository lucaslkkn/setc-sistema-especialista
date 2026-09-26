# -*- coding: utf-8 -*-
"""
SETC - Sistema Especialista de Triagem de Chamados
Interface de linha de comando (CLI) para aquisição de fatos junto ao
usuário, execução do motor de inferência e apresentação do resultado.

Uso:
    python setc_cli.py            # modo interativo
    python setc_cli.py --demo     # executa 3 casos de teste prontos
"""

import sys
from base_conhecimento import construir_base_de_regras, VALORES_VALIDOS
from motor_inferencia import MotorDeInferencia


def pergunta_escolha(rotulo: str, opcoes: list) -> str:
    print(f"\n{rotulo} {opcoes}")
    while True:
        resp = input("> ").strip().lower()
        if resp in opcoes:
            return resp
        print("Valor inválido, escolha uma das opções listadas.")


def pergunta_sim_nao(rotulo: str) -> bool:
    print(f"\n{rotulo} (s/n)")
    while True:
        resp = input("> ").strip().lower()
        if resp in ("s", "sim"):
            return True
        if resp in ("n", "nao", "não"):
            return False
        print("Responda com 's' ou 'n'.")


def pergunta_numero(rotulo: str) -> int:
    print(f"\n{rotulo}")
    while True:
        resp = input("> ").strip()
        if resp.isdigit():
            return int(resp)
        print("Informe um número inteiro.")


def coletar_fatos_interativo() -> dict:
    print("=" * 70)
    print(" SETC — Abertura de chamado (entrevista do sistema especialista)")
    print("=" * 70)
    fatos = {
        "categoria": pergunta_escolha(
            "Categoria do problema:", VALORES_VALIDOS["categoria"]),
        "urgencia": pergunta_escolha(
            "Urgência percebida pelo usuário:", VALORES_VALIDOS["urgencia"]),
        "status_servico": pergunta_escolha(
            "Situação do serviço/sistema:", VALORES_VALIDOS["status_servico"]),
        "qtd_usuarios_afetados": pergunta_numero(
            "Quantidade de usuários afetados:"),
        "sistema": input("\nNome do sistema/aplicação (ou Enter p/ pular): ").strip() or None,
        "usuario_vip": pergunta_sim_nao("O solicitante é um usuário VIP?"),
        "chamado_reincidente": pergunta_sim_nao(
            "O mesmo problema já ocorreu nos últimos 7 dias?"),
        "fora_do_horario_comercial": pergunta_sim_nao(
            "A abertura ocorre fora do horário comercial?"),
    }
    return fatos


def casos_de_teste_demo() -> list:
    return [
        {
            "titulo": "Caso 1 — Queda total de rede no departamento financeiro",
            "fatos": dict(categoria="rede", urgencia="critica",
                          status_servico="indisponivel_total",
                          qtd_usuarios_afetados=35, sistema=None,
                          usuario_vip=False, chamado_reincidente=False,
                          fora_do_horario_comercial=False),
        },
        {
            "titulo": "Caso 2 — Diretor (VIP) sem acesso ao e-mail, fora do horário",
            "fatos": dict(categoria="email", urgencia="media",
                          status_servico="funcionando_com_erro",
                          qtd_usuarios_afetados=1, sistema="Outlook",
                          usuario_vip=True, chamado_reincidente=True,
                          fora_do_horario_comercial=True),
        },
        {
            "titulo": "Caso 3 — Suspeita de phishing (incidente de segurança)",
            "fatos": dict(categoria="seguranca", urgencia="baixa",
                          status_servico="funcionando_com_erro",
                          qtd_usuarios_afetados=1, sistema="Webmail",
                          usuario_vip=False, chamado_reincidente=False,
                          fora_do_horario_comercial=False),
        },
    ]


def exibir_resultado(fatos: dict, rastro: list) -> None:
    print("\n" + "-" * 70)
    print(" RASTRO DE INFERÊNCIA (regras disparadas)")
    print("-" * 70)
    for linha in rastro:
        print(linha)

    print("\n" + "=" * 70)
    print(" RESULTADO DA TRIAGEM")
    print("=" * 70)
    print(f" Impacto inferido ..........: {fatos.get('impacto')}")
    print(f" Urgência informada ........: {fatos.get('urgencia')}")
    print(f" Prioridade base (matriz) ..: {fatos.get('prioridade_base')}")
    print(f" Prioridade final ..........: {fatos.get('prioridade_final')}")
    print(f" Fila de atendimento .......: {fatos.get('fila_atendimento')}")
    print(f" SLA de resposta ...........: {fatos.get('sla_resposta')}")
    if fatos.get("observacao_sla"):
        print(f" Observação .................: {fatos.get('observacao_sla')}")
    if fatos.get("aciona_notificacao_gestor"):
        print(" >> Notificação automática ao gestor de plantão acionada.")
    for j in fatos.get("justificativas", []):
        print(f" Justificativa: {j}")
    print("=" * 70)


def main():
    regras = construir_base_de_regras()
    motor = MotorDeInferencia(regras)

    if "--demo" in sys.argv:
        for caso in casos_de_teste_demo():
            print("\n\n#### " + caso["titulo"])
            fatos_final, rastro = motor.executar(dict(caso["fatos"]))
            exibir_resultado(fatos_final, rastro)
    else:
        fatos = coletar_fatos_interativo()
        fatos_final, rastro = motor.executar(fatos)
        exibir_resultado(fatos_final, rastro)


if __name__ == "__main__":
    main()
