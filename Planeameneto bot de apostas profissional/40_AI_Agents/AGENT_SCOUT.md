# Agent Scout

**ID:** AI-003 | **Fase:** #phase/9+ | **Owner:** Chief Systems Architect | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Agente de IA para parsing de lesões/notícias NBA e conversão em features de contexto. O Agent-Scout monitoriza feeds RSS e APIs, extrai informação estruturada, e enriquece o modelo com dados não-estruturados.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Parsing de lesões/notícias → features |
| **Stack** | LLM + NLP + RSS feeds + NBA API |
| **Custo** | ~$10/mês (API LLM) |

---

## 2. ARQUITETURA DO AGENTE

### 2.1 Fluxo de Coleta

```
┌─────────────────────────────────────────────────────────────┐
│ AGENT-SCOUT                                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. COLETA DE FONTES                                   │   │
│  │    - NBA Injury Report (API)                          │   │
│  │    - Twitter/X (API v2)                               │   │
│  │    - ESPN/BR API (RSS)                                │   │
│  │    - NBA.com (RSS)                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. FILTRAGEM DE RELEVÂNCIA                           │   │
│  │    - Equipas monitorizadas                            │   │
│  │    - Palavras-chave (injury, trade, etc.)            │   │
│  │    - Verificação de credibilidade                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. EXTRAÇÃO ESTRUTURADA (LLM)                        │   │
│  │    - Jogador afetado                                  │   │
│  │    - Tipo de lesão                                    │   │
│  │    - Severidade (questionable, probable, out)         │   │
│  │    - Tempo esperado de retorno                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. CONVERSÃO EM FEATURES                             │   │
│  │    - injury_status (0/1)                             │   │
│  │    - injury_severity (0-3)                           │   │
│  │    - expected_return_days (int)                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 5. ARMAZENAMENTO                                     │   │
│  │    - Tabela injury_context                           │   │
│  │    - Atualização em tempo real                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. CONFIGURAÇÃO DE FONTES

### 3.1 NBA Injury Report

```python
# vbq/agents/scout/sources/nba_injury.py
import requests

def fetch_nba_injury_report():
    """Busca relatório de lesões oficial da NBA"""
    url = "https://cdn.nba.com/static/json/latestInjuryReport.json"
    
    response = requests.get(url)
    response.raise_for_status()
    
    data = response.json()
    
    return data['resultSet']['rowSet']
```

### 3.2 Twitter/X API

```python
# vbq/agents/scout/sources/twitter.py
import tweepy

def fetch_twitter_mentions(team_abbreviations: list):
    """Busca menções de equipas no Twitter"""
    
    client = tweepy.Client(
        bearer_token=os.getenv('TWITTER_BEARER_TOKEN')
    )
    
    tweets = []
    
    for team in team_abbreviations:
        query = f"#{team} (injury OR trade OR rest)"
        
        response = client.search_recent_tweets(
            query=query,
            max_results=10,
            tweet_fields=['created_at', 'author_id']
        )
        
        tweets.extend(response.data)
    
    return tweets
```

### 3.3 ESPN RSS Feed

```python
# vbq/agents/scout/sources/espn_rss.py
import feedparser

def fetch_espn_news(team_abbreviations: list):
    """Busca notícias ESPN via RSS"""
    
    articles = []
    
    for team in team_abbreviations:
        url = f"http://www.espn.com/espn/rss/nba/team/_/name/{team}"
        
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            articles.append({
                'title': entry.title,
                'summary': entry.summary,
                'link': entry.link,
                'published': entry.published
            })
    
    return articles
```

---

## 4. EXTRAÇÃO ESTRUTURADA

### 4.1 Template de Prompt

```python
# vbq/agents/scout/llm_extractor.py
from openai import OpenAI

client = OpenAI()

def extract_injury_info(text: str, team: str) -> dict:
    """Extrai informação estruturada de lesão usando LLM"""
    
    prompt = f"""
És um especialista em NBA e análise de notícias de lesões.

TEXTO:
{text}

EQUIPA:
{team}

INSTRUÇÕES:
1. Identifica se há informação de lesão para esta equipa
2. Se houver, extrai:
   - Jogador (nome completo)
   - Tipo de lesão (ex: ankle, knee, hamstring)
   - Status (questionable, probable, out)
   - Tempo esperado de retorno (dias, se disponível)
3. Se não houver, retorna null

Formato JSON:
{{
  "has_injury": true/false,
  "players": [
    {{
      "name": "Nome do Jogador",
      "injury_type": "Tipo de lesão",
      "status": "questionable/probable/out",
      "expected_return_days": int ou null
    }}
  ]
}}

Responde apenas com JSON, sem texto adicional.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.1
    )
    
    import json
    return json.loads(response.choices[0].message.content)
```

### 4.2 Exemplo de Extração

```json
{
  "has_injury": true,
  "players": [
    {
      "name": "LeBron James",
      "injury_type": "ankle",
      "status": "questionable",
      "expected_return_days": 3
    },
    {
      "name": "Anthony Davis",
      "injury_type": "knee",
      "status": "out",
      "expected_return_days": null
    }
  ]
}
```

---

## 5. CONVERSÃO EM FEATURES

### 5.1 Mapeamento de Features

```python
# vbq/agents/scout/feature_mapper.py
def map_to_features(injury_info: dict, team: str, game_date: str) -> dict:
    """Converte informação de lesão em features"""
    
    features = {
        'team': team,
        'game_date': game_date,
        'has_injury': 0,
        'num_injured': 0,
        'injury_severity_score': 0,
        'expected_return_days_avg': 0
    }
    
    if not injury_info['has_injury']:
        return features
    
    features['has_injury'] = 1
    features['num_injured'] = len(injury_info['players'])
    
    # Calcular severity score
    severity_map = {'out': 3, 'questionable': 1, 'probable': 2}
    severity_scores = [severity_map.get(p['status'], 0) for p in injury_info['players']]
    features['injury_severity_score'] = sum(severity_scores) / len(severity_scores)
    
    # Calcular tempo médio de retorno
    return_days = [p['expected_return_days'] for p in injury_info['players'] if p['expected_return_days']]
    if return_days:
        features['expected_return_days_avg'] = sum(return_days) / len(return_days)
    
    return features
```

### 5.2 Exemplo de Features

```json
{
  "team": "LAL",
  "game_date": "2026-05-18",
  "has_injury": 1,
  "num_injured": 2,
  "injury_severity_score": 2.0,
  "expected_return_days_avg": 7.5
}
```

---

## 6. ARMAZENAMENTO

### 6.1 Tabela de Contexto

```sql
CREATE TABLE injury_context (
    id SERIAL PRIMARY KEY,
    team VARCHAR(10) NOT NULL,
    game_date DATE NOT NULL,
    has_injury BOOLEAN NOT NULL,
    num_injured INTEGER NOT NULL,
    injury_severity_score FLOAT NOT NULL,
    expected_return_days_avg FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team, game_date)
);
```

### 6.2 Inserção de Features

```python
# vbq/agents/scout/storage.py
from vbq.database.connection import get_db

def store_injury_features(features: dict):
    """Armazena features de lesão na BD"""
    
    db = get_db()
    
    db.execute("""
        INSERT INTO injury_context 
        (team, game_date, has_injury, num_injured, injury_severity_score, expected_return_days_avg)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (team, game_date) DO UPDATE SET
            has_injury = EXCLUDED.has_injury,
            num_injured = EXCLUDED.num_injured,
            injury_severity_score = EXCLUDED.injury_severity_score,
            expected_return_days_avg = EXCLUDED.expected_return_days_avg
    """, (
        features['team'],
        features['game_date'],
        features['has_injury'],
        features['num_injured'],
        features['injury_severity_score'],
        features['expected_return_days_avg']
    ))
```

---

## 7. AGENDAMENTO

### 7.1 Execução Periódica

```python
# vbq/agents/scout/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from vbq.agents.scout.sources.nba_injury import fetch_nba_injury_report
from vbq.agents.scout.sources.twitter import fetch_twitter_mentions
from vbq.agents.scout.sources.espn_rss import fetch_espn_news
from vbq.agents.scout.llm_extractor import extract_injury_info
from vbq.agents.scout.feature_mapper import map_to_features
from vbq.agents.scout.storage import store_injury_features

scheduler = BackgroundScheduler()

TEAMS = ['LAL', 'BOS', 'GSW', 'MIL', 'PHI', 'BKN', 'NYK', 'MIA']

def scout_task():
    """Tarefa de scouting"""
    
    # Coletar dados
    injury_report = fetch_nba_injury_report()
    tweets = fetch_twitter_mentions(TEAMS)
    articles = fetch_espn_news(TEAMS)
    
    # Processar cada equipa
    for team in TEAMS:
        # Extrair informação de lesão
        injury_info = extract_injury_info(str(injury_report), team)
        
        # Converter em features
        features = map_to_features(injury_info, team, date.today())
        
        # Armazenar
        store_injury_features(features)

scheduler.add_job(
    func=scout_task,
    trigger="interval",
    hours=2  # Executar a cada 2 horas
)

scheduler.start()
```

---

## 8. INTEGRAÇÃO COM MODELO

### 8.1 Features no Pipeline

```python
# vbq/features/feature_builder.py
def build_features(game_id: str) -> dict:
    """Constrói features para um jogo"""
    
    # Features base
    features = build_base_features(game_id)
    
    # Features de contexto de lesão
    injury_features = get_injury_context(features['home_team'], features['date'])
    features.update(injury_features)
    
    return features
```

---

## 9. CONFIGURAÇÃO

### 9.1 Variáveis de Ambiente

```bash
# .env
OPENAI_API_KEY=sk-...
TWITTER_BEARER_TOKEN=...
NBA_API_KEY=...
```

### 9.2 Configuração do Agente

```python
# vbq/agents/scout/config.py
import os

AGENT_SCOUT_CONFIG = {
    'openai_api_key': os.getenv('OPENAI_API_KEY'),
    'model': 'gpt-4o-mini',
    'max_tokens': 500,
    'temperature': 0.1,
    'check_interval_hours': 2,
    'teams': ['LAL', 'BOS', 'GSW', 'MIL', 'PHI', 'BKN', 'NYK', 'MIA']
}
```

---

## 10. TESTES

### 10.1 Teste de Extração

```python
# vbq/agents/scout/tests/test_extractor.py
def test_extract_injury_info():
    """Teste de extração de informação de lesão"""
    text = "LeBron James (ankle) is questionable for tonight's game"
    
    result = extract_injury_info(text, "LAL")
    
    assert result['has_injury'] == True
    assert len(result['players']) == 1
    assert result['players'][0]['name'] == "LeBron James"
    assert result['players'][0]['injury_type'] == "ankle"
```

---

## 11. LINKS CRUZADOS

- [[40_AI_Agents/INDEX]] ← Secção mãe
- [[40_AI_Agents/ASSISTENTE_ANALISE]] → Agente de análise
- [[42_Player_Props/USAGE_ROLE_CHANGES]] → Mudanças de uso e rotação
- [[04_Data_Engineering/INDEX]] → Engenharia de dados

---

**Custo de implementação:** ~$10/mês (API LLM + Twitter)  
**Tempo estimado de implementação:** 2 semanas  
**Prioridade:** MÉDIA (útil para contexto não-estruturado)
