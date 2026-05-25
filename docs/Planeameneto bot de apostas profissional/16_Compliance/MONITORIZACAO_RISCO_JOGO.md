---
ID: CMP-010
tags: #status/active #compliance #responsible-gambling #monitorizacao #risco
---

# Monitorização de Risco de Jogo - Detalhamento Operacional

## Objetivo
Explicar em detalhe os procedimentos operacionais, métricas, intervenções e follow-up associados à monitorização contínua do comportamento de jogo dos subscritores, assegurando a deteção precoce de padrões de risco, a intervenção atempada, e a proteção de indivíduos vulneráveis, em conformidade com as melhores práticas da EGBA (European Gaming and Betting Association) e os códigos de conduta do SRIJ.

## Filosofia da Monitorização

A monitorização de risco de jogo baseia-se em três princípios fundamentais:

1. **Proatividade**: Intervir antes que o comportamento se torne problemático grave
2. **Proporcionalidade**: A intensidade da intervenção deve ser proporcional ao nível de risco
3. **Empatia**: Tratar o subscritor com dignidade, sem estigma, oferecendo apoio real

---

## Métricas de Risco Comportamental

### 1. Métricas de Volume

#### 1.1 Frequência de Apostas

**Definição:** Número de apostas colocadas por dia/semana/mês

**Thresholds:**
- **Normal:** 1-3 apostas/dia
- **Elevado:** 4-7 apostas/dia
- **Preocupante:** 8-15 apostas/dia
- **Crítico:** >15 apostas/dia

**Rationale:** Alta frequência pode indicar compulsividade e perda de controlo

**Dados necessários:**
- Timestamp de cada aposta recomendada
- Número de apostas colocadas (se disponível via integração)
- Padrão temporal (apostas espalhadas vs. concentradas)

**Implementação:**
```sql
SELECT subscritor_id, 
       COUNT(*) as apostas_24h,
       COUNT(DISTINCT DATE(data_hora)) as dias_ativos_7d
FROM sinais_enviados
WHERE data_hora >= NOW() - INTERVAL '24 hours'
GROUP BY subscritor_id
HAVING COUNT(*) > 8;
```

#### 1.2 Volume Financeiro (Stake)

**Definição:** Valor total apostado por período

**Thresholds (relativos ao perfil do subscritor):**
- **Normal:** 1-2x stake média histórica
- **Elevado:** 2-3x stake média histórica
- **Preocupante:** 3-5x stake média histórica
- **Crítico:** >5x stake média histórica

**Rationale:** Aumentos drásticos de stake podem indicar "chasing losses"

**Dados necessários:**
- Stake de cada aposta
- Stake média histórica do subscritor
- Rendimento disponível (se conhecido)

**Implementação:**
```sql
SELECT subscritor_id,
       AVG(stake) as stake_media_historica,
       AVG(stake) OVER (ORDER BY data_hora 
                        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as stake_media_7d,
       stake_media_7d / stake_media_historica as ratio_aumento
FROM sinais_enviados
WHERE data_hora >= NOW() - INTERVAL '7 days'
HAVING stake_media_7d / stake_media_historica > 3;
```

### 2. Métricas de Padrão Temporal

#### 2.1 Atividade Ininterrupta

**Definição:** Número de dias consecutivos com atividade de apostas

**Thresholds:**
- **Normal:** 1-3 dias consecutivos
- **Elevado:** 4-7 dias consecutivos
- **Preocupante:** 8-14 dias consecutivos
- **Crítico:** >14 dias consecutivos

**Rationale:** Atividade ininterrupta sugere obsessão e falta de pausas

**Dados necessários:**
- Data de cada aposta/sinal
- Padrão de pausas naturais (fim de semana, offseason)

**Implementação:**
```sql
WITH sequencias AS (
    SELECT subscritor_id,
           data_hora::date as data_aposta,
           data_hora::date - LAG(data_hora::date) OVER (PARTITION BY subscritor_id ORDER BY data_hora) as gap_dias
    FROM sinais_enviados
    WHERE data_hora >= NOW() - INTERVAL '30 days'
)
SELECT subscritor_id,
       SUM(CASE WHEN gap_dias = 1 THEN 1 ELSE 0 END) as dias_consecutivos_max
FROM sequencias
GROUP BY subscritor_id
HAVING SUM(CASE WHEN gap_dias = 1 THEN 1 ELSE 0 END) > 7;
```

#### 2.2 Horas de Atividade

**Definição:** Horas do dia em que o subscritor está ativo

**Padrões de risco:**
- **Atividade noturna:** Apostas entre 00:00-06:00
- **Atividade durante horário de trabalho:** Apostas durante 09:00-17:00 (se conhecido)
- **Atividade 24/7:** Distribuição uniforme por todas as horas

**Rationale:** Padrões atípicos podem indicar interferência com vida normal

**Dados necessários:**
- Timestamp de cada interação (sinal recebido, aposta colocada)
- Fuso horário do subscritor

**Implementação:**
```sql
SELECT subscritor_id,
       EXTRACT(HOUR FROM data_hora) as hora,
       COUNT(*) as atividades_hora
FROM sinais_enviados
WHERE data_hora >= NOW() - INTERVAL '30 days'
GROUP BY subscritor_id, EXTRACT(HOUR FROM data_hora)
ORDER BY subscritor_id, atividades_hora DESC;
```

### 3. Métricas de Resultado

#### 3.1 Drawdown Emocional

**Definição:** Perda acumulada num período curto (7-14 dias)

**Thresholds (percentual do bankroll estimado):**
- **Normal:** <10% drawdown
- **Elevado:** 10-25% drawdown
- **Preocupante:** 25-50% drawdown
- **Crítico:** >50% drawdown

**Rationale:** Drawdowns severos podem desencadear comportamento de chasing

**Dados necessários:**
- Histórico de resultados (win/loss)
- Bankroll estimado (se disponível)
- Stake de cada aposta

**Implementação:**
```sql
WITH resultados_cumulativos AS (
    SELECT subscritor_id,
           data_hora::date as data,
           SUM(CASE WHEN resultado = 'WIN' THEN stake * (odd - 1)
                    WHEN resultado = 'LOSS' THEN -stake
                    ELSE 0 END) 
           OVER (PARTITION BY subscritor_id ORDER BY data_hora) as resultado_cumulativo
    FROM sinais_enviados
    WHERE data_hora >= NOW() - INTERVAL '30 days'
)
SELECT subscritor_id,
       data,
       resultado_cumulativo,
       resultado_cumulativo - LAG(resultado_cumulativo) OVER (PARTITION BY subscritor_id ORDER BY data) as drawdown_diario
FROM resultados_cumulativos
WHERE drawdown_diario < 0;
```

#### 3.2 Sequência de Derrotas

**Definição:** Número consecutivo de apostas perdidas

**Thresholds:**
- **Normal:** 1-3 derrotas consecutivas
- **Elevado:** 4-6 derrotas consecutivas
- **Preocupante:** 7-10 derrotas consecutivas
- **Crítico:** >10 derrotas consecutivas

**Rationale:** Sequências longas de derrotas podem desencadear chasing losses

**Implementação:**
```sql
WITH sequencias_derrotas AS (
    SELECT subscritor_id,
           data_hora,
           resultado,
           CASE WHEN resultado = 'LOSS' 
                THEN ROW_NUMBER() OVER (PARTITION BY subscritor_id, 
                                        CASE WHEN resultado = 'LOSS' THEN 1 ELSE 0 END 
                                        ORDER BY data_hora)
                ELSE 0 END as sequencia_loss
    FROM sinais_enviados
    WHERE data_hora >= NOW() - INTERVAL '30 days'
)
SELECT subscritor_id,
       MAX(sequencia_loss) as max_sequencia_loss
FROM sequencias_derrotas
GROUP BY subscritor_id
HAVING MAX(sequencia_loss) > 5;
```

### 4. Métricas de Comportamento

#### 4.1 Tempo de Resposta a Sinais

**Definição:** Tempo entre receção do sinal e aposta colocada (se disponível)

**Thresholds:**
- **Normal:** 5-30 minutos
- **Elevado:** 1-5 minutos
- **Preocupante:** <1 minuto
- **Crítico:** <30 segundos (resposta quase instantânea)

**Rationale:** Respostas extremamente rápidas podem indicar obsessão/compulsividade

**Dados necessários:**
- Timestamp de envio do sinal
- Timestamp de aposta colocada (via integração)
- Timestamp de abertura do sinal (via tracking)

**Implementação:**
```sql
SELECT subscritor_id,
       AVG(tempo_resposta_segundos) as tempo_medio_resposta,
       MIN(tempo_resposta_segundos) as tempo_minimo_resposta
FROM interacoes_sinais
WHERE data_hora >= NOW() - INTERVAL '30 days'
GROUP BY subscritor_id
HAVING AVG(tempo_resposta_segundos) < 60;
```

#### 4.2 Múltiplas Contas

**Definição:** Detecção de subscritor com múltiplas contas

**Thresholds:**
- **Normal:** 1 conta
- **Elevado:** 2 contas (mesmo IP/dispositivo)
- **Preocupante:** 3 contas
- **Crítico:** >3 contas

**Rationale:** Múltiplas contas podem indicar evasão de limites ou fraude

**Dados necessários:**
- IP de registo/login
- Device fingerprint
- Dados de pagamento (cartão, IBAN)
- Padrões de comportamento

**Implementação:**
```sql
SELECT ip_registo,
       COUNT(DISTINCT subscritor_id) as contas_por_ip
FROM subscritores
WHERE data_criacao >= NOW() - INTERVAL '90 days'
GROUP BY ip_registo
HAVING COUNT(DISTINCT subscritor_id) > 1;
```

#### 4.3 Reclamações e Comportamento Hostil

**Definição:** Número de reclamações, tom de comunicação, comportamento agressivo

**Thresholds:**
- **Normal:** 0-1 reclamações/ano, tom respeitoso
- **Elevado:** 2-3 reclamações/ano, tom impaciente
- **Preocupante:** 4-5 reclamações/ano, tom hostil
- **Crítico:** >5 reclamações/ano, ameaças, linguagem abusiva

**Rationale:** Comportamento hostil pode indicar stress financeiro/emocional

**Dados necessários:**
- Registo de reclamações
- Análise de sentimento de comunicações
- Notas de equipa de suporte

**Implementação:**
```sql
SELECT subscritor_id,
       COUNT(*) as total_reclamacoes,
       COUNT(CASE WHEN sentimento = 'hostil' THEN 1 END) as reclamacoes_hostis
FROM reclamacoes
WHERE data >= NOW() - INTERVAL '12 months'
GROUP BY subscritor_id
HAVING COUNT(*) > 3 OR COUNT(CASE WHEN sentimento = 'hostil' THEN 1 END) > 0;
```

---

## Sistema de Pontuação de Risco

### Cálculo do Score de Risco

Cada métrica contribui para um score total de 0-100:

| Métrica | Peso | Pontuação Normal | Pontuação Elevado | Pontuação Preocupante | Pontuação Crítico |
|---------|------|------------------|-------------------|----------------------|-------------------|
| Frequência apostas/dia | 15 | 0-5 | 6-10 | 11-15 | 16-20 |
| Aumento stake | 20 | 0-5 | 6-10 | 11-15 | 16-20 |
| Dias consecutivos | 10 | 0-3 | 4-6 | 7-10 | 11-15 |
| Drawdown 7d | 15 | 0-4 | 5-8 | 9-12 | 13-15 |
| Sequência losses | 10 | 0-3 | 4-6 | 7-10 | 11-15 |
| Tempo resposta | 5 | 0-1 | 2 | 3 | 4-5 |
| Múltiplas contas | 15 | 0 | 5 | 10 | 15 |
| Reclamações | 10 | 0-2 | 3-5 | 6-8 | 9-10 |

**Níveis de Risco:**
- **VERDE (0-19):** Comportamento normal, sem intervenção necessária
- **AMARELO (20-39):** Comportamento elevado, alerta automático
- **LARANJA (40-59):** Comportamento preocupante, intervenção direta
- **VERMELHO (60-100):** Comportamento crítico, intervenção severa

---

## Intervenções por Nível de Risco

### Nível VERDE (Score 0-19)

**Ação:** Nenhuma

**Monitorização:** Contínua, automática

**Comunicação:** Nenhuma

---

### Nível AMARELO (Score 20-39)

**Ação Automática:**
- Envio de mensagem de autoavaliação
- Sugestão de limites de gasto
- Informação sobre ferramentas de controlo

**Mensagem Template:**
```
Olá [Nome],

Notámos que a tua atividade de apostas aumentou recentemente. Queremos garantir que estás a jogar de forma responsável.

Alguns recursos disponíveis:
- Define limites de depósito na tua conta de bookmaker
- Faz pausas regulares
- Lembra-te: aposte apenas o que pode perder

Se sentires que o jogo está a ter um impacto negativo, estás disponíveis estes recursos:
- PT: SRIJ - Linha Apoio Jogo (+351 213 893 700)
- UK: GambleAware (0808 8020 133)
- Geral: Gamblers Anonymous (www.gamblersanonymous.org)

Equipa de Jogo Responsável
[Nome Empresa]
```

**Ação Humana:**
- Revisão semanal pelo Responsible Gambling Officer
- Anotação no perfil do subscritor

**Follow-up:**
- Reavaliação em 7 dias
- Se score aumentar: escalonar para LARANJA
- Se score diminuir: continuar monitorização

---

### Nível LARANJA (Score 40-59)

**Ação Automática:**
- Limite temporário de stake (-50% da média)
- Pausa obrigatória de 7 dias
- Bloqueio de sinais durante pausa
- Mensagem de intervenção

**Mensagem Template:**
```
Olá [Nome],

Como parte do nosso compromisso com o jogo responsável, aplicámos temporariamente as seguintes medidas à tua conta:

1. Pausa de 7 dias no envio de sinais
2. Sugestão de redução do stake para 50% da tua média histórica

Estas medidas são preventivas e visam garantir que manténs controlo sobre a tua atividade de jogo.

Durante estes 7 dias, recomendamos:
- Refletir sobre os teus hábitos de jogo
- Considerar definir limites permanentes
- Contactar entidades de apoio se necessário

Se quiseres discutir estas medidas, estamos disponíveis em [email].

Equipa de Jogo Responsável
[Nome Empresa]
```

**Ação Humana:**
- Contacto direto por email em 24h
- Oferta de conversa com Responsible Gambling Officer
- Análise manual do perfil

**Follow-up:**
- Reavaliação após 7 dias
- Se score diminuir: remover limites
- Se score mantiver ou aumentar: escalar para VERMELHO
- Se subscritor solicitar reativação: avaliação manual

---

### Nível VERMELHO (Score 60-100)

**Ação Automática:**
- Bloqueio total de sinais
- Suspensão da conta
- Mensagem de autoexclusão sugerida
- Notificação à equipa

**Mensagem Template:**
```
Olá [Nome],

Devido a padrões de comportamento que indicam possível jogo problemático, suspendemos temporariamente o envio de sinais para a tua conta.

Recomendamos vivamente que consideres a autoexclusão, que pode ser ativada diretamente nos bookmakers ou através:

- PT: SRIJ - Linha Apoio Jogo (+351 213 893 700)
- UK: GamCare (www.gamcare.org.uk)
- Geral: Gamblers Anonymous (www.gamblersanonymous.org)

Se quiseres discutir esta decisão ou solicitar reativação, por favor contacta-nos em [email].

A tua saúde e bem-estar são mais importantes que qualquer aposta.

Equipa de Jogo Responsável
[Nome Empresa]
```

**Ação Humana:**
- Contacto telefónico em 24h (se número disponível)
- Oferta de encaminhamento para profissional de saúde
- Análise detalhada do perfil
- Registo detalhado no audit trail

**Follow-up:**
- Reativação apenas após avaliação manual
- Reativação condicional a:
  - Autoexclusão confirmada em bookmakers
  - Ou avaliação profissional positiva
  - Ou período mínimo de 30 dias sem atividade

---

## Parcerias com Entidades de Apoio

### Entidades em Portugal

| Entidade | Contacto | Serviços | Quando Referenciar |
|----------|----------|----------|-------------------|
| SRIJ - Linha Apoio Jogo | +351 213 893 700 | Aconselhamento, encaminhamento | Todos os casos PT |
| Jogadores Anónimos | www.jogadoresanonimos.pt | Grupos de apoio, 12 passos | Se subscritor pedir |
| APA | www.apartugal.org | Tratamento especializado | Casos graves |

### Entidades no Reino Unido

| Entidade | Contacto | Serviços | Quando Referenciar |
|----------|----------|----------|-------------------|
| GamCare | 0808 8020 133 | Aconselhamento, tratamento | Todos os casos UK |
| GambleAware | www.begambleaware.org | Informação, encaminhamento | Todos os casos UK |
| Gamblers Anonymous | www.gamblersanonymous.org.uk | Grupos de apoio | Se subscritor pedir |

### Entidades Internacionais

| Entidade | Contacto | Serviços | Quando Referenciar |
|----------|----------|----------|-------------------|
| Gamblers Anonymous International | www.gamblersanonymous.org | Grupos de apoio global | Subscritores fora PT/UK |

---

## Registo e Documentação

### Registo de Intervenções

Todas as intervenções devem ser registadas no audit trail com:

- Data e hora da intervenção
- Subscritor ID
- Score de risco antes/depois
- Tipo de intervenção
- Mensagem enviada (hash)
- Resposta do subscritor
- Responsável pela decisão
- Próxima data de reavaliação

### Retenção de Registos

- Registros de intervenções: 10 anos
- Comunicações com subscritores sobre RG: 10 anos
- Registros de autoexclusão: 10 anos após fim da relação

---

## Formação da Equipa

### Competências Necessárias

A equipa responsável por Responsible Gambling deve ter formação em:

1. **Detecção de padrões de risco:** Identificação de red flags
2. **Comunicação empática:** Como falar com jogadores em dificuldade
3. **Conhecimento de recursos:** Entidades de apoio disponíveis
4. **Procedimentos de emergência:** O que fazer em casos de crise

### Formação Anual

- **Módulo 1:** Atualização sobre melhores práticas RG (2 horas)
- **Módulo 2:** Treino de comunicação empática (2 horas)
- **Módulo 3:** Estudos de caso (2 horas)
- **Módulo 4:** Recursos de apoio atualizados (1 hora)

**Total:** 7 horas/ano por membro da equipa

---

## Métricas de Sucesso do Programa

### KPIs

| KPI | Target | Frequência |
|-----|--------|------------|
| % subscritores em intervenção | <5% | Mensal |
| Taxa de reativação após VERMELHO | <20% | Trimestral |
| Tempo médio de deteção de risco | <7 dias | Mensal |
| Satisfação com intervenções | N/A (qualitativo) | Trimestral |
| Referências para entidades de apoio | ≥50% casos VERMELHO | Trimestral |

---

## Links Cruzados

- [[16_Compliance/RESPONSIBLE_GAMBLING]] - Visão geral do programa de jogo responsável
- [[16_Compliance/AUDIT_TRAIL_COMPLIANCE]] - Registo de intervenções
- [[16_Compliance/COMUNICACAO_AUTORIDADES]] - Comunicação com SRIJ
- [[17_Legal/TERMS_OF_SERVICE]] - Cláusulas de jogo responsável nos ToS