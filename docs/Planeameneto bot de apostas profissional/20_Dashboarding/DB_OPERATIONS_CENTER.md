---
ID: DB-003
tags: #status/active #dashboard #operations #center #real-time
---

# Dashboard Operations Center (NOC)

## Objetivo
Criar o painel de controlo em tempo real da sala de operações (Network Operations Center equivalente), permitindo que os operadores monitorem a saúde do sistema, a execução das rotinas, o estado dos serviços, e o fluxo de sinais em tempo real. O Operations Center é o cockpit diário da equipa de operações, projetado em ecrãs na sala de controlo e acessível remotamente via VPN/SSO.

## O que faz
- Monitoriza em tempo real: estado dos feeds de dados (NBA stats, odds, injuries), latência e throughput de todas as APIs internas e externas, filas de processamento (Redis, Celery), estado das bases de dados (PostgreSQL, replicação), e estado do bot Telegram.
- Visualiza o pipeline de sinais: desde a deteção de oportunidade pelo modelo, passando pela verificação de circuit breakers, até ao envio para subscritores, com timestamps em cada etapa.
- Mostra o estado das rotinas diárias: quais tarefas de abertura/fecho foram concluídas, quais estão em atraso, e quais falharam.
- Integra o feed de alertas ativos: P1 em vermelho piscante, P2 em laranja, P3 em amarelo, com possibilidade de reconhecimento direto no dashboard.

## Porque existe
- **Situação de Consciência (Situational Awareness)**: Um operador precisa de ver o estado do sistema num relance. Sem um NOC digital, a equipa descobre problemas quando os subscritores reclamam.
- **Coordenação de Incidentes**: Durante um incidente, o dashboard é a fonte única de verdade que todos os intervenientes (ops, engenharia, gestão) consultam para alinhar a resposta.
- **Prevenção Proativa**: Tendências de degradação (ex: latência do feed de odds a subir gradualmente) são visíveis no dashboard antes de se tornarem falhas.
- **Eficiência Operacional**: Operadores não precisam de fazer login em 10 ferramentas diferentes (AWS, Datadog, PostgreSQL, Redis, Telegram). O NOC agrega tudo.

## Implementação / Pseudocódigo
```python
class DashboardOperationsCenter:
    def __init__(self):
        self.componentes = {
            "feed_nba_stats": {"nome": "NBA Stats API", "tipo": "FEED", "latencia_threshold_ms": 5000, "uptime_threshold": 0.99},
            "feed_odds": {"nome": "Odds API", "tipo": "FEED", "latencia_threshold_ms": 3000, "uptime_threshold": 0.995},
            "feed_injuries": {"nome": "Injuries API", "tipo": "FEED", "latencia_threshold_ms": 10000, "uptime_threshold": 0.98},
            "api_modelo": {"nome": "Model API", "tipo": "SERVICO", "latencia_threshold_ms": 200, "uptime_threshold": 0.999},
            "api_sinais": {"nome": "Signals API", "tipo": "SERVICO", "latencia_threshold_ms": 100, "uptime_threshold": 0.999},
            "postgresql": {"nome": "PostgreSQL", "tipo": "BD", "latencia_threshold_ms": 50, "uptime_threshold": 0.999},
            "redis": {"nome": "Redis", "tipo": "CACHE", "latencia_threshold_ms": 10, "uptime_threshold": 0.999},
            "bot_telegram": {"nome": "Telegram Bot", "tipo": "BOT", "latencia_threshold_ms": 5000, "uptime_threshold": 0.99},
            "circuit_breaker": {"nome": "Circuit Breaker", "tipo": "RISCO", "estado": "CLOSED", "threshold_drawdown": 0.15}
        }
        self.pipeline_sinais = [
            "detecao_oportunidade",
            "validacao_modelo",
            "verificacao_circuit_breaker",
            "calculo_edge",
            "verificacao_odd",
            "formatacao_mensagem",
            "envio_telegram",
            "confirmacao_entrega"
        ]
        self.refresh_ms = 5000  # 5 segundos

    def gerar_estado_componentes(self):
        estado = {}
        for chave, config in self.componentes.items():
            health = self.verificar_saude(chave, config)
            estado[chave] = {
                "nome": config["nome"],
                "status": health["status"],  # OK, DEGRADED, DOWN
                "latencia_ms": health["latencia"],
                "uptime_24h": health["uptime"],
                "ultimo_check": datetime.utcnow().isoformat(),
                "alerta_ativo": health["status"] != "OK"
            }
        return estado

    def gerar_pipeline_sinais(self, horas=24):
        sinais = self.db.obter_sinais_ultimas_horas(horas)
        pipeline = []
        for sinal in sinais:
            etapas = {}
            for etapa in self.pipeline_sinais:
                timestamp = sinal.get(f"timestamp_{etapa}")
                duracao = None
                if timestamp and etapa != self.pipeline_sinais[0]:
                    etapa_anterior = self.pipeline_sinais[self.pipeline_sinais.index(etapa) - 1]
                    ts_anterior = sinal.get(f"timestamp_{etapa_anterior}")
                    if ts_anterior:
                        duracao = (datetime.fromisoformat(timestamp) - datetime.fromisoformat(ts_anterior)).total_seconds()
                etapas[etapa] = {"timestamp": timestamp, "duracao_seg": duracao}
            pipeline.append({"sinal_id": sinal["id"], "etapas": etapas})
        return pipeline

    def gerar_estado_rotinas(self):
        hoje = datetime.utcnow().date()
        rotina_abertura = self.db.obter_rotina("ABERTURA", hoje)
        rotina_fecho = self.db.obter_rotina("FECHO", hoje)
        return {
            "abertura": {
                "status": rotina_abertura["status"] if rotina_abertura else "NAO_INICIADA",
                "tarefas_concluidas": rotina_abertura["concluidas"] if rotina_abertura else 0,
                "tarefas_totais": rotina_abertura["totais"] if rotina_abertura else 12,
                "progresso_percent": rotina_abertura["progresso"] if rotina_abertura else 0
            },
            "fecho": {
                "status": rotina_fecho["status"] if rotina_fecho else "NAO_INICIADA",
                "tarefas_concluidas": rotina_fecho["concluidas"] if rotina_fecho else 0,
                "tarefas_totais": rotina_fecho["totais"] if rotina_fecho else 10,
                "progresso_percent": rotina_fecho["progresso"] if rotina_fecho else 0
            }
        }

    def gerar_feed_alertas(self):
        alertas = self.db.obter_alertas_ativos()
        return [{"id": a["id"], "severidade": a["severidade"], "mensagem": a["mensagem"], "estado": a["estado"], "owner": a["owner"], "idade_min": self.calcular_idade_min(a["timestamp"])} for a in alertas]

    def renderizar_dashboard(self):
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "componentes": self.gerar_estado_componentes(),
            "pipeline_sinais": self.gerar_pipeline_sinais(horas=1),
            "rotinas": self.gerar_estado_rotinas(),
            "alertas": self.gerar_feed_alertas(),
            "metricas_rapidas": {
                "sinais_hoje": self.db.contar_sinais_hoje(),
                "apostas_pendentes": self.db.contar_apostas_pendentes(),
                "subscritores_ativos": self.db.contar_subscritores_ativos(),
                "mensagens_fila_telegram": self.redis.llen("fila_telegram")
            }
        }
```

## Thresholds e Tabelas

| Componente | Status OK | Status DEGRADED | Status DOWN | Latência Alerta | Uptime Alerta |
|-----------|-----------|-----------------|-------------|-----------------|---------------|
| NBA Stats API | Lat < 5s | Lat 5-10s | Lat > 10s ou falha | > 5s | < 99% |
| Odds API | Lat < 3s | Lat 3-5s | Lat > 5s ou falha | > 3s | < 99.5% |
| Injuries API | Lat < 10s | Lat 10-30s | Lat > 30s | > 10s | < 98% |
| Model API | Lat < 200ms | Lat 200-500ms | Lat > 500ms | > 200ms | < 99.9% |
| Signals API | Lat < 100ms | Lat 100-300ms | Lat > 300ms | > 100ms | < 99.9% |
| PostgreSQL | Lat < 50ms | Lat 50-100ms | Lat > 100ms | > 50ms | < 99.9% |
| Redis | Lat < 10ms | Lat 10-50ms | Lat > 50ms | > 10ms | < 99.9% |
| Telegram Bot | Heartbeat < 60s | Heartbeat 60-180s | Heartbeat > 180s | > 60s | < 99% |
| Circuit Breaker | CLOSED | HALF-OPEN | OPEN | — | — |

| Etapa Pipeline | SLA Máximo | Threshold Alerta | Ação em Falha |
|---------------|-----------|-----------------|---------------|
| Deteção Oportunidade | 1 min | > 2 min | Verificar feed odds |
| Validação Modelo | 500 ms | > 1 s | Verificar API modelo |
| Verificação CB | 100 ms | > 500 ms | Verificar sistema risco |
| Cálculo Edge | 200 ms | > 500 ms | Fallback para edge simples |
| Verificação Odd | 1 s | > 3 s | Verificar bookmaker API |
| Formatação Mensagem | 100 ms | > 500 ms | Template padrão |
| Envio Telegram | 5 s | > 10 s | Alerta ops + fila retry |
| Confirmação Entrega | 10 s | > 30 s | Verificar bot health |

## Riscos
- **Risco de Falso Negativo**: Um componente pode estar "UP" no dashboard mas entregar dados incorretos (ex: feed de odds a responder em 1s mas com odds de ontem). Health checks devem validar conteúdo, não apenas latência.
- **Risco de Overhead**: Polling de 5 segundos em 10 componentes pode gerar carga significativa. Usar push/webhooks quando possível.
- **Risco de Indisponibilidade do Próprio Dashboard**: Se o NOC cair, a equipa fica cega. O dashboard deve ter redundância (instância standby) e deve ser leve o suficiente para correr em local.
- **Risco de Informação Excessiva**: Demasiados ecrãs ou demasiados dados num ecrã reduzem a eficácia. Layout deve seguir princípios de information hierarchy.

## Checklist do Operations Center
- [ ] Dashboard projetado em ecrã físico na sala de operações; layout testado para legibilidade à distância.
- [ ] Atualização automática a cada 5 segundos; fallback para 30 segundos se a carga for elevada.
- [ ] Alertas sonoros configurados para P1 (som crítico) e P2 (som de aviso); P3 apenas visual.
- [ ] Reconhecimento de alertas diretamente no dashboard (botão "ACK") que sincroniza com [[18_Operations/GESTAO_ALERTAS]].
- [ ] Histórico de 24h visível para todos os componentes; tendência de latência em gráfico de linha.
- [ ] Modo "Incidente": quando um P1 é ativado, o dashboard foca automaticamente no componente afetado e no runbook associado.
- [ ] Acesso remoto via VPN + SSO; logs de acesso ao dashboard arquivados por 90 dias.
- [ ] Teste de failover mensal: desligar componente em staging e verificar se dashboard reflete corretamente.

## Links Cruzados
- [[18_Operations/ROTINA_DIARIA]] - Rotinas cujo estado é mostrado no dashboard.
- [[18_Operations/GESTAO_ALERTAS]] - Sistema de alertas integrado no NOC.
- [[19_Telegram_System/BOT_TELEGRAM_CONFIG]] - Estado do bot monitorizado.
- [[26_Runbooks/RB-001_Feed_Dados_Offline]] até [[RB-010]] - Runbooks associados a falhas de componentes.
- [[33_Alerting/THRESHOLDS_ALERTAS]] - Thresholds que alimentam os alertas do dashboard.
