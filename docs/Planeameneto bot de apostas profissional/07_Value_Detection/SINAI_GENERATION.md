# SINAI_GENERATION — Pipeline de Geração de Sinais

**ID:** `VD-004` | **Fase:** #phase/2-3 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

O pipeline de geração de sinais é responsável por transformar as previsões do modelo e as odds do mercado em sinais de apostas acionáveis. Este pipeline deve ser:

- **Determinístico:** Mesmos inputs → mesmo output
- **Rápido:** Gerar sinais em segundos, não minutos
- **Robusto:** Lidar com falhas de dados sem crashar
- **Auditável:** Cada decisão deve ser traceável
- **Escalável:** Capaz de processar múltiplos jogos em paralelo

O sinal final é o produto final que será consumido pelo sistema de execução e, eventualmente, por usuários humanos via Telegram ou dashboard.

---

## 2. ARQUITETURA DO PIPELINE

### 2.1 Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUTS DO PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│ • Features do jogo (do Feature Store)                       │
│ • Probabilidade do modelo primário (calibrada)              │
│ • Odds de mercado em tempo real (Pinnacle/Betfair)          │
│ • Volume de liquidez (Betfair API)                          │
│ • Probabilidade do meta-modelo                              │
│ • Configuração de thresholds                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 ETAPA 1: VALIDAÇÃO DE DADOS                  │
├─────────────────────────────────────────────────────────────┤
│ • Verificar completude de features                          │
│ • Validar ranges de probabilidades                          │
│ • Checar integridade de odds                                │
│ • Confirmar timestamp atualidade                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 ETAPA 2: CÁLCULO DE EDGE                     │
├─────────────────────────────────────────────────────────────┤
│ • Normalizar odds (remover overround)                       │
│ • Calcular edge = (prob × odd) - 1                          │
│ • Ajustar edge à liquidez                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              ETAPA 3: APLICAÇÃO DE FILTROS                   │
├─────────────────────────────────────────────────────────────┤
│ • Filtro de probabilidade [0.15, 0.85]                      │
│ • Filtro de liquidez (1.5x stake)                           │
│ • Filtro de regime (blacklist)                              │
│ • Filtro de confiança meta (> 0.60)                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│            ETAPA 4: CÁLCULO DE STAKE (KELLY)                 │
├─────────────────────────────────────────────────────────────┤
│ • Calcular Kelly fracionado (K=0.5)                          │
│ • Aplicar limite máximo por aposta (2% da banca)            │
│ • Aplicar limite máximo diário (12% da banca)                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              ETAPA 5: GERAÇÃO DE RATIONALE                   │
├─────────────────────────────────────────────────────────────┤
│ • Compilar explicação do sinal                              │
│ • Incluir métricas chave (edge, confiança)                  │
│ • Adicionar contexto relevante (forma, injuries)             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT: SINAL FINAL                       │
├─────────────────────────────────────────────────────────────┤
│ • JSON estruturado com todos os campos                       │
│ • Timestamp de geração e expiração                          │
│ • Pronto para delivery via API/Webhook                       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Paralelização

O pipeline processa múltiplos jogos em paralelo usando:

- **Batch processing:** Processa grupos de jogos simultaneamente
- **Async I/O:** Chamadas de API não bloqueantes
- **Worker pools:** Múltiplos workers para CPU-bound operations

Isso permite processar todos os jogos do dia em < 30 segundos.

---

## 3. FORMATO DO SINAL

### 3.1 Estrutura JSON

O sinal é entregue em formato JSON estruturado:

```json
{
  "signal_id": "SIG-20261015-001",
  "timestamp_gerado": "2026-10-15T18:30:00Z",
  "timestamp_expiracao": "2026-10-15T18:35:00Z",
  "versao_modelo": "v2.3.1",
  
  "jogo": {
    "id": "NBA-20261015-BOS-LAL",
    "equipa_casa": "Boston Celtics",
    "equipa_fora": "LA Lakers",
    "data": "2026-10-15",
    "hora": "20:00",
    "local": "TD Garden, Boston",
    "regime": {
      "back_to_back": false,
      "injuries_casa": ["Marcus Smart (Questionable)"],
      "injuries_fora": ["LeBron James (Out)"]
    }
  },
  
  "mercado": {
    "tipo": "moneyline",
    "selecao": "Boston Celtics",
    "odd_recomendada": 1.85,
    "bookmaker": "Pinnacle",
    "exchange": "Betfair"
  },
  
  "analise": {
    "prob_modelo": 0.58,
    "prob_mercado_normalizada": 0.5317,
    "edge_estimado": 0.073,
    "edge_percentual": "7.3%",
    "prob_meta": 0.72,
    "confidence_score": 0.85,
    "liquidez_disponivel": 50000,
    "liquidez_ratio": 20.0
  },
  
  "stake": {
    "valor_eur": 25.00,
    "unidade_banca": 0.025,
    "metodo": "kelly_fracionado",
    "kelly_fraction": 0.5,
    "limite_aplicado": "nenhum"
  },
  
  "rationale": {
    "resumo": "Edge 7.3% em favorito moderado. Meta-modelo confiante (72%).",
    "detalhes": [
      "Celtics em forma excelente: 58% eFG% nos últimos 5 jogos",
      "Lakers sem LeBron James: impacto estimado de -8 pontos",
      "Celtics em casa: +3.2 pontos de home court advantage",
      "Modelo prevê 58% vs mercado 53%: discrepância significativa",
      "Meta-modelo 72% confiança: sinal validado"
    ],
    "alertas": [
      "Marcus Smart questionable: monitorizar lineup confirmado",
      "Lakers em back-to-back: fadiga pode afetar performance"
    ]
  },
  
  "metadados": {
    "fonte_features": "feature_store_v2",
    "fonte_odds": "pinnacle_api",
    "latencia_ms": 234,
    "filtros_aplicados": ["probabilidade", "liquidez", "regime", "meta"],
    "versao_pipeline": "v1.2.0"
  }
}
```

### 3.2 Campos Obrigatórios vs Opcionais

**Obrigatórios:**
- signal_id: Identificador único
- timestamp_gerado: Quando o sinal foi criado
- timestamp_expiracao: Quando o sinal expira
- jogo: Informações do jogo
- mercado: Tipo de mercado e seleção
- odd_recomendada: Odd para apostar
- analise: Métricas de análise
- stake: Quantidade a apostar

**Opcionais (mas recomendados):**
- rationale: Explicação do sinal
- metadados: Informações de debug
- alertas: Avisos e warnings

### 3.3 Validação de Schema

Todo sinal é validado contra um schema JSON antes de ser enviado:
- Todos os campos obrigatórios presentes
- Tipos de dados corretos
- Valores dentro de ranges esperados
- Timestamps válidos (geração < expiração)

---

## 4. MECANISMO DE EXPIRAÇÃO

### 4.1 Por que Expiração?

As odds de mercado mudam constantemente. Um sinal baseado numa odd de 1.85 pode não ter edge se a odd cair para 1.80. Portanto, cada sinal tem um tempo de validade.

### 4.2 Regras de Expiração

**Expiração padrão:** 5 minutos após geração

**Ajustes dinâmicos:**
- **Alta volatilidade:** 3 minutos (odds mudam rápido)
- **Baixa volatilidade:** 10 minutos (odds estáveis)
- **Próximo do evento:** 2 minutos (últimos minutos antes do jogo)

### 4.3 Mecanismo de Cancelamento

Se a odd mudar > 2% após geração do sinal:
1. Sistema detecta mudança via webhook
2. Recalcula edge com nova odd
3. Se edge cai abaixo de threshold → Sinal cancelado
4. Notificação enviada via Telegram/API

### 4.4 Timestamps

**timestamp_gerado:** Momento exato da geração do sinal
**timestamp_expiracao:** timestamp_gerado + tempo_validade
**timestamp_execucao:** Quando a aposta foi executada (se aplicável)

---

## 5. DELIVERY DE SINAIS

### 5.1 Canais de Delivery

Sinais são entregues através de múltiplos canais:

#### 5.1.1 API/Webhook (Primário)
- **Endpoint:** POST /api/v1/signals
- **Formato:** JSON
- **Autenticação:** API key
- **Rate limiting:** 100 requisições/minuto
- **Retry logic:** Exponential backoff em falhas

#### 5.1.2 Telegram (Secundário)
- **Bot:** @ValueBettingBot
- **Formato:** Mensagem formatada com emojis
- **Frequência:** Batch de sinais a cada 15 minutos
- **Interatividade:** Botões para confirmar/rejeitar

#### 5.1.3 Dashboard (Terciário)
- **Interface:** Web dashboard em tempo real
- **Atualização:** WebSocket para atualizações live
- **Histórico:** Últimos 100 sinais
- **Filtros:** Por mercado, edge, confiança

### 5.2 Priorização de Delivery

```
1. API/Webhook → Sistema de execução automático
2. Telegram → Notificação para usuários humanos
3. Dashboard → Visualização e análise
```

### 5.3 Garantia de Delivery

Para garantir que sinais não são perdidos:

- **Acknowledge:** Receptor deve confirmar recebimento
- **Retry:** Se não houver ack em 30s, reenviar
- **Dead letter queue:** Sinais não entregues após 3 tentativas vão para DLQ
- **Alerta:** Alerta operacional se DLQ > 10 sinais

---

## 6. SISTEMA DE RATIONALE

### 6.1 Objetivo do Rationale

O rationale explica POR QUE o sinal foi gerado. Isso é crucial para:

- **Confiança do usuário:** Entender a lógica atrás da aposta
- **Debugging:** Identificar problemas no modelo
- **Melhoria contínua:** Analisar o que funciona e o que não
- **Compliance:** Documentar decisões de apostas

### 6.2 Componentes do Rationale

#### 6.2.1 Resumo
Uma frase curta que captura a essência do sinal:
- "Edge 7.3% em favorito moderado. Meta-modelo confiante (72%)."

#### 6.2.2 Detalhes
Lista de fatores que suportam o sinal:
- Forma recente das equipas
- Injuries e roster changes
- Vantagens de casa/fora
- Discrepâncias entre modelo e mercado
- Validação do meta-modelo

#### 6.2.3 Alertas
Fatores de risco que devem ser monitorizados:
- Jogadores questionable
- Back-to-back games
- Condições meteorológicas (para outdoor sports)
- Mudanças recentes no coaching staff

### 6.3 Geração Automática

O rationale é gerado automaticamente usando templates:

```
Template: "Edge {edge}% em {tipo_aposta}. Meta-modelo {confiança}%."

Fatores:
- Se eFG% > média: "{equipa} em forma excelente: {eFG}% eFG% últimos 5 jogos"
- Se injury importante: "{equipa} sem {jogador}: impacto estimado de {impacto}"
- Se jogo em casa: "{equipa} em casa: +{hca} pontos de home court"
- Se discrepância > 5%: "Modelo prevê {p_modelo}% vs mercado {p_mercado}%: discrepância significativa"
```

---

## 7. MONITORIZAÇÃO E LOGGING

### 7.1 Métricas de Pipeline

Monitorizamos continuamente:

- **Latência:** Tempo médio de geração de sinal (target: < 5s)
- **Throughput:** Sinais gerados por minuto (target: > 10/min)
- **Taxa de aprovação:** % de sinais que passam filtros (target: 5-10%)
- **Taxa de expiração:** % de sinais que expiram antes de execução (target: < 5%)
- **Taxa de erro:** % de sinais com erro de geração (target: < 0.1%)

### 7.2 Logging Detalhado

Cada sinal gera logs detalhados:

```
[INFO] Signal SIG-20261015-001 generated
[INFO] Edge calculated: 0.073 (7.3%)
[INFO] Filters passed: probabilidade, liquidez, regime, meta
[INFO] Stake calculated: 25.00 EUR (2.5% of bankroll)
[INFO] Signal delivered via API: 200 OK
[INFO] Signal delivered via Telegram: Success
```

Logs são armazenados por 90 dias para auditoria.

### 7.3 Alertas

Alertas são gerados se:

- **Pipeline lento:** Latência > 30s por 5 minutos consecutivos
- **Taxa de erro alta:** > 1% de sinais com erro em 1 hora
- **Taxa de aprovação anormal:** < 2% ou > 20% por 24 horas
- **Delivery falha:** > 10% de sinais não entregues em 1 hora

---

## 8. BOAS PRÁTICAS

### 8.1 Idempotência

O pipeline deve ser idempotente: mesmos inputs → mesmo output, mesmo que executado múltiplas vezes. Isso permite re-execução em caso de falha sem duplicar sinais.

### 8.2 Versionamento

Cada sinal inclui a versão do modelo e do pipeline. Isso permite:
- Rastrear qual versão gerou cada sinal
- Reverter para versões anteriores se necessário
- Analisar performance por versão

### 8.3 Testes A/B

O pipeline suporta testes A/B:
- Sinais podem ser gerados com diferentes configurações
- Performance comparada em produção
- Melhor configuração selecionada automaticamente

### 8.4 Rollback

Se uma mudança no pipeline causar problemas:
- Rollback automático para versão anterior
- Sinais da versão problemática são marcados
- Análise post-mortem é iniciada

---

## 9. LINKS CRUZADOS

- [[07_Value_Detection/INDEX]] ← Seção mãe
- [[09_Execution_System/INDEX]] → Sistema que executa os sinais
- [[19_Telegram_System/INDEX]] → Delivery via Telegram
- [[20_Dashboarding/INDEX]] → Visualização de sinais
- [[08_Risk_Management/INDEX]] → Cálculo de Kelly e stakes