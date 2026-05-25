# PIPELINE_ETL_NBA — Ingestão de Dados

**ID:** `DE-001` | **Fase:** #phase/1 | **Owner:** Lead Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Recolher, validar e persistir todos os dados necessários para o sistema de value betting na NBA. O pipeline deve ser idempotente (execuções repetidas produzem o mesmo resultado), auditável (todas as transformações são rastreáveis) e garantir zero look-ahead leakage (nenhum dado do futuro é usado no treino). O objetivo é建立一个robusto e confiável pipeline de dados que sirva como fundação para todas as operações downstream, incluindo treino de modelos, backtesting, e execução em produção.

---

## 2. POR QUE UM PIPELINE ETL?

### 2.1 O Problema de Dados Desorganizados

Sem um pipeline ETL estruturado:
- Dados estão espalhados em múltiplas fontes (APIs, scraping, arquivos CSV)
- Não há garantia de qualidade ou consistência
- Difícil rastrear de onde veio cada dado
- Impossível reproduzir resultados
- Alto risco de leakage temporal
- Difícil detectar problemas quando ocorrem

### 2.2 Benefícios do Pipeline ETL

**Centralização:**
- Todos os dados fluem através de um pipeline controlado
- Single source of truth para cada tipo de dado
- Fácil de monitorizar e debugar

**Qualidade Garantida:**
- Validações automáticas em cada etapa
- Detecção de anomalias e outliers
- Alertas automáticos quando dados são suspeitos

**Reproducibilidade:**
- Cada transformação é documentada e versionada
- Possível reproduzir qualquer estado de dados
- Auditoria completa de todas as mudanças

**Performance:**
- Dados são pré-processados para queries rápidas
- Índices otimizados para padrões de acesso
- Batch processing eficiente

---

## 3. FONTES DE DADOS

### 3.1 Visão Geral

| Fonte | Dados | Frequencia | Metodo | Custo | Prioridade |
|-------|-------|------------|--------|-------|------------|
| nba_api (Python) | Play-by-play, box scores, jogadores, equipas | Diario (pos-jogo) | API oficial | Gratuito | Alta |
| Basketball-Reference | Four Factors, ratings avançados, calendario | Diario | Web scraping / CSV export | Gratuito | Alta |
| ESPN Injury Report | Lesoes, status jogadores | 2x/dia | RSS + scraping | Gratuito | Alta |
| Betfair Exchange API | Odds em tempo real | A cada 5 min (jogo dia) | API oficial | Gratuito (dev) | Alta |
| Pinnacle (proxy) | Odds de fecho historicas | Batch historico | Kaggle / Repositorios publicos | Gratuito | Média |
| NBA.com/stats | Estatisticas avancadas oficiais | Diario | API nba_api wrapper | Gratuito | Média |

### 3.2 Detalhes por Fonte

**nba_api (Python):**
- **O que fornece:** Dados oficiais da NBA incluindo play-by-play, box scores, estatísticas de jogadores e equipas, calendário de jogos
- **Por que usar:** Fonte oficial, atualizada em tempo real, gratuita, bem documentada
- **Limitações:** Rate limiting, ocasionalmente down para manutenção
- **Mitigação:** Caching local, retry com exponential backoff, fontes alternativas

**Basketball-Reference:**
- **O que fornece:** Four Factors, ratings avançados ( offensive/defensive rating), calendário histórico, dados históricos longos
- **Por que usar:** Métricas avançadas não disponíveis na NBA API, dados históricos completos
- **Limitações:** Scraping pode ser bloqueado, estrutura de HTML pode mudar
- **Mitigação:** Caching agressivo, monitorização de mudanças de HTML, export CSV manual como backup

**ESPN Injury Report:**
- **O que fornece:** Status de lesões de jogadores, expected return date
- **Por que usar:** Informações críticas que afetam performance de equipas
- **Limitações:** Nem sempre atualizado, inconsistências entre fontes
- **Mitigação:** Cruzar com múltiplas fontes (NBA API, team websites), flag de confiança

**Betfair Exchange API:**
- **O que fornece:** Odds em tempo real para mercados NBA, volume de liquidez
- **Por que usar:** É onde executamos apostas, odds mais líquidas e precisas
- **Limitações:** Rate limiting, requer autenticação, apenas dados recentes (histórico limitado)
- **Mitigação:** Rate limiting respeitado, caching de odds históricas, fontes alternativas para histórico

**Pinnacle (proxy):**
- **O que fornece:** Odds de fecho históricas para backtesting
- **Por que usar:** Pinnacle é considerada a "sharp" house, odds de fechamento são excelentes benchmark
- **Limitações:** Não é acesso direto à API (via Kaggle ou repositórios públicos), pode não estar atualizado
- **Mitigação:** Validar qualidade de dados, cruzar com outras fontes, atualizar regularmente

**NBA.com/stats:**
- **O que fornece:** Estatísticas avançadas oficiais (player tracking, shot charts)
- **Por que usar:** Métricas oficiais de alta qualidade
- **Limitações:** Algumas métricas requerem subscription, rate limiting
- **Mitigação:** Usar apenas métricas gratuitas para MVP, considerar subscription para escala

---

## 4. ARQUITETURA DO PIPELINE

### 4.1 Visão Geral

```
Cron (30 min em dias de jogo / 1x/dia offseason)
       |
       v
+----------------+     +----------------+     +----------------+
|  EXTRACT       | --> |  TRANSFORM     | --> |  LOAD          |
|  (Bronze)      |     |  (Silver)      |     |  (Gold/Prod)   |
+----------------+     +----------------+     +----------------+
       |                       |                      |
       v                       v                      v
  Raw JSON/CSV           Normalizado             Feature Store
  Tabelas raw_*          Tabelas clean_*         + model ready
  (Imutável)            (Deduplicado)           (Pronto para uso)
```

### 4.2 Camada Bronze (Extract)

**Objetivo:** Ingerir dados brutos de fontes externas sem modificação.

**Características:**
- Dados são armazenados exatamente como recebidos da fonte
- Nunca modificados após ingestão (imutabilidade)
- Retenção indefinida (nunca apagar dados brutos)
- Particionado por data para eficiência de queries

**Tabelas Bronze:**
- `raw_nba_games`: Jogos da NBA como recebidos da NBA API
- `raw_nba_boxscores`: Box scores brutos
- `raw_nba_playbyplay`: Play-by-play bruto
- `raw_basketball_reference`: Dados do scraping de Basketball-Reference
- `raw_injuries`: Dados de lesões brutos
- `raw_odds_betfair`: Odds brutas da Betfair
- `raw_odds_pinnacle`: Odds históricas do Pinnacle

### 4.3 Camada Silver (Transform)

**Objetivo:** Normalizar, limpar e deduplicar dados.

**Características:**
- Dados normalizados (tipos consistentes, formatos padronizados)
- Deduplicação (remover registros duplicados)
- Validação de qualidade (range checks, null checks)
- Enriquecimento (adicionar campos derivados)
- Retenção de 5 anos (dados mais antigos arquivados)

**Tabelas Silver:**
- `clean_games`: Jogos normalizados com info básica
- `clean_team_stats`: Estatísticas de equipa por jogo
- `clean_player_availability`: Status de lesão por dia
- `clean_odds`: Odds normalizadas com probabilidades implícitas
- `clean_schedule`: Calendário com back-to-backs e rest days

### 4.4 Camada Gold (Load)

**Objetivo:** Preparar dados para consumo downstream (treino de modelos, backtesting, produção).

**Características:**
- Features calculadas e agregadas
- Pronto para uso direto por modelos
- Otimizado para performance de queries
- Versionado para reproducibilidade

**Tabelas Gold:**
- `features_training`: Features prontas para treino de modelos
- `features_inference`: Features prontas para inferência em produção
- `features_backtest`: Features para backtesting

---

## 5. FLUXO DE DADOS POR TIPO

### 5.1 Jogos e Resultados (nba_api)

```python
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2

# Jogos por epoca
games = leaguegamefinder.LeagueGameFinder(
    season_nullable='2023-24',
    league_id_nullable='00'
).get_data_frames()[0]

# Box score por jogo (apos final)
box = boxscoretraditionalv2.BoxScoreTraditionalV2(
    game_id='0022300001'
).get_data_frames()[0]
```

**Regra de Ouro:** Box scores só são ingeridos após o jogo ter terminado (status final). Nunca durante o jogo. Isto previne look-ahead leakage onde dados do jogo em tempo real seriam usados para prever o resultado do mesmo jogo.

**Validações:**
- Verificar que status do jogo é "Final" antes de ingerir
- Verificar que todos os jogadores têm estatísticas completas
- Verificar que pontuação total é consistente com play-by-play

### 5.2 Estatísticas Avançadas (Basketball-Reference)

```python
import pandas as pd

# Four Factors por equipa
url = f"https://www.basketball-reference.com/leagues/NBA_2024.html"
tables = pd.read_html(url)
four_factors = tables[2]  # Team Per 100 Possessions
```

**Backoff Strategy:** Se scraping falhar, usar cache de 24h e alertar. Não falhar o pipeline inteiro por falha de uma fonte não-crítica.

**Validações:**
- Verificar que número de equipas é 30 (NBA tem 30 equipas)
- Verificar que Four Factors somam a valores razoáveis
- Verificar que dados são para a temporada correta

### 5.3 Lesões (ESPN + nba_api)

```python
from nba_api.stats.endpoints import commonteamroster, playerprofilev2

# Status de lesao vem de ESPN RSS + nba_api injury report
# Normalizado para: AVAILABLE, QUESTIONABLE, DOUBTFUL, OUT, INJURED
```

**Normalização de Status:**
- **AVAILABLE:** Jogador esperado para jogar
- **QUESTIONABLE:** 50% de chance de jogar
- **DOUBTFUL:** 25% de chance de jogar
- **OUT:** Não vai jogar
- **INJURED:** Lesão grave, fora por período prolongado

**Validações:**
- Verificar que status está na lista permitida
- Verificar que jogador existe na NBA
- Cruzar com múltiplas fontes para consistência

### 5.4 Odds (Betfair Exchange)

```python
import requests

# Betfair API endpoint para listar mercados
def get_betfair_odds(market_id):
    headers = {"X-Application": BETFAIR_APP_KEY}
    # ... chamada API
```

**Rate Limiting:**
- Respeitar limites da API (10 req/s para Betfair)
- Implementar exponential backoff em caso de falha
- Cache de odds para evitar requests duplicados

**Validações:**
- Verificar que odds estão em range razoável (1.01 - 1000)
- Verificar que volume de liquidez é suficiente
- Verificar que mercado ainda está aberto (não suspenso)

---

## 6. SCHEMA BRONZE (RAW)

### 6.1 Princípios

Todas as tabelas raw têm prefixo `raw_` e guardam dados exatamente como recebidos. Nunca são modificados após ingestão (imutabilidade). Isto garante que sempre podemos voltar aos dados originais para auditoria ou debugging.

### 6.2 Tabelas Bronze

| Tabela | Fonte | Retencao | Particionamento |
|--------|-------|----------|----------------|
| raw_nba_games | nba_api | Indefinida | Por temporada |
| raw_nba_boxscores | nba_api | Indefinida | Por data |
| raw_nba_playbyplay | nba_api | Indefinida | Por data |
| raw_basketball_reference | scraping | Indefinida | Por temporada |
| raw_injuries | ESPN + nba_api | Indefinida | Por data |
| raw_odds_betfair | Betfair API | Indefinida | Por data |
| raw_odds_pinnacle | Kaggle/publico | Indefinida | Por temporada |

### 6.3 Schema Exemplo (raw_nba_games)

```sql
CREATE TABLE raw_nba_games (
    id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    game_id VARCHAR(20) NOT NULL,
    season VARCHAR(10) NOT NULL,
    game_date DATE NOT NULL,
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    game_status VARCHAR(20),
    raw_payload JSONB
) PARTITION BY RANGE (game_date);
```

---

## 7. SCHEMA SILVER (CLEAN)

### 7.1 Princípios

Dados normalizados, deduplicados, com tipos corretos. Camada Silver é onde a qualidade de dados é garantida através de validações e limpeza.

### 7.2 Tabelas Silver

| Tabela | Chave | Conteudo | Validações |
|--------|-------|----------|------------|
| clean_games | game_id | Info basica do jogo (data, equipas, local, resultado) | Duplicados, nulls, range checks |
| clean_team_stats | game_id + team_id + stat_type | Estatisticas de equipa por jogo | Valores razoáveis, consistência |
| clean_player_availability | player_id + date | Status de lesao por dia | Status válido, consistência temporal |
| clean_odds | game_id + market + bookmaker + timestamp | Odds historico | Odds válidas, overround razoável |
| clean_schedule | season + team_id + date | Calendario com back-to-backs | Sem sobreposição, dias de descanso |

### 7.3 Schema Exemplo (clean_games)

```sql
CREATE TABLE clean_games (
    game_id VARCHAR(20) PRIMARY KEY,
    season VARCHAR(10) NOT NULL,
    game_date DATE NOT NULL,
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    home_score INTEGER NOT NULL,
    away_score INTEGER NOT NULL,
    winner VARCHAR(100),
    home_team_id VARCHAR(20),
    away_team_id VARCHAR(20),
    venue VARCHAR(100),
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_season FOREIGN KEY (season) REFERENCES seasons(season)
);

CREATE INDEX idx_clean_games_date ON clean_games(game_date);
CREATE INDEX idx_clean_games_team ON clean_games(home_team, away_team);
```

---

## 8. VALIDAÇÕES OBRIGATÓRIAS

### 8.1 Validações de Pipeline

```python
# Apos cada run do pipeline
def validate_pipeline():
    # Verificar que não houve perda de dados
    assert count_raw_games() == count_clean_games(), "Perda de jogos na transformacao"
    
    # Verificar que não há look-ahead leakage
    assert no_future_games_in_train(), "Look-ahead detectado!"
    
    # Verificar qualidade de dados
    assert all_odds_positive(), "Odds invalidas detectadas"
    assert injury_status_valid(), "Status de lesao invalido"
    
    # Verificar integridade referencial
    assert all_players_exist(), "Jogadores inexistentes detetados"
    assert all_teams_exist(), "Equipas inexistentes detetadas"
```

### 8.2 Validações de Qualidade de Dados

**Validações de Range:**
- Odds: 1.01 ≤ odd ≤ 1000
- Pontuação: 0 ≤ pontos ≤ 200
- Estatísticas: valores razoáveis para cada métrica
- Volume: volume ≥ 0

**Validações de Consistência:**
- Pontuação total = soma de pontos home + away
- Estatísticas de equipa = soma de estatísticas de jogadores
- Calendário sem sobreposição de jogos para mesma equipa

**Validações de Integridade:**
- Todas as FKs são válidas
- Não há orfãos (registros sem referência)
- Timestamps são cronologicamente consistentes

---

## 9. MONITORIZAÇÃO E ALERTAS

### 9.1 Métricas de Pipeline

**Métricas de Sucesso:**
- Taxa de sucesso de ingestão (% de runs bem-sucedidos)
- Latência de pipeline (tempo de execução)
- Volume de dados ingerido (registros por run)
- Taxa de falhas de validação

**Métricas de Qualidade:**
- Percentagem de dados que passam validações
- Percentagem de dados com missing values
- Percentagem de dados duplicados
- Percentagem de dados com outliers

### 9.2 Alertas

**Alertas Críticos:**
- Pipeline falha completamente → Telegram imediato
- Look-ahead leakage detetado → Telegram imediato + parar pipeline
- Fonte de dados down por > 1 hora → Telegram
- Dados corrompidos detetados → Telegram

**Alertas de Warning:**
- Alta taxa de falhas de validação → Email diário
- Latência de pipeline aumentando → Email diário
- Volume de dados anormal → Email diário
- Fonte de dados com delays → Email diário

---

## 10. BACKLOG TÉCNICO

- [ ] Implementar extrator nba_api com retry e backoff
- [ ] Implementar extrator Basketball-Reference com caching
- [ ] Implementar feed de odds Betfair com websocket fallback
- [ ] Criar sistema de deduplicação de jogos (multiplas fontes)
- [ ] Implementar snapshots diários (backup logico)
- [ ] Criar dashboard de health do pipeline (Grafana)
- [ ] Implementar sistema de alertas (Prometheus + Alertmanager)
- [ ] Criar testes automatizados de qualidade de dados
- [ ] Implementar sistema de versionamento de schemas
- [ ] Criar documentação de lineage de dados

---

## 10. IMPLEMENTAÇÃO COMPLETA

### 10.1 Script Robusto de Pipeline ETL
```python
"""
Pipeline ETL completo para dados NBA
Inclui Extract, Transform, Load com logging, error handling e métricas
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import json
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Extractor(ABC):
    """Classe abstrata para extratores de dados"""
    
    @abstractmethod
    def extract(self) -> pd.DataFrame:
        """Extrai dados da fonte"""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Retorna nome da fonte"""
        pass

class NBAAPIExtractor(Extractor):
    """Extrator para NBA API"""
    
    def __init__(self, season='2023-24'):
        self.season = season
        self.source_name = "NBA API"
    
    def extract(self) -> pd.DataFrame:
        """Extrai jogos da NBA API"""
        logger.info(f"🏀 Extraindo dados da {self.source_name} para temporada {self.season}...")
        
        try:
            from nba_api.stats.endpoints import leaguegamefinder
            
            gamefinder = leaguegamefinder.LeagueGameFinder(
                season_nullable=self.season
            )
            df = gamefinder.get_data_frames()[0]
            
            logger.info(f"✅ {len(df)} jogos extraídos")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados da {self.source_name}: {e}")
            return pd.DataFrame()
    
    def get_source_name(self) -> str:
        return self.source_name

class BasketballReferenceExtractor(Extractor):
    """Extrator para Basketball-Reference"""
    
    def __init__(self, season='2024'):
        self.season = season
        self.source_name = "Basketball-Reference"
    
    def extract(self) -> pd.DataFrame:
        """Extrai dados do Basketball-Reference"""
        logger.info(f"🏀 Extraindo dados do {self.source_name} para temporada {self.season}...")
        
        try:
            import pandas as pd
            
            url = f"https://www.basketball-reference.com/leagues/NBA_{self.season}.html"
            tables = pd.read_html(url)
            
            # Four Factors table (índice 2)
            four_factors = tables[2]
            
            logger.info(f"✅ {len(four_factors)} equipas extraídas")
            return four_factors
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados do {self.source_name}: {e}")
            return pd.DataFrame()
    
    def get_source_name(self) -> str:
        return self.source_name

class Transformer:
    """Transformador de dados"""
    
    def __init__(self):
        self.transformations_log = []
    
    def transform_games(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados de jogos"""
        logger.info("🔄 Transformando dados de jogos...")
        
        if df.empty:
            return df
        
        original_count = len(df)
        
        # Normalizar nomes de colunas
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Converter datas
        if 'game_date' in df.columns:
            df['game_date'] = pd.to_datetime(df['game_date'])
        
        # Remover duplicados
        if 'game_id' in df.columns:
            df = df.drop_duplicates(subset=['game_id'], keep='last')
        
        # Validar status - manter apenas jogos finalizados
        if 'game_status' in df.columns:
            valid_statuses = ['Final', 'Final/OT']
            df = df[df['game_status'].isin(valid_statuses)]
        
        logger.info(f"✅ Transformação completa ({original_count} → {len(df)} jogos)")
        
        self.transformations_log.append({
            'table': 'games',
            'original_count': original_count,
            'final_count': len(df),
            'timestamp': datetime.now().isoformat()
        })
        
        return df
    
    def transform_odds(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados de odds"""
        logger.info("🔄 Transformando dados de odds...")
        
        if df.empty:
            return df
        
        original_count = len(df)
        
        # Validar odds
        if 'odd' in df.columns:
            df = df[df['odd'] > 1.0]  # Remover odds ≤ 1.0
            df = df[df['odd'] <= 1000]  # Remover odds > 1000
        
        # Calcular probabilidade implícita
        if 'odd' in df.columns:
            df['implied_prob'] = 1 / df['odd']
        
        logger.info(f"✅ Transformação completa ({original_count} → {len(df)} odds)")
        
        self.transformations_log.append({
            'table': 'odds',
            'original_count': original_count,
            'final_count': len(df),
            'timestamp': datetime.now().isoformat()
        })
        
        return df

class Loader:
    """Carregador de dados para database"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string
        self.load_log = []
    
    def load_to_postgres(self, df: pd.DataFrame, table_name: str, if_exists='append'):
        """Carrega DataFrame para PostgreSQL"""
        logger.info(f"💾 Carregando dados para tabela {table_name}...")
        
        if df.empty:
            logger.warning(f"DataFrame vazio, skipping load para {table_name}")
            return
        
        try:
            from sqlalchemy import create_engine
            
            engine = create_engine(self.connection_string or 'postgresql://user:pass@localhost:5432/vbq')
            
            df.to_sql(table_name, engine, if_exists=if_exists, index=False)
            
            logger.info(f"✅ {len(df)} registos carregados para {table_name}")
            
            self.load_log.append({
                'table': table_name,
                'count': len(df),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados para {table_name}: {e}")
            raise
    
    def load_to_csv(self, df: pd.DataFrame, filepath: str):
        """Carrega DataFrame para CSV"""
        logger.info(f"💾 Carregando dados para CSV {filepath}...")
        
        try:
            df.to_csv(filepath, index=False)
            logger.info(f"✅ {len(df)} registos guardados em {filepath}")
            
            self.load_log.append({
                'format': 'csv',
                'filepath': filepath,
                'count': len(df),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Erro ao guardar CSV: {e}")
            raise

class ETLPipeline:
    """Pipeline ETL completo"""
    
    def __init__(self, connection_string: str = None):
        self.extractors = []
        self.transformer = Transformer()
        self.loader = Loader(connection_string)
        self.metrics = {
            'start_time': None,
            'end_time': None,
            'duration_seconds': None,
            'total_records_extracted': 0,
            'total_records_loaded': 0,
            'sources_processed': 0,
            'errors': []
        }
    
    def add_extractor(self, extractor: Extractor):
        """Adiciona extrator ao pipeline"""
        self.extractors.append(extractor)
        logger.info(f"Extrator adicionado: {extractor.get_source_name()}")
    
    def run(self, load_to_db: bool = False, output_dir: str = "output"):
        """Executa pipeline ETL completo"""
        logger.info("🚀 Iniciando pipeline ETL...")
        
        self.metrics['start_time'] = datetime.now()
        
        # Criar diretório de output
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Processar cada extrator
        for extractor in self.extractors:
            try:
                # Extract
                logger.info(f"\n📥 Extract: {extractor.get_source_name()}")
                df = extractor.extract()
                
                if df.empty:
                    logger.warning(f"⚠️  Nenhum dado extraído de {extractor.get_source_name()}")
                    continue
                
                self.metrics['total_records_extracted'] += len(df)
                
                # Transform
                logger.info(f"🔄 Transform: {extractor.get_source_name()}")
                if extractor.get_source_name() == "NBA API":
                    df = self.transformer.transform_games(df)
                elif 'odds' in extractor.get_source_name().lower():
                    df = self.transformer.transform_odds(df)
                
                # Load
                logger.info(f"💾 Load: {extractor.get_source_name()}")
                table_name = f"{extractor.get_source_name().lower().replace(' ', '_')}"
                
                if load_to_db:
                    self.loader.load_to_postgres(df, table_name)
                else:
                    csv_path = output_path / f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    self.loader.load_to_csv(df, str(csv_path))
                
                self.metrics['total_records_loaded'] += len(df)
                self.metrics['sources_processed'] += 1
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar {extractor.get_source_name()}: {e}")
                self.metrics['errors'].append({
                    'source': extractor.get_source_name(),
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        self.metrics['end_time'] = datetime.now()
        self.metrics['duration_seconds'] = (self.metrics['end_time'] - self.metrics['start_time']).total_seconds()
        
        # Resumo
        logger.info("\n📊 Resumo do Pipeline:")
        logger.info(f"  Fontes processadas: {self.metrics['sources_processed']}")
        logger.info(f"  Registros extraídos: {self.metrics['total_records_extracted']}")
        logger.info(f"  Registros carregados: {self.metrics['total_records_loaded']}")
        logger.info(f"  Duração: {self.metrics['duration_seconds']:.2f}s")
        logger.info(f"  Erros: {len(self.metrics['errors'])}")
        
        return self.metrics
    
    def generate_report(self) -> str:
        """Gera relatório do pipeline"""
        report = "# Relatório do Pipeline ETL\n\n"
        report += f"Gerado em: {datetime.now().isoformat()}\n\n"
        
        report += "## Métricas\n\n"
        for key, value in self.metrics.items():
            if key == 'errors' and value:
                report += f"{key}: {len(value)}\n"
            elif isinstance(value, datetime):
                report += f"{key}: {value.isoformat()}\n"
            elif isinstance(value, list) and not value:
                report += f"{key}: 0\n"
            else:
                report += f"{key}: {value}\n"
        
        report += "\n## Transformações\n\n"
        for log in self.transformer.transformations_log:
            report += f"- {log['table']}: {log['original_count']} → {log['final_count']}\n"
        
        report += "\n## Loads\n\n"
        for log in self.loader.load_log:
            report += f"- {log.get('table', log.get('format'))}: {log['count']} registos\n"
        
        return report

class PipelineValidator:
    """Validador de pipeline"""
    
    @staticmethod
    def validate_no_data_loss(raw_count: int, clean_count: int) -> bool:
        """Valida que não houve perda de dados"""
        loss = raw_count - clean_count
        loss_pct = (loss / raw_count * 100) if raw_count > 0 else 0
        
        if loss_pct > 10:
            logger.warning(f"⚠️  Perda de dados significativa: {loss_pct:.2f}% ({loss} registros)")
            return False
        
        return True
    
    @staticmethod
    def validate_no_lookahead(df: pd.DataFrame, date_column: str = 'game_date') -> bool:
        """Valida que não há look-ahead bias"""
        if date_column not in df.columns:
            return True
        
        df[date_column] = pd.to_datetime(df[date_column])
        today = pd.Timestamp.now().normalize()
        
        future_count = (df[date_column] > today).sum()
        
        if future_count > 0:
            logger.error(f"❌ Look-ahead bias detetado: {future_count} registos futuros")
            return False
        
        return True
    
    @staticmethod
    def validate_odds_range(df: pd.DataFrame, odd_column: str = 'odd') -> bool:
        """Valida range de odds"""
        if odd_column not in df.columns:
            return True
        
        invalid = (df[odd_column] <= 1.0) | (df[odd_column] > 1000)
        invalid_count = invalid.sum()
        
        if invalid_count > 0:
            logger.error(f"❌ {invalid_count} odds fora de range válido")
            return False
        
        return True

# Uso
if __name__ == "__main__":
    # Criar pipeline
    pipeline = ETLPipeline()
    
    # Adicionar extratores
    pipeline.add_extractor(NBAAPIExtractor(season='2023-24'))
    pipeline.add_extractor(BasketballReferenceExtractor(season='2024'))
    
    # Executar pipeline (sem DB para teste)
    metrics = pipeline.run(load_to_db=False, output_dir="output/etl")
    
    # Validar
    validator = PipelineValidator()
    
    # Gerar relatório
    report = pipeline.generate_report()
    print(report)
```

---

## 11. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]] ← Secção mãe
- [[04_Data_Engineering/DEDUPLICACAO_E_LIMPEZA]] → Regras de limpeza detalhadas
- [[04_Data_Engineering/VALIDACAO_DADOS]] → Validações de dados
- [[04_Data_Engineering/INGESTAO_ODDS]] → Ingestão específica de odds
- [[15_Database/INDEX]] → Schema detalhado PostgreSQL
- [[32_Feature_Store/INDEX]] → Features derivadas
