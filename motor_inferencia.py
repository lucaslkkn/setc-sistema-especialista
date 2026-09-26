# -*- coding: utf-8 -*-
"""
Motor de Inferência do SETC — encadeamento para frente (forward chaining)
--------------------------------------------------------------------------
Algoritmo clássico de sistemas de produção:

    enquanto houver alteração na base de fatos:
        para cada regra da base de regras, em ordem:
            se a condição da regra é satisfeita pelos fatos atuais:
                executa a ação (conclusão) da regra
                marca que houve alteração
        se nenhuma regra disparou nesta rodada -> ponto fixo, encerra

O motor é agnóstico ao domínio: recebe uma base de fatos (dict) e uma lista
de Regra (ver base_conhecimento.py) e devolve o rastro de execução (quais
regras dispararam, em que ordem) além dos fatos finais — o que corresponde,
em um SE clássico, à separação entre Motor de Inferência, Base de Regras e
Base de Fatos.
"""

from typing import Dict, Any, List, Tuple
from base_conhecimento import Regra


class MotorDeInferencia:
    def __init__(self, regras: List[Regra], limite_ciclos: int = 50):
        self.regras = regras
        self.limite_ciclos = limite_ciclos
        self.rastro: List[str] = []

    def executar(self, fatos: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        self.rastro = []
        for ciclo in range(1, self.limite_ciclos + 1):
            houve_disparo = False
            for regra in self.regras:
                if regra.condicao(fatos):
                    regra.acao(fatos)
                    houve_disparo = True
                    self.rastro.append(
                        f"Ciclo {ciclo:02d} -> {regra.id} disparada: {regra.descricao}"
                    )
            if not houve_disparo:
                self.rastro.append(
                    f"Ciclo {ciclo:02d} -> nenhuma regra disparou (ponto fixo atingido)"
                )
                break
        # Limpa flags internas de controle antes de devolver os fatos
        fatos_limpos = {k: v for k, v in fatos.items() if not k.startswith("_")}
        return fatos_limpos, self.rastro
