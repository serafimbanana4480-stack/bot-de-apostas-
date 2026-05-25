---
ID: OPS-002
tags: #status/active #operations #alerts #management #escalation
---

# Gestão de Alertas Operacionais

## Objetivo
Estabelecer o sistema centralizado de receção, triagem, enquadramento, encaminhamento e resolução de todos os alertas operacionais gerados pelo ecossistema de value betting NBA. Desde alertas técnicos (infraestrutura) até alertas de negócio (drawdown, CLV negativo), todos os eventos devem seguir um ciclo de vida definido: deteção → classificação → notificação → investigação → resolução → pós-mortem.

## O que faz
- Define as 8+ categorias de alerta: Infraestrutura, Dados, Modelo, Risco, Performance, Segurança, Compliance, Financeiro.
- Estabelece níveis de severidade (P1-Crítico, P2-Alto, P3-Médio, P4-Baixo, P5-Informativo) com tempos de resposta máximos e rotas de escalação.
- Integra múltiplos canais de notificação: Telegram (ops team), PagerDuty/Opsgenie (on-call), e-mail (stakeholders), dashboard (visual).
- Define estados do ciclo de vida do alerta: TRIGGERED, ACKNOWLEDGED, INVESTIGATING, RESOLVED, SILENCED, FALSE_POSITIVE.
- Implementa mecanismos de deduplicação, agrupamento (correlation), e silenciamento programado para manutenção.

## Porque existe
- **Síndrome do Alerta Falso**: Sem gestão rigorosa, operadores desenvolvem "alert fatigue" e ignoram alertas críticos misturados com ruído. Um estudo da PagerDuty indica que >50% de alertas em sistemas mal geridos são falsos positivos.
- **Tempo de Resposta**: Em value betting, 5 minutos de latência num feed de odds podem significar a diferença entre um sinal com +3% CLV e um sinal com -1% CLV. A gestão de alertas é operação de tempo real.
- **Accountability**: Todo o alerta deve ter um dono (owner) que o reconhece e resolve. Alertas "órfãos" são sinónimo de falha organizacional.
- **Melhoria Contínua**: O histórico de alertas alimenta os runbooks e os postmortems. Sem gestão, perde-se a memória institucional.

## Implementação / Pseudocódigo
```python
class GestaoAlertas:
    def __init__(self):
        self.categorias = {
            "INFRA": {"descricao": "Infraestrutura: VPS, CPU, RAM, disco, rede", "canal": "#ops-infra"},
            "DADOS": {"descricao": "Feeds, latência, qualidade, drift", "canal": "#ops-dados"},
            "MODELO": {"descricao": "Performance preditiva, retrain, deploy", "canal": "#ops-ml"},
            "RISCO": {"descricao": "Drawdown, exposure, circuit breaker", "canal": "#ops-risco"},
            "PERFORMANCE": {"descricao": "P&L, CLV, taxa acerto, slippage", "canal": "#ops-performance"},
            "SEGURANCA": {"descricao": "Acessos não autorizados, vulnerabilidades", "canal": "#ops-seguranca"},
            "COMPLIANCE": {"descricao": "KYC, GDPR, RG, regulamentação", "canal": "#ops-compliance"},
            "FINANCEIRO": {"descricao": "Cobranças, reembolsos, chargebacks", "canal": "#ops-financeiro"}
        }
        self.severidades = {
            "P1": {"nome": "CRITICO", "tempo_resposta_min": 5, "tempo_resolucao_max_min": 30, "escalacao": "auto_pagerduty_call"},
            "P2": {"nome": "ALTO", "tempo_resposta_min": 15, "tempo_resolucao_max_min": 120, "escalacao": "telegram_urgente"},
            "P3": {"nome": "MEDIO", "tempo_resposta_min": 60, "tempo_resolucao_max_min": 480, "escalacao": "email_ops"},
            "P4": {"nome": "BAIXO", "tempo_resposta_min": 240, "tempo_resolucao_max_min": 1440, "escalacao": "dashboard_only"},
            "P5": {"nome": "INFORMATIVO", "tempo_resposta_min": None, "tempo_resolucao_max_min": None, "escalacao": "none"}
        }
        self.estados = ["TRIGGERED", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "SILENCED", "FALSE_POSITIVE"]

    def processar_novo_alerta(self, categoria, severidade, mensagem, origem, payload):
        alerta_id = f"ALT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        
        # Deduplicação
        alerta_existente = self.db.procurar_alerta_ativo(categoria, mensagem, janela_minutos=10)
        if alerta_existente:
            self.db.incrementar_contagem(alerta_existente["id"])
            return {"status": "DEDUPLICADO", "alerta_pai": alerta_existente["id"]}
        
        # Agrupamento (correlation)
        grupo = self.avaliar_grupo(categoria, origem)
        
        alerta = {
            "id": alerta_id,
            "timestamp_utc": datetime.utcnow().isoformat(),
            "categoria": categoria,
            "severidade": severidade,
            "mensagem": mensagem,
            "origem": origem,
            "payload": payload,
            "estado": "TRIGGERED",
            "grupo": grupo,
            "owner": None,
            "tempo_resposta_max": self.severidades[severidade]["tempo_resposta_min"],
            "tempo_resolucao_max": self.severidades[severidade]["tempo_resolucao_max_min"]
        }
        
        self.db.inserir("alertas", alerta)
        self.notificar(alerta)
        
        if severidade in ["P1", "P2"]:
            self.agendar_escalacao_automatica(alerta)
        
        return {"status": "CRIADO", "alerta_id": alerta_id}

    def notificar(self, alerta):
        config = self.categorias[alerta["categoria"]]
        severidade_config = self.severidades[alerta["severidade"]]
        
        if alerta["severidade"] == "P1":
            self.pagerduty.trigger_incident(
                title=f"[P1] {alerta['mensagem']}",
                urgency="high",
                service_key=config["canal"],
                details=alerta["payload"]
            )
            self.telegram.enviar_urgente(config["canal"], alerta)
        elif alerta["severidade"] == "P2":
            self.telegram.enviar_urgente(config["canal"], alerta)
            self.email.enviar_ops(alerta)
        elif alerta["severidade"] == "P3":
            self.telegram.enviar(config["canal"], alerta)
            self.email.enviar_ops(alerta)
        elif alerta["severidade"] == "P4":
            self.dashboard.publicar(alerta)
        # P5: apenas dashboard

    def agendar_escalacao_automatica(self, alerta):
        if alerta["severidade"] == "P1":
            # Se não for ACK em 5 minutos, escalao para gestor de operações
            schedule.delay(self.escalar, args=(alerta["id"], "gestor_operacoes"), countdown=300)
        elif alerta["severidade"] == "P2":
            # Se não for ACK em 15 minutos, escalao
            schedule.delay(self.escalar, args=(alerta["id"], "gestor_operacoes"), countdown=900)

    def transitar_estado(self, alerta_id, novo_estado, operador_id, nota=""):
        alerta = self.db.obter_alerta(alerta_id)
        transicao_valida = self.validar_transicao(alerta["estado"], novo_estado)
        if not transicao_valida:
            raise ValueError(f"Transição inválida: {alerta['estado']} -> {novo_estado}")
        
        self.db.atualizar_alerta(alerta_id, {
            "estado": novo_estado,
            "owner": operador_id,
            "nota_resolucao": nota,
            f"timestamp_{novo_estado.lower()}": datetime.utcnow().isoformat()
        })
        
        if novo_estado == "RESOLVED":
            self.metricas.registrar_ttr(alerta_id)  # Time To Resolve
        elif novo_estado == "ACKNOWLEDGED":
            self.metricas.registrar_tta(alerta_id)  # Time To Acknowledge
```

## Thresholds e Tabelas

| Severidade | Nome | Tempo para ACK | Tempo para Resolução | Notificação | Escalção Automática |
|-----------|------|---------------|---------------------|-------------|---------------------|
| P1 | Crítico | 5 minutos | 30 minutos | PagerDuty call + Telegram + E-mail | Gestor em 5 min; CEO em 15 min |
| P2 | Alto | 15 minutos | 2 horas | Telegram urgente + E-mail | Gestor em 15 min |
| P3 | Médio | 1 hora | 8 horas | Telegram + E-mail | Gestor em 4 horas |
| P4 | Baixo | 4 horas | 24 horas | Dashboard + E-mail diário | Nenhuma |
| P5 | Informativo | N/A | N/A | Dashboard | Nenhuma |

| Categoria | Exemplos de Alerta | Severidade Típica | Runbook Associado |
|-----------|-------------------|------------------|--------------------|
| INFRA | CPU > 90% por 5 min | P2 | [[26_Runbooks/RB-004_PostgreSQL_Down]] |
| DADOS | Feed de odds offline > 10 min | P1 | [[26_Runbooks/RB-001_Feed_Dados_Offline]] |
| MODELO | AUC abaixo de 0.55 em 3 jogos | P2 | [[26_Runbooks/RB-002_Modelo_Valores_Estranhos]] |
| RISCO | Drawdown diário > 15% | P1 | [[26_Runbooks/RB-008_Drawdown_Acelerado]] |
| PERFORMANCE | CLV médio 3 dias < 0% | P2 | [[26_Runbooks/RB-009_CLV_Negativo_3d]] |
| SEGURANCA | Login falhado > 10x de mesmo IP | P2 | [[26_Runbooks/RB-005_Redis_Indisponivel]] (exemplo) |
| COMPLIANCE | Consentimento cookie ausente > 100 pedidos | P3 | N/A |
| FINANCEIRO | Chargeback rate mensal > 1% | P2 | N/A |

## Riscos
- **Risco de Inundação (Alert Fatigue)**: Um sistema que gera 500 alertas P3 por dia torna-se inútil. Requer tuning contínuo de thresholds.
- **Risco de Silenciamento Esquecido**: Um alerta silenciado para manutenção pode nunca ser reativado, deixando uma lacuna de monitorização permanente.
- **Risco de Escalada Desproporcionada**: Alertas P1 em volume elevado desgastam a equipa de gestão e reduzem a eficácia da resposta a incidentes verdadeiramente críticos.
- **Risco de Falso Positivo Mal Classificado**: Um alerta marcado como FALSE_POSITIVE sem investigação adequada pode esconder um problema real subjacente.

## Checklist de Gestão de Alertas
- [ ] Todos os alertas P1 e P2 dos últimos 30 dias têm owner atribuído e nota de resolução.
- [ ] Taxa de falsos positivos < 15% por categoria (revisão mensal).
- [ ] Tempo médio de ACK (TTA) para P1 < 3 minutos; para P2 < 10 minutos.
- [ ] Tempo médio de resolução (TTR) para P1 < 20 minutos; para P2 < 90 minutos.
- [ ] Dashboard de alertas ativos atualizado em tempo real e projetado em ecrã na sala de operações.
- [ ] Runbook associado a cada alerta P1 e P2; link direto no corpo da mensagem de alerta.
- [ ] Revisão semanal de alertas silenciados para reativação ou remoção permanente.
- [ ] Integração com [[27_Postmortems/EXEMPLO_POSTMORTEM]]: todo alerta P1 que exigiu intervenção manual gera ticket de postmortem.

## Links Cruzados
- [[33_Alerting/THRESHOLDS_ALERTAS]] - Definição técnica dos thresholds que disparam cada alerta.
- [[33_Alerting/ROTAS_ESCALADA]] - Detalhe das rotas de escalação por severidade.
- [[33_Alerting/PLAYBOOK_RESPOSTA]] - Playbooks específicos de resposta a alertas.
- [[26_Runbooks/RB-001_Feed_Dados_Offline]] a [[26_Runbooks/RB-010_Erro_Deploy_Modelo]] - Runbooks ligados aos alertas.
- [[18_Operations/ROTINA_DIARIA]] - Rotina que inclui verificação de alertas pendentes.
