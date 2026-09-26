# -*- coding: utf-8 -*-
"""Testes automatizados do motor de inferência do SETC (pytest ou execução direta)."""

from base_conhecimento import construir_base_de_regras
from motor_inferencia import MotorDeInferencia


def _executar(fatos):
    motor = MotorDeInferencia(construir_base_de_regras())
    return motor.executar(dict(fatos))


def test_rede_critica_departamento_vira_p1():
    fatos = dict(categoria="rede", urgencia="critica",
                 status_servico="indisponivel_total",
                 qtd_usuarios_afetados=35, sistema=None,
                 usuario_vip=False, chamado_reincidente=False,
                 fora_do_horario_comercial=False)
    resultado, _ = _executar(fatos)
    assert resultado["impacto"] == "departamento"
    assert resultado["prioridade_final"] == "P1"
    assert resultado["fila_atendimento"].startswith("N3")


def test_vip_promove_prioridade_em_um_nivel():
    fatos = dict(categoria="email", urgencia="media",
                 status_servico="funcionando_com_erro",
                 qtd_usuarios_afetados=1, sistema="Outlook",
                 usuario_vip=True, chamado_reincidente=False,
                 fora_do_horario_comercial=False)
    resultado, _ = _executar(fatos)
    # impacto inferido = grupo (R05); grupo+media = P3 (base); VIP promove -> P2
    assert resultado["prioridade_base"] == "P3"
    assert resultado["prioridade_final"] == "P2"


def test_seguranca_forca_p1_mesmo_com_urgencia_baixa():
    fatos = dict(categoria="seguranca", urgencia="baixa",
                 status_servico="funcionando_com_erro",
                 qtd_usuarios_afetados=1, sistema="Webmail",
                 usuario_vip=False, chamado_reincidente=False,
                 fora_do_horario_comercial=False)
    resultado, _ = _executar(fatos)
    assert resultado["prioridade_final"] == "P1"
    assert resultado["aciona_notificacao_gestor"] is True


def test_fora_do_horario_gera_observacao_de_diferimento():
    fatos = dict(categoria="hardware", urgencia="baixa",
                 status_servico="funcionando_com_erro",
                 qtd_usuarios_afetados=1, sistema=None,
                 usuario_vip=False, chamado_reincidente=False,
                 fora_do_horario_comercial=True)
    resultado, _ = _executar(fatos)
    assert resultado["prioridade_final"] == "P4"
    assert "próximo expediente" in resultado["observacao_sla"]


def test_motor_sempre_atinge_ponto_fixo():
    fatos = dict(categoria="software", urgencia="alta",
                 status_servico="degradado",
                 qtd_usuarios_afetados=5, sistema=None,
                 usuario_vip=False, chamado_reincidente=False,
                 fora_do_horario_comercial=False)
    resultado, rastro = _executar(fatos)
    assert resultado["triagem_concluida"] is True
    assert "ponto fixo atingido" in rastro[-1]


def test_promocoes_nao_se_acumulam_e_p2_nao_e_diferido():
    fatos = dict(categoria="email", urgencia="media",
                 status_servico="funcionando_com_erro",
                 qtd_usuarios_afetados=1, sistema="Outlook",
                 usuario_vip=True, chamado_reincidente=True,
                 fora_do_horario_comercial=True)
    resultado, _ = _executar(fatos)
    # VIP + reincidente promovem apenas um nível (P3 -> P2)
    assert resultado["prioridade_final"] == "P2"
    # P2 não é diferido para o próximo expediente
    assert resultado.get("observacao_sla") is None


if __name__ == "__main__":
    testes = [v for k, v in globals().items() if k.startswith("test_")]
    falhas = 0
    for t in testes:
        try:
            t()
            print(f"OK   - {t.__name__}")
        except AssertionError as e:
            falhas += 1
            print(f"FALHOU - {t.__name__}: {e}")
    print(f"\n{len(testes) - falhas}/{len(testes)} testes passaram.")
