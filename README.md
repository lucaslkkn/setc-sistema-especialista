# SETC — Sistema Especialista de Triagem de Chamados de Suporte de TI

Implementação em Python de um sistema especialista baseado em regras de
produção (SE-ENTÃO) com motor de inferência por encadeamento para frente
(*forward chaining*), aplicado ao domínio de **Service Desk / Suporte
Técnico de TI**.

## Estrutura

```
codigo/
├── base_conhecimento.py   # Base de Regras (30 regras) + vocabulário de fatos
├── motor_inferencia.py    # Motor de Inferência (forward chaining genérico)
├── setc_cli.py            # Interface de aquisição de fatos e apresentação
├── test_setc.py           # Testes automatizados (6 cenários)
└── README.md
```

## Como executar

```bash
# Executa 3 casos de teste prontos (modo demonstração)
python3 setc_cli.py --demo

# Modo interativo (entrevista o usuário e realiza a triagem)
python3 setc_cli.py

# Executa a bateria de testes
python3 test_setc.py
```

Requisitos: Python 3.8+ (biblioteca padrão apenas, sem dependências externas).

## Arquitetura do sistema especialista

| Componente clássico de SE | Implementação neste projeto |
|---|---|
| Base de Fatos (memória de trabalho) | `dict` construído em `setc_cli.py` e mutado por `motor_inferencia.py` |
| Base de Regras (base de conhecimento) | Lista de objetos `Regra` em `base_conhecimento.py` |
| Motor de Inferência | Classe `MotorDeInferencia` (encadeamento para frente, ciclo até ponto fixo) |
| Interface de aquisição de conhecimento/uso | `setc_cli.py` |
| Módulo de explicação (rastro) | Lista `rastro` retornada por `MotorDeInferencia.executar()` |

## Protótipo de telas (Figma)

https://www.figma.com/design/0lCUF2SzWgX0wfpy5nN8My/SETC---Prototipo-de-Telas

## Casos de teste

`test_setc.py` cobre 6 cenários: incidente crítico de rede (P1), promoção por
usuário VIP, trava de segurança (phishing → P1), diferimento fora do horário
comercial, parada do motor em ponto fixo e não acúmulo de promoções.

## Licença

Uso acadêmico.
