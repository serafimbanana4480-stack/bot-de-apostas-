---
ID: OPS-003
tags: #status/active #operations #communication #team #handoff
---

# Comunicação da Equipa de Operações

## Objetivo
Definir os protocolos, canais, ritmos e formatos de comunicação interna da equipa de operações do sistema de value betting NBA, garantindo que a informação flui de forma eficiente, rastreável e acionável entre todos os membros da equipa, independentemente do fuso horário, turno, ou função específica. A comunicação operacional é a cola que mantém o sistema coerente face à complexidade e à velocidade do negócio.

## O que faz
- Estabelece canais de comunicação oficiais com finalidade definida: canais síncronos (Telegram ops, Discord ops) para urgências; canais assíncronos (Notion, Obsidian, e-mail) para documentação e decisões; reuniões rituais (standups, handoffs, retros) para alinhamento.
- Define o "Handoff Report" padronizado — documento obrigatório de passagem de turno que resume estado do sistema, alertas abertos, decisões tomadas, e tarefas pendentes.
- Especifica o formato e frequência de cada tipo de comunicação: daily standup, weekly review, monthly ops report, incident communication.
- Estabelece regras de escalada de comunicação: quando falar no canal geral vs. no privado, quando marcar uma call vs. enviar mensagem, quando acordar o gestor de operações.

## Porque existe
- **Continuidade em Turnos**: Value betting NBA opera numa janela que cruza noites e madrugadas em Portugal/Europa. A passagem de informação entre turnos é crítica para evitar perda de contexto.
- **Redução de Ruído**: Equipas de operações tendem a comunicar em demasia ("overcommunication") ou de menos. Canais bem definidos reduzem a sobrecarga cognitiva.
- **Responsabilização**: Comunicação informal ("falei com o João no café") não constitui prova de que a informação foi transmitida. Protocolos escritos criam accountability.
- **Cultura de Aprendizagem**: Reuniões de retrospectiva e postmortems documentadas transformam erros em conhecimento institucional.

## Implementação / Pseudocódigo
```python
class ComunicacaoEquipa:
    def __init__(self):
        self.canais = {
            "ops_geral": {"tipo": "Telegram", "finalidade": "Comunicação geral da equipa", "urgencia": "baixa", "hora_inicio": None, "hora_fim": None},
            "ops_alertas": {"tipo": "Telegram", "finalidade": "Alertas P1 e P2 apenas", "urgencia": "alta", "hora_inicio": None, "hora_fim": None},
            "ops_handoff": {"tipo": "Telegram", "finalidade": "Relatórios de handoff", "urgencia": "media", "hora_inicio": None, "hora_fim": None},
            "ops_oncall": {"tipo": "PagerDuty/Discord", "finalidade": "Escalada on-call", "urgencia": "critica", "hora_inicio": None, "hora_fim": None},
            "ops_documentacao": {"tipo": "Notion/Obsidian", "finalidade": "Documentação, decisões, SOPs", "urgencia": "baixa", "hora_inicio": None, "hora_fim": None},
            "ops_email": {"tipo": "E-mail", "finalidade": "Comunicação formal externa/interna", "urgencia": "media", "hora_inicio": "09:00", "hora_fim": "18:00"}
        }
        self.rituais = {
            "standup_diario": {"duracao_min": 15, "participantes": "toda_equipa", "horario": "14:00 UTC", "formato": "O que fiz / O que vou fazer / Bloqueios"},
            "handoff_turno": {"duracao_min": 10, "participantes": "operador_saida, operador_entrada", "horario": "19:00 UTC e 04:00 UTC", "formato": "Template padronizado"},
            "review_semanal": {"duracao_min": 60, "participantes": "toda_equipa + gestor", "horario": "Segunda 10:00 UTC", "formato": "Métricas da semana, alertas, melhorias"},
            "retro_mensal": {"duracao_min": 90, "participantes": "toda_equipa + gestor + stakeholders", "horario": "Última sexta do mês", "formato": "O que correu bem / O que pode melhorar / Ações"}
        }

    def gerar_handoff_report(self, operador_saida_id):
        operador = self.db.obter_operador(operador_saida_id)
        turno = self.obter_turno_atual(operador_saida_id)
        
        relatorio = {
            "timestamp": datetime.utcnow().isoformat(),
            "operador_saida": operador.nome,
            "turno": turno.nome,
            "estado_sistema": self.obter_estado_sistema(),
            "alertas_abertos": self.listar_alertas_abertos(),
            "alertas_resolvidos_turno": self.listar_alertas_resolvidos(turno.inicio, turno.fim),
            "tarefas_criticas_pendentes": self.listar_tarefas_criticas_pendentes(),
            "decisoes_tomadas": self.listar_decisoes_tomadas(turno.inicio, turno.fim),
            "anomalias_observadas": self.listar_anomalias(),
            "recomendacoes": self.listar_recomendacoes(),
            "proximos_eventos": self.listar_proximos_eventos(horas=24)
        }
        
        self.enviar_para_canal("ops_handoff", relatorio)
        self.arquivar_handoff(relatorio)
        return relatorio

    def avaliar_necessidade_escalada(self, alerta, minutos_desde_criacao):
        if alerta["severidade"] == "P1" and minutos_desde_criacao > 5:
            return {"escalar": True, "para": "gestor_operacoes", "canal": "ops_oncall", "mensagem": "P1 não ACK em 5 minutos"}
        elif alerta["severidade"] == "P2" and minutos_desde_criacao > 15:
            return {"escalar": True, "para": "gestor_operacoes", "canal": "ops_alertas", "mensagem": "P2 não ACK em 15 minutos"}
        elif alerta["categoria"] == "RISCO" and alerta["severidade"] in ["P1", "P2"]:
            return {"escalar": True, "para": "gestor_risco", "canal": "ops_alertas", "mensagem": "Alerta de risco crítico requer atenção imediata"}
        return {"escalar": False}

    def formatar_mensagem_incidente(self, incidente):
        return f"""
**[INCIDENTE] {incidente['id']} - {incidente['severidade']}**
- **Início**: {incidente['timestamp_inicio']}
- **Descrição**: {incidente['descricao']}
- **Impacto**: {incidente['impacto']}
- **Owner**: {incidente['owner'] or 'N/A'}
- **Status**: {incidente['status']}
- **Runbook**: {incidente.get('runbook', 'N/A')}
- **Comunicação externa necessária**: {'Sim' if incidente['comunicacao_externa'] else 'Não'}
"""

    def documentar_decisao(self, titulo, contexto, decisao, responsavel, stakeholders):
        registo = {
            "titulo": titulo,
            "data": datetime.utcnow().isoformat(),
            "contexto": contexto,
            "decisao": decisao,
            "responsavel": responsavel,
            "stakeholders": stakeholders,
            "revisao_prevista": (datetime.utcnow() + timedelta(days=90)).isoformat()
        }
        self.db.inserir("decisoes_operacionais", registo)
        self.notificar("ops_documentacao", f"Nova decisão documentada: {titulo}")
        return registo
```

## Thresholds e Tabelas

| Canal | Tipo | Finalidade | SLA de Resposta | Acessível 24/7 | Notificações |
|-------|------|-----------|-----------------|---------------|-------------|
| ops_geral | Telegram | Geral | 2 horas | Sim | Silenciadas 00:00-08:00 UTC |
| ops_alertas | Telegram | Alertas P1/P2 | 5 minutos | Sim | Sempre ativas |
| ops_handoff | Telegram | Handoffs | 30 minutos | Sim | Apenas em turnover |
| ops_oncall | PagerDuty/Discord | Escalada | 1 minuto | Sim | Call + push |
| ops_documentacao | Notion/Obsidian | Decisões/SOPs | 24 horas | Sim | N/A |
| ops_email | E-mail | Formal | 1 dia útil | Não | Horário laboral |

| Ritual | Frequência | Duração Máx | Obrigatório | Output |
|--------|-----------|-------------|-------------|--------|
| Standup Diário | Diário | 15 min | Sim | Notas no canal ops_geral |
| Handoff Turno | Por turnover | 10 min | Sim | Handoff Report arquivado |
| Review Semanal | Semanal | 60 min | Sim | Ações no backlog |
| Retrospectiva | Mensal | 90 min | Sim | Documento de melhorias |
| Postmortem | Pós-incidente P1 | 120 min | Sim (se P1) | [[27_Postmortems/EXEMPLO_POSTMORTEM]] |
| 1-on-1 | Mensal | 30 min | Recomendado | Notas privadas |

## Riscos
- **Risco de Comunicação Assíncrona Excessiva**: Equipas dispersas no tempo tendem a comunicar apenas por texto. Problemas complexos (ex: debug de modelo em produção) exigem calls síncronas; a ausência de protocolo para marcar calls retarda a resolução.
- **Risco de Informação em Silos**: Um operador resolve um alerta e não documenta a resolução; o mesmo alerta reaparece no turno seguinte e ninguém sabe o que fazer.
- **Risco de Fadiga On-Call**: On-call 24/7 sem rotação justa leva a burnout. A comunicação de escalada deve respeitar os limites humanos (ex: não acordar operador que já teve 3 chamadas essa noite).
- **Risco de Mensagens Privadas vs. Canais Públicos**: Decisões tomadas em DM privados não são acessíveis à equipa; perde-se a transparência e a possibilidade de auditoria.

## Checklist de Comunicação da Equipa
- [ ] Todos os operadores têm acesso a todos os canais oficiais e notificações configuradas corretamente.
- [ ] Calendário de on-call partilhado e visível; rotação semanal com backup designado.
- [ ] Template de Handoff Report preenchido em 100% dos turnovers; revisão semanal da qualidade dos handoffs.
- [ ] Standup diário realizado mesmo em dias sem incidentes; presença obrigatória > 80%.
- [ ] Decisões operacionais materiais (alteração de threshold, deploy de modelo, mudança de runbook) documentadas em [[18_Operations/DOCUMENTACAO_OPERACIONAL]].
- [ ] Comunicação de incidentes P1/P2 segue o template definido; nenhuma informação omitida.
- [ ] Reunião retrospectiva mensal produz lista de ações concretas com dono e prazo; follow-up no standup seguinte.
- [ ] Zero decisões operacionais importantes tomadas exclusivamente por DM; regra de ouro: "se afeta o sistema, vai para o canal ops_geral ou para a documentação".

## Links Cruzados
- [[18_Operations/ROTINA_DIARIA]] - Tarefas que alimentam os handoffs.
- [[18_Operations/GESTAO_ALERTAS]] - Alertas que disparam comunicação de escalação.
- [[18_Operations/DOCUMENTACAO_OPERACIONAL]] - Onde as decisões e SOPs são arquivadas.
- [[25_SOPs/SOP-001_Rotina_Diaria_Abertura]] e [[25_SOPs/SOP-002_Rotina_Diaria_Fecho]] - Rotinas que estruturam a comunicação.
