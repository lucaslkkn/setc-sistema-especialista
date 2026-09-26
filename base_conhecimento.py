# -*- coding: utf-8 -*-
"""
Base de Conhecimento do Sistema Especialista de Triagem de Chamados (SETC)
---------------------------------------------------------------------------
Domínio: Suporte Técnico de TI / Service Desk

Este módulo concentra:
  1) a BASE DE FATOS  -> representada em tempo de execução por um dicionário
     de working memory (memória de trabalho) alimentado pelo usuário e
     enriquecido pelo motor de inferência;
  2) a BASE DE REGRAS -> uma lista de regras de produção no formato
     SE <condições> ENTÃO <conclusões>, cada uma implementada como uma
     função (condicao, acao) para permitir encadeamento para frente
     (forward chaining).

As 30 regras estão organizadas em quatro grupos, refletindo a lógica de um
especialista humano de service desk:
  A) Regras de INFERÊNCIA DE IMPACTO  (R01-R05)
  B) Regras de PRIORIZAÇÃO (matriz Impacto x Urgência)  (R06-R21)
  C) Regras de EXCEÇÃO / AJUSTE FINO  (R22-R26)
  D) Regras de ROTEAMENTO DE FILA E SLA (R27-R30)
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, Any, List


@dataclass
class Regra:
    """Representa uma regra de produção SE-ENTÃO da base de conhecimento."""
    id: str
    descricao: str
    condicao: Callable[[Dict[str, Any]], bool]
    acao: Callable[[Dict[str, Any]], None]
    grupo: str


def _set_se_ausente(fatos: Dict[str, Any], chave: str, valor: Any) -> bool:
    """Define fatos[chave]=valor somente se ainda não definido.
    Retorna True se alterou a memória de trabalho (novo fato inferido)."""
    if fatos.get(chave) is None:
        fatos[chave] = valor
        return True
    return False


# ---------------------------------------------------------------------------
# BASE DE REGRAS
# ---------------------------------------------------------------------------
def construir_base_de_regras() -> List[Regra]:
    regras: List[Regra] = []

    # ---------------- GRUPO A: INFERÊNCIA DE IMPACTO ----------------------
    regras.append(Regra(
        "R01",
        "SE categoria = rede E status_servico = indisponivel_total "
        "ENTÃO impacto = departamento",
        lambda f: f.get("categoria") == "rede"
                  and f.get("status_servico") == "indisponivel_total"
                  and f.get("impacto") is None,
        lambda f: _set_se_ausente(f, "impacto", "departamento"),
        "A - Inferência de Impacto",
    ))

    regras.append(Regra(
        "R02",
        "SE categoria = email E status_servico = indisponivel_total "
        "E qtd_usuarios_afetados > 20 ENTÃO impacto = organizacao",
        lambda f: f.get("categoria") == "email"
                  and f.get("status_servico") == "indisponivel_total"
                  and (f.get("qtd_usuarios_afetados") or 0) > 20,
        lambda f: f.__setitem__("impacto", "organizacao"),
        "A - Inferência de Impacto",
    ))

    regras.append(Regra(
        "R03",
        "SE categoria = hardware E qtd_usuarios_afetados = 1 "
        "ENTÃO impacto = individual",
        lambda f: f.get("categoria") == "hardware"
                  and (f.get("qtd_usuarios_afetados") or 1) == 1
                  and f.get("impacto") is None,
        lambda f: _set_se_ausente(f, "impacto", "individual"),
        "A - Inferência de Impacto",
    ))

    regras.append(Regra(
        "R04",
        "SE categoria = acesso E sistema = 'ERP financeiro' "
        "ENTÃO impacto = departamento",
        lambda f: f.get("categoria") == "acesso"
                  and f.get("sistema") == "ERP financeiro"
                  and f.get("impacto") is None,
        lambda f: _set_se_ausente(f, "impacto", "departamento"),
        "A - Inferência de Impacto",
    ))

    regras.append(Regra(
        "R05",
        "SE impacto ainda não inferido ENTÃO impacto = grupo (padrão "
        "conservador do domínio)",
        lambda f: f.get("impacto") is None and f.get("categoria") is not None,
        lambda f: _set_se_ausente(f, "impacto", "grupo"),
        "A - Inferência de Impacto",
    ))

    # ------------- GRUPO B: MATRIZ IMPACTO x URGÊNCIA -> PRIORIDADE -------
    matriz = {
        ("organizacao", "critica"): "P1",
        ("organizacao", "alta"): "P1",
        ("organizacao", "media"): "P2",
        ("organizacao", "baixa"): "P2",
        ("departamento", "critica"): "P1",
        ("departamento", "alta"): "P2",
        ("departamento", "media"): "P3",
        ("departamento", "baixa"): "P3",
        ("grupo", "critica"): "P2",
        ("grupo", "alta"): "P3",
        ("grupo", "media"): "P3",
        ("grupo", "baixa"): "P4",
        ("individual", "critica"): "P3",
        ("individual", "alta"): "P4",
        ("individual", "media"): "P4",
        ("individual", "baixa"): "P4",
    }

    def gera_regra_matriz(rid, impacto, urgencia, prioridade):
        desc = (f"SE impacto = {impacto} E urgencia = {urgencia} "
                f"ENTÃO prioridade_base = {prioridade}")
        cond = (lambda f, i=impacto, u=urgencia:
                f.get("impacto") == i and f.get("urgencia") == u
                and f.get("prioridade_base") is None)
        acao = (lambda f, p=prioridade: f.__setitem__("prioridade_base", p))
        return Regra(rid, desc, cond, acao, "B - Matriz Impacto x Urgência")

    # R06 a R21 (16 combinações de impacto x urgência)
    for indice, ((imp, urg), prio) in enumerate(matriz.items()):
        rid = f"R{6 + indice:02d}"
        regras.append(gera_regra_matriz(rid, imp, urg, prio))

    # ------------- GRUPO C: EXCEÇÕES / AJUSTE FINO -------------------------
    def upgrade(prioridade: str) -> str:
        ordem = ["P4", "P3", "P2", "P1"]
        idx = ordem.index(prioridade)
        return ordem[min(idx + 1, len(ordem) - 1)]

    regras.append(Regra(
        "R22",
        "SE usuario_vip = True E prioridade_base != P1 "
        "ENTÃO promove prioridade em um nível",
        lambda f: f.get("usuario_vip") is True
                  and f.get("prioridade_base") is not None
                  and f.get("prioridade_final") is None
                  and f.get("_r22_aplicada") is not True,
        lambda f: (f.__setitem__("prioridade_final",
                                  upgrade(f["prioridade_base"])),
                   f.__setitem__("_r22_aplicada", True),
                   f.__setitem__("justificativas",
                                 f.get("justificativas", [])
                                 + ["R22: usuário VIP promoveu a prioridade"])),
        "C - Exceções",
    ))

    regras.append(Regra(
        "R23",
        "SE chamado_reincidente = True (mesmo problema em 7 dias) E nenhuma "
        "promoção já aplicada ENTÃO promove prioridade em um nível "
        "(promoções não se acumulam)",
        lambda f: f.get("chamado_reincidente") is True
                  and f.get("prioridade_base") is not None
                  and f.get("prioridade_final") is None
                  and f.get("_r23_aplicada") is not True,
        lambda f: (f.__setitem__("prioridade_final",
                                  upgrade(f["prioridade_base"])),
                   f.__setitem__("_r23_aplicada", True),
                   f.__setitem__("justificativas",
                                 f.get("justificativas", [])
                                 + ["R23: reincidência em 7 dias promoveu a prioridade"])),
        "C - Exceções",
    ))

    regras.append(Regra(
        "R24",
        "SE fora_do_horario_comercial = True E prioridade_final em (P3,P4) "
        "ENTÃO marca 'atendimento_diferido'",
        lambda f: f.get("fora_do_horario_comercial") is True
                  and f.get("prioridade_final") in ("P3", "P4")
                  and f.get("atendimento_diferido") is None,
        lambda f: f.__setitem__("atendimento_diferido", True),
        "C - Exceções",
    ))

    regras.append(Regra(
        "R25",
        "SE nenhuma exceção alterou a prioridade "
        "ENTÃO prioridade_final = prioridade_base",
        lambda f: f.get("prioridade_base") is not None
                  and f.get("prioridade_final") is None,
        lambda f: f.__setitem__("prioridade_final", f["prioridade_base"]),
        "C - Exceções",
    ))

    regras.append(Regra(
        "R26",
        "SE categoria = seguranca (ex.: suspeita de invasão/phishing) "
        "ENTÃO força prioridade_final = P1 (trava de segurança)",
        lambda f: f.get("categoria") == "seguranca"
                  and f.get("prioridade_final") != "P1",
        lambda f: (f.__setitem__("prioridade_final", "P1"),
                   f.__setitem__("justificativas",
                                 f.get("justificativas", [])
                                 + ["R26: incidente de segurança força P1"])),
        "C - Exceções",
    ))

    # ------------- GRUPO D: ROTEAMENTO DE FILA E SLA -----------------------
    sla_fila = {
        "P1": ("N3 - Especialistas / Infraestrutura crítica", "15 minutos"),
        "P2": ("N2 - Analistas de Suporte Pleno", "2 horas"),
        "P3": ("N1 - Suporte de primeiro nível", "8 horas úteis"),
        "P4": ("N1 - Suporte de primeiro nível", "24 horas úteis"),
    }

    regras.append(Regra(
        "R27",
        "SE prioridade_final definida ENTÃO define fila_atendimento e "
        "sla_resposta conforme tabela de SLA",
        lambda f: f.get("prioridade_final") is not None
                  and f.get("fila_atendimento") is None,
        lambda f: (f.__setitem__("fila_atendimento",
                                  sla_fila[f["prioridade_final"]][0]),
                   f.__setitem__("sla_resposta",
                                 sla_fila[f["prioridade_final"]][1])),
        "D - Roteamento e SLA",
    ))

    regras.append(Regra(
        "R28",
        "SE atendimento_diferido = True ENTÃO acrescenta observação de "
        "atendimento no próximo expediente",
        lambda f: f.get("atendimento_diferido") is True
                  and f.get("observacao_sla") is None,
        lambda f: f.__setitem__(
            "observacao_sla",
            "Atendimento no próximo expediente (fora do horário comercial)."),
        "D - Roteamento e SLA",
    ))

    regras.append(Regra(
        "R29",
        "SE prioridade_final = P1 ENTÃO aciona_notificacao_gestor = True",
        lambda f: f.get("prioridade_final") == "P1"
                  and f.get("aciona_notificacao_gestor") is None,
        lambda f: f.__setitem__("aciona_notificacao_gestor", True),
        "D - Roteamento e SLA",
    ))

    regras.append(Regra(
        "R30",
        "SE fila_atendimento e sla_resposta definidos "
        "ENTÃO triagem_concluida = True (condição de parada do motor)",
        lambda f: f.get("fila_atendimento") is not None
                  and f.get("sla_resposta") is not None
                  and f.get("triagem_concluida") is not True,
        lambda f: f.__setitem__("triagem_concluida", True),
        "D - Roteamento e SLA",
    ))

    return regras


# Vocabulário controlado aceito pela base de fatos (valida entrada do usuário)
VALORES_VALIDOS = {
    "categoria": ["rede", "hardware", "software", "acesso", "email", "seguranca"],
    "urgencia": ["baixa", "media", "alta", "critica"],
    "status_servico": ["funcionando_com_erro", "degradado", "indisponivel_total"],
    "impacto": ["individual", "grupo", "departamento", "organizacao"],
}
