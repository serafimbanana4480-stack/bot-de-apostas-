# 40_AI Agents — INDEX

**ID:** `SEC-40` | **Fase:** #phase/8+ | **Owner:** Chief Systems Architect | **Status:** #status/active  
**Última Atualização:** `2026-05-13`

---

## 1. OBJETIVO

Explorar e implementar agentes de IA para assistência operacional — análise de pós-jogo, geração de relatórios, deteção de anomalias, enriquecimento de features com dados não-estruturados, e interação automatizada com subscritores.

**Princípio:** Agentes de IA apenas onde substituem trabalho manual repetitivo ou processam informação não-estruturada que o sistema quant não consegue processar. Nunca substituem o julgamento do operador em decisões críticas.

---

## 2. AGENTES PLANEADOS

| Agente | Função | Fase | Stack | Prioridade |
|--------|--------|------|-------|-----------|
| **Agent-Analyst** | Resumos diários automáticos de performance | 8 | GPT-4o-mini + SQL | Alta |
| **Agent-Monitor** | Deteção de anomalias em métricas e alertas explicativos | 8 | Regras + LLM para narração | Alta |
| **Agent-Scout** | Parsing de lesões/notícias NBA → features de contexto | 9 | LLM + NLP + RSS feeds | Média |
| **Agent-Support** | Responder a FAQs de subscritores Telegram | 10 | LLM + RAG sobre docs | Baixa |
| **Agent-Reviewer** | Revisão automática de qualidade de modelos pré-produção | 11 | LLM + MLflow API | Baixa |

---

## 3. AGENT-ANALYST (Fase 8) — Especificação

### 3.1 Função
Gerar diariamente um relatório de performance em linguagem natural, enviado às 08:00 UTC via Telegram para o operador.

### 3.2 Input
```python
context = {
    "date": "2026-10-15",
    "bets_yesterday": [...],    # Da tabela bets
    "pnl_yesterday": -12.50,
    "clv_yesterday": 2.1,
    "roi_7d": 3.8,
    "roi_30d": 4.2,
    "drawdown_current": -5.2,
    "model_brier": 0.231,
    "alerts_active": ["SlowIngestion"]
}
```

### 3.3 Output (Telegram)
```
📊 RELATÓRIO DIÁRIO — 2026-10-15

💰 PnL ontem: -€12.50 (3 apostas, 1 win)
📈 CLV ontem: +2.1% ✅
📉 ROI 7d: +3.8% | ROI 30d: +4.2%
⚠️ Drawdown atual: -5.2% (limite: -15%)

🤖 Análise: Ontem foi um dia negativo mas o CLV positivo
indica que as decisões foram corretas. A variância de curto
prazo é esperada com N=3 apostas. Continuar sem ajustes.

🔧 Alertas: 1 warning ativo (ingestão lenta)
```

### 3.4 Stack
```python
from openai import OpenAI

def generate_daily_report(context: dict) -> str:
    client = OpenAI()  # API key via env var
    prompt = f"""
    És um analista quant especializado em value betting NBA.
    Gera um relatório diário CONCISO (máx 200 palavras) com base nestes dados:
    {context}
    Inclui: resumo de ontem, tendências, e recomendação operacional.
    Tom: profissional, factual, sem exageros.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content
```

---

## 4. AGENT-SCOUT (Fase 9) — Especificação

### 4.1 Função
Monitorizar feeds RSS e APIs de notícias NBA, extrair informação estruturada (lesões, suspensões, mudanças de rotação) e convertê-la em features para o modelo.

### 4.2 Fontes
| Fonte | Tipo | Frequência |
|-------|------|-----------|
| NBA Injury Report (oficial) | PDF/API | 2x/dia |
| Twitter/X (jornalistas credenciados) | API v2 | A cada 30 min |
| ESPN/BR API | RSS | A cada hora |

### 4.3 Output
```python
{
    "game_id": "20261015_BOS_LAL",
    "injury_features": {
        "home_key_player_out": 1,     # 1 se jogador top-10 min ausente
        "away_key_player_out": 0,
        "home_fatigue_score": 0.7,    # Derivado de B2B + lesões
        "injury_uncertainty": 0.3     # Incerteza sobre lineup
    },
    "extracted_at": "2026-10-15T10:30:00Z",
    "confidence": 0.85
}
```

---

## 5. GUARDRAILS E LIMITES

| Guardrail | Razão |
|-----------|-------|
| Agentes não executam apostas | Execução manual ou automática separada |
| Agentes não alteram parâmetros de risco | Risk Manager humano necessário |
| Outputs de agentes são sempre auditáveis | Logs de todos os prompts e respostas |
| Fallback para regras simples se LLM falhar | Sem dependência crítica de APIs externas |
| Custo máximo por mês: 20€ (OpenAI API) | Monitorizar uso no dashboard |

---

## 6. DOCUMENTOS NESTA SECÇÃO

| Ficheiro | Conteúdo |
|----------|----------|
| [[40_AI_Agents/ASSISTENTE_ANALISE]] | Especificação detalhada do Agent-Analyst |

---

## 7. BACKLOG

- [ ] Implementar Agent-Analyst básico (Fase 8, sem RAG)
- [ ] Integrar com cron job 08:00 UTC
- [ ] Avaliar custo vs valor do Agent-Scout (Fase 9)
- [ ] Documentar política de uso de LLMs (custo, privacidade, fallback)

---

## 8. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[19_Telegram_System/INDEX]] → Canal de envio dos relatórios
- [[10_Monitoring/INDEX]] → Métricas que alimentam os agentes
- [[39_Automation/INDEX]] → Cron jobs dos agentes
