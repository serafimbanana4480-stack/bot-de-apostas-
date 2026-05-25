# VALIDAÇÃO DE DADOS E QUALIDADE

**ID:** `SEC-04-03` | **Fase:** #phase/1 | **Owner:** Data Engineer | **Status:** #status/pending  
**Última Atualização:** `2026-05-13`

---

## 1. PILARES DA QUALIDADE DE DADOS

| Pilar | Definição | Exemplo |
|-------|-----------|---------|
| **Completude** | Campos obrigatórios preenchidos | `odd_back` nunca NULL |
| **Precisão** | Valores dentro dos intervalos esperados | Odd entre 1.01 e 1000 |
| **Consistência** | Sem contradições entre tabelas | `home_team` igual no `raw_odds` e `games` |
| **Pontualidade** | Dados disponíveis quando necessários | Odds disponíveis ≥ 2h antes do jogo |
| **Unicidade** | Sem duplicados | Uma linha por `market_id + selection_id + hora` |
| **Validade** | Formato e tipos corretos | `game_date` é DATE, não VARCHAR |

---

## 2. FRAMEWORK: GREAT EXPECTATIONS

### 2.1 Estrutura
```
great_expectations/
├── expectations/
│   ├── raw_odds_suite.json         # Suite Bronze
│   ├── odds_cleaned_suite.json     # Suite Silver
│   ├── features_suite.json         # Suite Gold
│   └── player_stats_suite.json     # Suite stats jogadores
├── checkpoints/
│   ├── bronze_checkpoint.yml
│   ├── silver_checkpoint.yml
│   └── gold_checkpoint.yml
└── uncommitted/
    └── data_docs/                  # Relatórios HTML gerados
```

### 2.2 Exemplo de Expectation Suite (raw_odds)
```python
import great_expectations as ge

suite = ge.core.ExpectationSuite("raw_odds_suite")

# Completude
suite.add_expectation(ge.core.ExpectationConfiguration(
    expectation_type="expect_column_values_to_not_be_null",
    kwargs={"column": "market_id"}
))
suite.add_expectation(ge.core.ExpectationConfiguration(
    expectation_type="expect_column_values_to_not_be_null",
    kwargs={"column": "best_back_price"}
))

# Precisão — odds válidas
suite.add_expectation(ge.core.ExpectationConfiguration(
    expectation_type="expect_column_values_to_be_between",
    kwargs={"column": "best_back_price", "min_value": 1.01, "max_value": 1000.0}
))

# Unicidade
suite.add_expectation(ge.core.ExpectationConfiguration(
    expectation_type="expect_compound_columns_to_be_unique",
    kwargs={"column_list": ["market_id", "selection_id", "ingested_at"]}
))

# Validade — source conhecido
suite.add_expectation(ge.core.ExpectationConfiguration(
    expectation_type="expect_column_values_to_be_in_set",
    kwargs={"column": "source", "value_set": ["betfair", "theoddsapi"]}
))
```

---

## 3. VALIDAÇÃO POR CAMADA

### 3.1 Bronze — Validação de Schema Básico
| Expectation | Tabela | Severidade |
|-------------|--------|-----------|
| Campos obrigatórios não nulos | `raw_odds` | CRITICAL |
| Tipos de dados corretos | `raw_odds` | CRITICAL |
| Odds no intervalo [1.01, 1000] | `raw_odds` | CRITICAL |
| Source em lista válida | `raw_odds` | WARNING |
| Volume diário dentro do esperado | `raw_odds` | WARNING |

### 3.2 Silver — Validação de Qualidade Alta
| Expectation | Tabela | Severidade |
|-------------|--------|-----------|
| `implied_prob` entre 0 e 1 | `odds_cleaned` | CRITICAL |
| Soma das probs do mercado ≈ 1.0 (± 0.001) | `odds_cleaned` | CRITICAL |
| Overround entre 0.02 e 0.15 | `odds_cleaned` | WARNING |
| Cada `market_id` tem exatamente 2 seleções (Moneyline) | `odds_cleaned` | WARNING |
| `is_closing_line` definido para jogos passados | `odds_cleaned` | WARNING |

### 3.3 Gold — Features Consistentes
| Expectation | Tabela | Severidade |
|-------------|--------|-----------|
| Sem NaN em features de treino | `features` | CRITICAL |
| Sem data leakage (futuras features) | `features` | CRITICAL |
| Distribuição de features estável | `features` | WARNING |
| Target variable balance > 30% | `features` | INFO |

---

## 4. VALIDAÇÕES POR DOMÍNIO

### 4.1 Odds de Apostas - Script Robusto
```python
"""
Script robusto de validação de dados de odds
Inclui validações por domínio, logging, error handling e métricas
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Resultado de validação"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]

class OddsValidator:
    """Validador robusto de odds de apostas"""
    
    def __init__(self):
        self.validation_results = []
    
    def validate_market_integrity(self, market_id: str, df: pd.DataFrame) -> ValidationResult:
        """
        Validações específicas para mercados NBA:
        - Moneyline: exatamente 2 seleções
        - Spread: 2 seleções com handicap simétrico
        - Probabilidades somam 1 (com overround)
        """
        errors = []
        warnings = []
        metrics = {}
        
        try:
            market_rows = df[df['market_id'] == market_id]
            
            # Validar número de seleções
            if len(market_rows) != 2:
                errors.append(f"Moneyline {market_id}: {len(market_rows)} seleções (esperado 2)")
            
            # Validar overround
            if 'odd_back' in market_rows.columns:
                total_implied = sum(1 / r['odd_back'] for _, r in market_rows.iterrows())
                metrics['total_implied'] = total_implied
                
                if not (1.02 <= total_implied <= 1.15):
                    errors.append(f"Overround anómalo: {total_implied:.4f}")
                elif not (1.05 <= total_implied <= 1.10):
                    warnings.append(f"Overround fora do ideal: {total_implied:.4f}")
            
            # Validar odds dentro de intervalo
            if 'odd_back' in market_rows.columns:
                for idx, row in market_rows.iterrows():
                    odd = row['odd_back']
                    if odd < 1.01 or odd > 1000:
                        errors.append(f"Odds inválida: {odd}")
            
            is_valid = len(errors) == 0
            
            logger.info(f"Validação mercado {market_id}: {'✅' if is_valid else '❌'}")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Erro ao validar mercado {market_id}: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Erro de validação: {str(e)}"],
                warnings=[],
                metrics={}
            )
    
    def validate_odds_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        """Valida DataFrame completo de odds"""
        errors = []
        warnings = []
        metrics = {}
        
        try:
            # Validar colunas obrigatórias
            required_columns = ['market_id', 'odd_back']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                errors.append(f"Colunas obrigatórias em falta: {missing_columns}")
            
            # Validar sem valores nulos em colunas críticas
            if 'market_id' in df.columns:
                null_count = df['market_id'].isnull().sum()
                if null_count > 0:
                    errors.append(f"{null_count} valores nulos em market_id")
                    metrics['null_market_id'] = null_count
            
            if 'odd_back' in df.columns:
                null_count = df['odd_back'].isnull().sum()
                if null_count > 0:
                    errors.append(f"{null_count} valores nulos em odd_back")
                    metrics['null_odd_back'] = null_count
            
            # Validar range de odds
            if 'odd_back' in df.columns:
                invalid_odds = df[(df['odd_back'] < 1.01) | (df['odd_back'] > 1000)]
                if len(invalid_odds) > 0:
                    errors.append(f"{len(invalid_odds)} odds fora de intervalo [1.01, 1000]")
                    metrics['invalid_odds_count'] = len(invalid_odds)
            
            # Validar duplicados
            if 'market_id' in df.columns:
                duplicates = df.duplicated(subset=['market_id']).sum()
                if duplicates > 0:
                    warnings.append(f"{duplicates} duplicados encontrados")
                    metrics['duplicate_count'] = duplicates
            
            # Métricas gerais
            metrics['total_rows'] = len(df)
            metrics['total_markets'] = df['market_id'].nunique() if 'market_id' in df.columns else 0
            
            is_valid = len(errors) == 0
            
            logger.info(f"Validação DataFrame: {'✅' if is_valid else '❌'} ({len(errors)} erros, {len(warnings)} avisos)")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Erro ao validar DataFrame: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Erro de validação: {str(e)}"],
                warnings=[],
                metrics={}
            )

class PlayerStatsValidator:
    """Validador de estatísticas de jogadores"""
    
    def __init__(self):
        self.validation_rules = {
            'points': (0, 100),
            'minutes_played': (0, 53),
            'field_goal_pct': (0.0, 1.0),
            'plus_minus': (-60, 60)
        }
    
    def validate_player_stats(self, df: pd.DataFrame) -> ValidationResult:
        """Valida DataFrame de estatísticas de jogadores"""
        errors = []
        warnings = []
        metrics = {}
        
        try:
            # Validar cada coluna de stats
            for column, (min_val, max_val) in self.validation_rules.items():
                if column in df.columns:
                    invalid_count = ((df[column] < min_val) | (df[column] > max_val)).sum()
                    
                    if invalid_count > 0:
                        errors.append(f"{invalid_count} valores inválidos em {column} (range: {min_val}-{max_val})")
                        metrics[f'invalid_{column}'] = invalid_count
            
            # Validar sem valores nulos
            null_counts = df.isnull().sum()
            if null_counts.sum() > 0:
                warnings.append(f"Valores nulos encontrados: {null_counts.to_dict()}")
                metrics['null_counts'] = null_counts.to_dict()
            
            is_valid = len(errors) == 0
            
            logger.info(f"Validação Stats Jogadores: {'✅' if is_valid else '❌'}")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Erro ao validar stats jogadores: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Erro de validação: {str(e)}"],
                warnings=[],
                metrics={}
            )

class GamesValidator:
    """Validador de calendário de jogos"""
    
    def __init__(self, valid_teams: List[str]):
        self.valid_teams = valid_teams
    
    def validate_games_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        """Valida DataFrame de jogos"""
        errors = []
        warnings = []
        metrics = {}
        
        try:
            # Validar equipas
            if 'home_team' in df.columns:
                invalid_teams = ~df['home_team'].isin(self.valid_teams)
                if invalid_teams.sum() > 0:
                    errors.append(f"{invalid_teams.sum()} equipas inválidas em home_team")
                    metrics['invalid_home_teams'] = invalid_teams.sum()
            
            if 'away_team' in df.columns:
                invalid_teams = ~df['away_team'].isin(self.valid_teams)
                if invalid_teams.sum() > 0:
                    errors.append(f"{invalid_teams.sum()} equipas inválidas em away_team")
                    metrics['invalid_away_teams'] = invalid_teams.sum()
            
            # Validar datas
            if 'game_date' in df.columns:
                # Verificar se está em formato de data
                try:
                    pd.to_datetime(df['game_date'])
                except Exception as e:
                    errors.append(f"Erro ao converter game_date: {e}")
            
            # Validar scores
            if 'home_score' in df.columns and 'away_score' in df.columns:
                low_scores = (df['home_score'] < 70) | (df['away_score'] < 70)
                if low_scores.sum() > 0:
                    warnings.append(f"{low_scores.sum()} jogos com scores abaixo de 70")
                    metrics['low_score_count'] = low_scores.sum()
            
            is_valid = len(errors) == 0
            
            logger.info(f"Validação Jogos: {'✅' if is_valid else '❌'}")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Erro ao validar jogos: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Erro de validação: {str(e)}"],
                warnings=[],
                metrics={}
            )

class ComprehensiveDataValidator:
    """Validador compreensivo de dados"""
    
    def __init__(self, valid_teams: List[str] = None):
        self.odds_validator = OddsValidator()
        self.player_stats_validator = PlayerStatsValidator()
        self.games_validator = GamesValidator(valid_teams or [])
        
        self.validation_history = []
    
    def validate_all(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, ValidationResult]:
        """Valida todos os DataFrames"""
        results = {}
        
        logger.info("🔍 Iniciando validação compreensiva de dados...")
        
        # Validar odds
        if 'odds' in data_dict:
            results['odds'] = self.odds_validator.validate_odds_dataframe(data_dict['odds'])
        
        # Validar stats jogadores
        if 'player_stats' in data_dict:
            results['player_stats'] = self.player_stats_validator.validate_player_stats(data_dict['player_stats'])
        
        # Validar jogos
        if 'games' in data_dict:
            results['games'] = self.games_validator.validate_games_dataframe(data_dict['games'])
        
        # Guardar histórico
        self.validation_history.append({
            'timestamp': datetime.now().isoformat(),
            'results': results
        })
        
        # Resumo
        total_errors = sum(len(r.errors) for r in results.values())
        total_warnings = sum(len(r.warnings) for r in results.values())
        
        logger.info(f"\n📊 Resumo Validação:")
        logger.info(f"  Erros: {total_errors}")
        logger.info(f"  Avisos: {total_warnings}")
        logger.info(f"  DataFrames validados: {len(results)}")
        
        return results
    
    def generate_validation_report(self, results: Dict[str, ValidationResult]) -> str:
        """Gera relatório de validação"""
        report = "# Relatório de Validação de Dados\n\n"
        report += f"Gerado em: {datetime.now().isoformat()}\n\n"
        
        for name, result in results.items():
            report += f"## {name}\n"
            report += f"Status: {'✅ Válido' if result.is_valid else '❌ Inválido'}\n\n"
            
            if result.errors:
                report += "### Erros\n"
                for error in result.errors:
                    report += f"- {error}\n"
                report += "\n"
            
            if result.warnings:
                report += "### Avisos\n"
                for warning in result.warnings:
                    report += f"- {warning}\n"
                report += "\n"
            
            if result.metrics:
                report += "### Métricas\n"
                for key, value in result.metrics.items():
                    report += f"- {key}: {value}\n"
                report += "\n"
        
        return report
    
    def save_validation_report(self, results: Dict[str, ValidationResult], filepath: str):
        """Guarda relatório de validação"""
        report = self.generate_validation_report(results)
        
        try:
            with open(filepath, 'w') as f:
                f.write(report)
            logger.info(f"💾 Relatório guardado em: {filepath}")
        except Exception as e:
            logger.error(f"Erro ao guardar relatório: {e}")

# Uso
if __name__ == "__main__":
    # Exemplo de uso
    valid_teams = ['LAL', 'BOS', 'GSW', 'MIA', 'NYK']  # Lista completa das 30 equipas
    
    validator = ComprehensiveDataValidator(valid_teams)
    
    # DataFrames de exemplo
    odds_df = pd.DataFrame({
        'market_id': ['m1', 'm2', 'm3'],
        'odd_back': [2.10, 1.95, 2.05],
        'selection_id': ['s1', 's2', 's3']
    })
    
    games_df = pd.DataFrame({
        'home_team': ['LAL', 'GSW'],
        'away_team': ['BOS', 'MIA'],
        'game_date': ['2023-01-01', '2023-01-02'],
        'home_score': [110, 105],
        'away_score': [100, 98]
    })
    
    data_dict = {
        'odds': odds_df,
        'games': games_df
    }
    
    # Validar
    results = validator.validate_all(data_dict)
    
    # Gerar relatório
    report = validator.generate_validation_report(results)
    print(report)
```

### 4.2 Estatísticas de Jogadores
| Campo | Regra |
|-------|-------|
| `points` | 0 ≤ pts ≤ 100 (record NBA: 100) |
| `minutes_played` | 0 ≤ min ≤ 53 (OT máximo) |
| `field_goal_pct` | 0.0 ≤ fg% ≤ 1.0 |
| `plus_minus` | -60 ≤ +/- ≤ 60 |

### 4.3 Calendário de Jogos
| Campo | Regra |
|-------|-------|
| `home_team` | Deve ser uma das 30 equipas NBA ativas |
| `game_date` | Dentro da época NBA (out–jun) |
| `home_score` + `away_score` | Ambos ≥ 70 para jogo completo |

---

## 5. TESTES DE INTEGRIDADE

```python
def test_referential_integrity():
    """Cada aposta deve ter um jogo correspondente na tabela games."""
    query = """
        SELECT COUNT(*) FROM bets b
        LEFT JOIN games g ON b.game_id = g.id
        WHERE g.id IS NULL
    """
    orphan_bets = db.execute(query).scalar()
    assert orphan_bets == 0, f"{orphan_bets} apostas sem jogo correspondente"


def test_temporal_integrity():
    """Apostas não podem ter timestamp posterior ao início do jogo."""
    query = """
        SELECT COUNT(*) FROM bets b
        JOIN games g ON b.game_id = g.id
        WHERE b.bet_timestamp > g.game_start
    """
    future_bets = db.execute(query).scalar()
    assert future_bets == 0, f"{future_bets} apostas com timestamp inválido"


def test_no_data_leakage():
    """Features de treino não devem conter informação do futuro."""
    # Verificar que nenhuma feature usa dados post-game para predição pre-game
    pass
```

---

## 6. FLUXO DE QUALIDADE

```
Ingestão (raw)
    │
    ▼
Validação Bronze (Great Expectations)
    │   Se CRITICAL falhar → alertar + não promover
    │   Se WARNING falhar → registar + promover com flag
    ▼
Transformação + Limpeza
    │
    ▼
Validação Silver (Great Expectations)
    │   Se CRITICAL falhar → alertar + investigar
    ▼
Promoção Gold (para treino/inferência)
    │
    ▼
Validação Gold (anti-leakage + distribuições)
    │   Se falhar → BLOQUEAR treino
    ▼
Consumo pelo Modelo
```

---

## 7. MONITORIZAÇÃO E ALERTAS

```python
# Métricas de qualidade exportadas para Prometheus
data_quality_score = Gauge(
    'data_quality_score',
    'Percentage of passing expectations',
    ['layer', 'suite']
)

validation_failures_total = Counter(
    'data_validation_failures_total',
    'Count of validation failures',
    ['layer', 'rule', 'severity']
)
```

**Alertas:**
- CRITICAL falhou → Telegram imediato + pausar pipeline
- WARNING > 5% dos registos → Telegram + investigar

---

## 8. BACKLOG

- [ ] Instalar Great Expectations e criar expectation suites (Fase 1)
- [ ] Integrar validações no pipeline de ingestão
- [ ] Criar checkpoints automáticos (cron após cada ingestão)
- [ ] Implementar métricas Prometheus de qualidade
- [ ] Criar dashboard de qualidade de dados no Grafana
- [ ] Documentar playbook para cada tipo de falha de validação

---

## 9. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]] ← Secção mãe
- [[04_Data_Engineering/INGESTAO_ODDS]] → Pipeline que é validado
- [[31_Data_Validation/INDEX]] → Validação avançada e schema evolution
- [[10_Monitoring/INDEX]] → Dashboards de qualidade
- [[33_Alerting/INDEX]] → Regras de alerta para falhas de qualidade
