# DEDUPLICACAO_E_LIMPEZA — Regras de Qualidade

**ID:** `DE-003` | **Fase:** #phase/1 | **Owner:** Lead Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Estabelecer regras sistemáticas e determinísticas para deduplicação e limpeza de dados provenientes de múltiplas fontes (NBA API, Basketball-Reference, ESPN, Betfair, etc.). A qualidade dos dados é a fundação de todo o sistema — dados incorretos, duplicados ou inconsistentes levarão inevitavelmente a modelos falhos, sinais errados e perdas financeiras. O objetivo não é apenas "limpar" dados, mas criar um processo robusto e auditável que garanta qualidade consistente em todas as ingestões.

---

## 2. PROBLEMA DE DADOS MULTI-FONTE

### 2.1 Inconsistência de Identificadores

Diferentes fontes usam diferentes identificadores para a mesma entidade. Por exemplo, o jogo entre Lakers e Celtics pode ser:
- NBA API: game_id = "0022300001"
- Basketball-Reference: game_id = "20231024LALBOS"
- ESPN: game_id = "401583455"

Sem deduplicação adequada, o sistema trataria estes como três jogos diferentes, causando duplicação de dados e inconsistências no modelo.

### 2.2 Inconsistência de Nomes

Nomes de equipas podem variar entre fontes:
- "Boston Celtics" vs "BOS" vs "Celtics" vs "Boston"
- "Los Angeles Lakers" vs "LAL" vs "Lakers" vs "LA Lakers"

Sem normalização, features derivadas de nomes de equipas serão inconsistentes e o modelo não conseguirá reconhecer que se referem à mesma entidade.

### 2.3 Inconsistência de Timestamps

Diferentes fontes podem reportar timestamps em diferentes timezones (UTC, EST, PST) ou com diferentes granularidades (segundos, minutos). Sem normalização, dados podem parecer duplicados quando na realidade são o mesmo evento reportado em momentos ligeiramente diferentes.

### 2.4 Missing Values e Outliers

Dados podem estar incompletos (missing values) ou conter erros óbvios (outliers). Por exemplo:
- Estatísticas de jogador faltando para jogos recentes
- Odds negativas ou iguais a zero (erro de feed)
- Scores negativos (impossível)
- Datas futuras no conjunto de dados de treino (look-ahead bias)

Sem tratamento sistemático, estes problemas corromperão o modelo e causarão predições incorretas.

---

## 3. REGRAS DE DEDUPLICAÇÃO

### 3.1 Jogos

**Objetivo:** Garantir que cada jogo físico aparece apenas uma vez no sistema, independentemente de quantas vezes foi reportado por diferentes fontes.

**Estratégia:** Usar o game_id da NBA API como identificador canônico. A NBA API é a fonte oficial mais confiável e seu game_id é único e estável.

**Regra:** Se houver múltiplos registos para o mesmo game_id, manter o registo mais recente (baseado em ingestion_timestamp). Isto permite atualizações — se um jogo é reportado como "em progresso" e depois como "finalizado", a versão finalizada substitui a anterior.

**Implementação:** Ordenar por ingestion_timestamp e usar drop_duplicates com keep='last'.

**Exemplo Prático:**
- 14:00: Jogo reportado como "Scheduled" (game_id: 0022300001)
- 20:30: Jogo reportado como "In Progress" (game_id: 0022300001)
- 23:00: Jogo reportado como "Final" (game_id: 0022300001)

Sistema mantém apenas o registo das 23:00 com status "Final".

---

### 3.2 Equipas

**Objetivo:** Normalizar todos os nomes de equipas para um identificador canônico único (team_id da NBA API).

**Estratégia:** Criar um mapeamento completo de todas as variações de nomes possíveis para o team_id canônico. Este mapeamento deve incluir:
- Nome completo oficial ("Boston Celtics")
- Abreviações padrão ("BOS")
- Nomes comuns ("Celtics")
- Variações históricas ou regionais

**Regra:** Quando ingerir dados, procurar o nome no mapeamento e substituir pelo team_id canônico. Se o nome não for encontrado no mapeamento, registar como erro e adicionar ao mapeamento manualmente após verificação.

**Implementação:** Dicionário Python ou tabela de lookup no PostgreSQL.

**Exemplo Prático:**
```
TEAM_NAME_MAP = {
    'Boston Celtics': 1610612738,
    'BOS': 1610612738,
    'Celtics': 1610612738,
    'Boston': 1610612738,
    'Los Angeles Lakers': 1610612747,
    'LAL': 1610612747,
    'Lakers': 1610612747,
    'LA Lakers': 1610612747,
    # ... todos os 30 times com todas as variações
}
```

---

### 3.3 Odds

**Objetivo:** Para a mesma combinação de jogo + mercado + bookmaker + timestamp, manter a odd mais favorável ao apostador (maior odd).

**Justificativa:** Se múltiplas fontes reportam odds diferentes para o mesmo mercado no mesmo momento, a odd mais alta representa a melhor oportunidade para o apostador. Manter a mais alta garante que não perdemos oportunidades de edge.

**Regra:** Agrupar por game_id, market, bookmaker, timestamp e manter o registo com a odd máxima.

**Implementação:** GroupBy com idxmax na coluna odd.

**Exemplo Prático:**
- Fonte A: Lakers vs Celtics, Moneyline Lakers, Betfair, 14:00, odd = 1.85
- Fonte B: Lakers vs Celtics, Moneyline Lakers, Betfair, 14:00, odd = 1.87

Sistema mantém odd = 1.87 (mais favorável).

---

## 4. REGRAS DE LIMPEZA

### 4.1 Tratamento de Missing Values em Estatísticas

**Problema:** Estatísticas de equipa ou jogador podem estar faltando (missing) devido a:
- Fonte não reportou a estatística
- Erro de ingestão
- Jogador não jogou (lesão, DNP)

**Regra:** Usar média da época para essa equipa específica como valor de imputação. Isto é preferível a média da liga porque cada equipa tem perfis diferentes — equipas ofensivas têm médias mais altas de pontos, equipas defensivas têm médias mais baixas.

**Justificativa:** Imputar com média da equipa preserva as características únicas de cada equipa enquanto fornece um valor razoável quando o valor real não está disponível.

**Exemplo Prático:** ORB% (Offensive Rebound Percentage) está missing para um jogo. A média de ORB% da equipa na época é 28.5%. Substituir missing por 28.5%.

---

### 4.2 Validação de Odds

**Problema:** Odds podem ser inválidas devido a erros de feed, parsing incorreto, ou problemas com a fonte.

**Regra:** Descartar qualquer odd ≤ 1.0. Odds de 1.0 ou abaixo são matematicamente impossíveis em apostas desportivas (representariam edge zero ou negativo garantido).

**Justificativa:** Odds inválidas corromperiam cálculos de edge e CLV. Descartar é a única opção segura.

**Exemplo Prático:** Odd reportada como 0.95 (erro evidente). Sistema descarta registo e regista erro em audit log.

---

### 4.3 Validação de Status de Jogo

**Problema:** Jogos podem ser reportados antes de estarem completados (Scheduled, In Progress, Halftime). Usar dados de jogos incompletos para treino causaria look-ahead bias.

**Regra:** Ignorar jogos cujo status não é "Final" ou "Final/OT" (após prorrogação). Apenas jogos completados devem ser usados para treino.

**Justificativa:** Features derivadas de jogos incompletos (ex: pontos marcados) são incompletas e não representam o resultado final. Usá-las contaminaria o modelo.

**Exemplo Prático:** Jogo está em "In Progress" no momento da ingestão. Sistema ignora este registo para camadas de treino, mas pode mantê-lo em camada raw para atualização posterior quando o jogo completar.

---

### 4.4 Normalização de Status de Lesão

**Problema:** Diferentes fontes usam terminologias diferentes para status de lesão (ex: "day-to-day", "questionable", "out", "doubtful").

**Regra:** Mapear todas as variações para um conjunto canônico de valores:
- "OUT": Jogador não vai jogar
- "QUESTIONABLE": 50% de chance de jogar
- "PROBABLE": 75% de chance de jogar
- "UNKNOWN": Status desconhecido

**Justificativa:** Normalização permite que o modelo use status de lesão como feature consistente, independentemente da fonte.

**Exemplo Prático:** "day-to-day" → QUESTIONABLE, "doubtful" → QUESTIONABLE, "out indefinitely" → OUT.

---

### 4.5 Prevenção de Look-Ahead Bias

**Problema:** Dados com timestamps futuros podem ser acidentalmente ingeridos no conjunto de treino, causando look-ahead bias (o modelo "vê" o futuro).

**Regra:** Rejeitar qualquer registo onde ingestion_date > today (data atual). Isto garante que só dados históricos são usados para treino.

**Justificativa:** Look-ahead bias é uma das causas mais comuns de backtests enganosos. Prevenção é crítica.

**Exemplo Prático:** Ingestão acidentalmente inclui dados de amanhã (erro de timezone). Sistema rejeita registo e regera alerta.

---

### 4.6 Validação de Scores

**Problema:** Scores podem ser negativos ou irrealisticamente altos devido a erros de parsing ou corrupção de dados.

**Regra:** Rejeitar qualquer score negativo. Validar que scores estão dentro de intervalos razoáveis (ex: 0-200 pontos para NBA).

**Justificativa:** Scores impossíveis corromperiam features derivadas e causariam erros no modelo.

**Exemplo Prático:** Score reportado como -15 (erro evidente). Sistema rejeita registo e regista erro.

---

## 5. TRATAMENTO DE MISSING VALUES

### 5.1 Estratégia Hierárquica

O sistema usa uma estratégia hierárquica de três níveis para imputação de missing values:

**Nível 1: Forward Fill por Equipa**
- Para estatísticas de equipa, usar o valor do jogo anterior da mesma equipa
- Isto preserva a tendência recente de performance da equipa
- Exemplo: eFG% do jogo anterior → imputar para missing atual

**Nível 2: Média da Época por Equipa**
- Se forward fill não é possível (primeiro jogo da época), usar média da equipa na época
- Isto preserva as características únicas da equipa
- Exemplo: Média de eFG% dos últimos 10 jogos da equipa

**Nível 3: Média da Liga**
- Se a equipa não tem dados suficientes (ex: nova equipa ou início de época), usar média da liga
- Isto fornece um fallback razoável quando dados específicos da equipa não estão disponíveis
- Exemplo: Média de eFG% de todas as equipas da NBA

### 5.2 Implementação

O processo de imputação é aplicado sequencialmente em ordem hierárquica. Se o nível 1 falha, tenta nível 2. Se nível 2 falha, usa nível 3. Se todos falharem, o registo pode ser descartado dependendo da criticalidade da feature.

**Exemplo Prático:**
1. Tentar forward fill: eFG% do jogo anterior = 52.3% → usar 52.3%
2. Se não houver jogo anterior: média da equipa = 51.8% → usar 51.8%
3. Se não houver dados da equipa: média da liga = 50.5% → usar 50.5%

---

## 6. AUDIT TRAIL

### 6.1 Propósito

Toda correção, imputação ou descarte de dados deve ser registada em audit trail. Isto é essencial para:
- Debugging de problemas de dados
- Análise post-mortem de erros de modelo
- Compliance e accountability
- Melhoria contínua do pipeline de dados

### 6.2 Estrutura do Audit Log

Cada evento de correção é registado com os seguintes campos:

- **correction_id:** UUID único do evento
- **table_name:** Tabela ou coleção afetada
- **record_id:** ID do registo corrigido
- **field_name:** Campo específico alterado
- **old_value:** Valor antes da correção
- **new_value:** Valor após a correção
- **reason:** Razão da correção (ex: "missing value imputed with team average")
- **timestamp:** Quando a correção foi aplicada
- **corrected_by:** "system" (automático) ou ID do utilizador (manual)

### 6.3 Consulta e Análise

O audit log deve ser queryable para permitir:
- Identificar padrões de erros (ex: mesma fonte sempre tem problema X)
- Estatísticas de qualidade de dados (taxa de correções por fonte)
- Investigação de problemas específicos (quando e como um registo foi alterado)

---

## 7. VALIDAÇÃO E MONITORIZAÇÃO

### 7.1 Métricas de Qualidade de Dados

O sistema deve monitorizar continuamente métricas de qualidade de dados:

- **Taxa de Duplicação:** Percentagem de registos duplicados antes de deduplicação
- **Taxa de Missing Values:** Percentagem de campos missing por fonte
- **Taxa de Correções:** Percentagem de registos que requereram correção
- **Taxa de Rejeição:** Percentagem de registos descartados por invalidação

**Targets:**
- Taxa de duplicação < 5%
- Taxa de missing values < 10%
- Taxa de rejeição < 2%

### 7.2 Alertas

Alertas devem ser gerados quando:
- Taxa de missing values excede 15% em qualquer fonte
- Taxa de rejeição excede 5%
- Nova fonte de dados introduzida sem validação prévia
- Padrão anormal de erros detetado

---

## 8. BACKLOG TÉCNICO

- [ ] Implementar mapeamento completo de nomes de equipas (todas as 30 equipas com variações)
- [ ] Criar suite de testes unitários para todas as regras de limpeza
- [ ] Implementar sistema de audit trail completo com query interface
- [ ] Documentar decision log de todas as regras de imputação
- [ ] Criar dashboard de qualidade de dados em tempo real
- [ ] Implementar alertas automáticos para anomalias de qualidade
- [ ] Adicionar validações adicionais para outliers estatísticos
- [ ] Criar processo manual de revisão para registros flagged como problemáticos

---

## 9. IMPLEMENTAÇÃO COMPLETA

### 9.1 Script Robusto de Deduplicação e Limpeza
```python
"""
Script robusto de deduplicação e limpeza de dados
Inclui deduplicação, normalização, tratamento de missing values e audit trail
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import uuid

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AuditRecord:
    """Registo de auditoria para correções"""
    correction_id: str
    table_name: str
    record_id: str
    field_name: str
    old_value: Any
    new_value: Any
    reason: str
    timestamp: datetime
    corrected_by: str

class DataCleaner:
    """Classe principal para limpeza e deduplicação de dados"""
    
    def __init__(self):
        self.audit_log = []
        self.team_name_map = self._initialize_team_map()
    
    def _initialize_team_map(self) -> Dict[str, int]:
        """Inicializa mapeamento de nomes de equipas para team_id"""
        return {
            # Boston Celtics
            'Boston Celtics': 1610612738,
            'BOS': 1610612738,
            'Celtics': 1610612738,
            'Boston': 1610612738,
            
            # Los Angeles Lakers
            'Los Angeles Lakers': 1610612747,
            'LAL': 1610612747,
            'Lakers': 1610612747,
            'LA Lakers': 1610612747,
            
            # Golden State Warriors
            'Golden State Warriors': 1610612744,
            'GSW': 1610612744,
            'Warriors': 1610612744,
            
            # Miami Heat
            'Miami Heat': 1610612748,
            'MIA': 1610612748,
            'Heat': 1610612748,
            
            # New York Knicks
            'New York Knicks': 1610612752,
            'NYK': 1610612752,
            'Knicks': 1610612752,
            'New York': 1610612752,
            
            # Adicionar todas as 30 equipas...
        }
    
    def _add_audit_record(self, table_name: str, record_id: str, field_name: str,
                         old_value: Any, new_value: Any, reason: str, corrected_by: str = "system"):
        """Adiciona registo de auditoria"""
        record = AuditRecord(
            correction_id=str(uuid.uuid4()),
            table_name=table_name,
            record_id=record_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            timestamp=datetime.now(),
            corrected_by=corrected_by
        )
        self.audit_log.append(record)
        logger.debug(f"Audit: {field_name} de {record_id} alterado de {old_value} para {new_value}")
    
    def deduplicate_games(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Deduplica jogos mantendo o registo mais recente
        Usa game_id como identificador canônico
        """
        logger.info("🔍 Deduplicando jogos...")
        
        if 'game_id' not in df.columns:
            logger.error("Coluna game_id não encontrada")
            return df
        
        original_count = len(df)
        
        # Ordenar por ingestion_timestamp e manter o mais recente
        if 'ingestion_timestamp' in df.columns:
            df = df.sort_values('ingestion_timestamp')
        
        # Remover duplicados mantendo o último
        df = df.drop_duplicates(subset=['game_id'], keep='last')
        
        removed_count = original_count - len(df)
        
        if removed_count > 0:
            logger.info(f"✅ {removed_count} duplicados removidos ({original_count} → {len(df)})")
        else:
            logger.info(f"✅ Sem duplicados encontrados ({len(df)} jogos)")
        
        return df
    
    def normalize_team_names(self, df: pd.DataFrame, team_column: str = 'team_name') -> pd.DataFrame:
        """
        Normaliza nomes de equipas para team_id canônico
        """
        logger.info(f"🔍 Normalizando nomes de equipas na coluna {team_column}...")
        
        if team_column not in df.columns:
            logger.warning(f"Coluna {team_column} não encontrada")
            return df
        
        normalized_count = 0
        not_found_count = 0
        
        for idx, row in df.iterrows():
            team_name = row[team_column]
            
            if pd.isna(team_name):
                continue
            
            if team_name in self.team_name_map:
                team_id = self.team_name_map[team_name]
                old_value = row[team_column]
                df.at[idx, 'team_id'] = team_id
                self._add_audit_record(
                    table_name='games',
                    record_id=str(idx),
                    field_name=team_column,
                    old_value=old_value,
                    new_value=team_id,
                    reason='team_name normalized to team_id'
                )
                normalized_count += 1
            else:
                not_found_count += 1
                logger.warning(f"Nome de equipa não encontrado no mapeamento: {team_name}")
        
        logger.info(f"✅ {normalized_count} nomes normalizados, {not_found_count} não encontrados")
        
        return df
    
    def deduplicate_odds(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Deduplica odds mantendo a odd mais favorável (maior)
        Agrupa por game_id, market, bookmaker, timestamp
        """
        logger.info("🔍 Deduplicando odds...")
        
        required_columns = ['game_id', 'market', 'bookmaker', 'timestamp', 'odd']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Colunas obrigatórias em falta: {missing_columns}")
            return df
        
        original_count = len(df)
        
        # Agrupar e manter odd máxima
        idx = df.groupby(['game_id', 'market', 'bookmaker', 'timestamp'])['odd'].idxmax()
        df = df.loc[idx]
        
        removed_count = original_count - len(df)
        
        if removed_count > 0:
            logger.info(f"✅ {removed_count} duplicados removidos ({original_count} → {len(df)})")
        else:
            logger.info(f"✅ Sem duplicados encontrados ({len(df)} odds)")
        
        return df
    
    def validate_odds(self, df: pd.DataFrame, odd_column: str = 'odd') -> pd.DataFrame:
        """
        Valida odds e remove valores inválidos (≤ 1.0)
        """
        logger.info(f"🔍 Validando odds na coluna {odd_column}...")
        
        if odd_column not in df.columns:
            logger.warning(f"Coluna {odd_column} não encontrada")
            return df
        
        original_count = len(df)
        
        # Identificar odds inválidas
        invalid_mask = df[odd_column] <= 1.0
        invalid_count = invalid_mask.sum()
        
        if invalid_count > 0:
            logger.warning(f"⚠️  {invalid_count} odds inválidas encontradas (≤ 1.0)")
            
            # Guardar em audit log
            for idx in df[invalid_mask].index:
                self._add_audit_record(
                    table_name='odds',
                    record_id=str(idx),
                    field_name=odd_column,
                    old_value=df.at[idx, odd_column],
                    new_value=None,
                    reason='invalid odds (≤ 1.0) removed'
                )
            
            # Remover inválidas
            df = df[~invalid_mask]
        
        logger.info(f"✅ Validação completa ({original_count} → {len(df)} odds)")
        
        return df
    
    def validate_game_status(self, df: pd.DataFrame, status_column: str = 'status') -> pd.DataFrame:
        """
        Valida status de jogos e mantém apenas "Final" ou "Final/OT"
        """
        logger.info(f"🔍 Validando status de jogos na coluna {status_column}...")
        
        if status_column not in df.columns:
            logger.warning(f"Coluna {status_column} não encontrada")
            return df
        
        original_count = len(df)
        
        # Status válidos
        valid_statuses = ['Final', 'Final/OT']
        
        # Filtrar apenas status válidos
        valid_mask = df[status_column].isin(valid_statuses)
        invalid_count = (~valid_mask).sum()
        
        if invalid_count > 0:
            logger.info(f"ℹ️  {invalid_count} jogos com status incompleto ignorados")
            df = df[valid_mask]
        
        logger.info(f"✅ Validação completa ({original_count} → {len(df)} jogos)")
        
        return df
    
    def impute_missing_values(self, df: pd.DataFrame, column: str, 
                            team_season_avg: Dict[str, float] = None,
                            league_avg: float = None) -> pd.DataFrame:
        """
        Imputa missing values usando estratégia hierárquica:
        1. Forward fill por equipa
        2. Média da época por equipa
        3. Média da liga
        """
        logger.info(f"🔍 Imputando missing values na coluna {column}...")
        
        if column not in df.columns:
            logger.warning(f"Coluna {column} não encontrada")
            return df
        
        original_missing = df[column].isnull().sum()
        
        if original_missing == 0:
            logger.info(f"✅ Sem missing values em {column}")
            return df
        
        imputed_count = 0
        
        # Nível 1: Forward fill por equipa (se houver team_id)
        if 'team_id' in df.columns and df['team_id'].notnull().any():
            df[column] = df.groupby('team_id')[column].fillna(method='ffill')
            remaining_missing = df[column].isnull().sum()
            imputed_count = original_missing - remaining_missing
            logger.info(f"  Nível 1 (forward fill): {imputed_count} valores imputados")
        
        # Nível 2: Média da época por equipa
        if team_season_avg and df[column].isnull().sum() > 0:
            for idx, row in df[df[column].isnull()].iterrows():
                team_id = row.get('team_id')
                if team_id and team_id in team_season_avg:
                    old_value = df.at[idx, column]
                    df.at[idx, column] = team_season_avg[team_id]
                    self._add_audit_record(
                        table_name='stats',
                        record_id=str(idx),
                        field_name=column,
                        old_value=old_value,
                        new_value=team_season_avg[team_id],
                        reason='imputed with team season average'
                    )
                    imputed_count += 1
            
            remaining_missing = df[column].isnull().sum()
            logger.info(f"  Nível 2 (team avg): {imputed_count} valores imputados")
        
        # Nível 3: Média da liga
        if league_avg and df[column].isnull().sum() > 0:
            missing_indices = df[df[column].isnull()].index
            for idx in missing_indices:
                old_value = df.at[idx, column]
                df.at[idx, column] = league_avg
                self._add_audit_record(
                    table_name='stats',
                    record_id=str(idx),
                    field_name=column,
                    old_value=old_value,
                    new_value=league_avg,
                    reason='imputed with league average'
                )
                imputed_count += 1
            
            logger.info(f"  Nível 3 (league avg): {imputed_count} valores imputados")
        
        logger.info(f"✅ Imputação completa ({original_missing} → {df[column].isnull().sum()} missing)")
        
        return df
    
    def validate_scores(self, df: pd.DataFrame, score_columns: List[str] = None) -> pd.DataFrame:
        """
        Valida scores e remove valores inválidos (negativos ou fora de intervalo)
        """
        logger.info("🔍 Validando scores...")
        
        if score_columns is None:
            score_columns = ['home_score', 'away_score']
        
        original_count = len(df)
        
        for column in score_columns:
            if column not in df.columns:
                continue
            
            # Validar scores não negativos
            invalid_mask = df[column] < 0
            invalid_count = invalid_mask.sum()
            
            if invalid_count > 0:
                logger.warning(f"⚠️  {invalid_count} scores negativos encontrados em {column}")
                
                # Guardar em audit log
                for idx in df[invalid_mask].index:
                    self._add_audit_record(
                        table_name='games',
                        record_id=str(idx),
                        field_name=column,
                        old_value=df.at[idx, column],
                        new_value=None,
                        reason='invalid score (negative) removed'
                    )
                
                # Remover inválidos
                df = df[~invalid_mask]
            
            # Validar scores dentro de intervalo razoável (0-200)
            invalid_mask = df[column] > 200
            invalid_count = invalid_mask.sum()
            
            if invalid_count > 0:
                logger.warning(f"⚠️  {invalid_count} scores > 200 encontrados em {column}")
                df = df[~invalid_mask]
        
        logger.info(f"✅ Validação completa ({original_count} → {len(df)} jogos)")
        
        return df
    
    def prevent_lookahead_bias(self, df: pd.DataFrame, date_column: str = 'game_date') -> pd.DataFrame:
        """
        Remove dados com datas futuras para prevenir look-ahead bias
        """
        logger.info(f"🔍 Prevenindo look-ahead bias na coluna {date_column}...")
        
        if date_column not in df.columns:
            logger.warning(f"Coluna {date_column} não encontrada")
            return df
        
        original_count = len(df)
        
        # Converter para datetime se necessário
        df[date_column] = pd.to_datetime(df[date_column])
        
        # Identificar datas futuras
        today = pd.Timestamp.now().normalize()
        future_mask = df[date_column] > today
        future_count = future_mask.sum()
        
        if future_count > 0:
            logger.warning(f"⚠️  {future_count} registos com datas futuras encontrados")
            
            # Guardar em audit log
            for idx in df[future_mask].index:
                self._add_audit_record(
                    table_name='games',
                    record_id=str(idx),
                    field_name=date_column,
                    old_value=df.at[idx, date_column],
                    new_value=None,
                    reason='lookahead bias prevention (future date removed)'
                )
            
            # Remover datas futuras
            df = df[~future_mask]
        
        logger.info(f"✅ Prevenção completa ({original_count} → {len(df)} jogos)")
        
        return df
    
    def generate_audit_report(self) -> str:
        """Gera relatório de auditoria"""
        report = "# Relatório de Auditoria de Limpeza\n\n"
        report += f"Gerado em: {datetime.now().isoformat()}\n"
        report += f"Total de correções: {len(self.audit_log)}\n\n"
        
        # Agrupar por tipo de correção
        corrections_by_reason = {}
        for record in self.audit_log:
            reason = record.reason
            if reason not in corrections_by_reason:
                corrections_by_reason[reason] = []
            corrections_by_reason[reason].append(record)
        
        report += "## Correções por Razão\n\n"
        for reason, records in corrections_by_reason.items():
            report += f"### {reason}\n"
            report += f"Total: {len(records)}\n\n"
        
        return report
    
    def save_audit_log(self, filepath: str):
        """Guarda audit log em arquivo"""
        try:
            with open(filepath, 'w') as f:
                for record in self.audit_log:
                    f.write(f"{record.correction_id},{record.table_name},{record.record_id},"
                           f"{record.field_name},{record.old_value},{record.new_value},"
                           f"{record.reason},{record.timestamp},{record.corrected_by}\n")
            logger.info(f"💾 Audit log guardado em: {filepath}")
        except Exception as e:
            logger.error(f"Erro ao guardar audit log: {e}")

class DataQualityMetrics:
    """Calcula métricas de qualidade de dados"""
    
    @staticmethod
    def calculate_duplication_rate(df: pd.DataFrame, key_columns: List[str]) -> float:
        """Calcula taxa de duplicação"""
        if not key_columns:
            return 0.0
        
        duplicates = df.duplicated(subset=key_columns).sum()
        return (duplicates / len(df)) * 100 if len(df) > 0 else 0.0
    
    @staticmethod
    def calculate_missing_rate(df: pd.DataFrame) -> float:
        """Calcula taxa de missing values"""
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        return (missing_cells / total_cells) * 100 if total_cells > 0 else 0.0
    
    @staticmethod
    def calculate_correction_rate(audit_log: List[AuditRecord]) -> float:
        """Calcula taxa de correções"""
        if not audit_log:
            return 0.0
        return len(audit_log)

# Uso
if __name__ == "__main__":
    cleaner = DataCleaner()
    
    # Exemplo de uso com dados de jogos
    games_df = pd.DataFrame({
        'game_id': ['0022300001', '0022300001', '0022300002'],
        'team_name': ['Boston Celtics', 'BOS', 'LAL'],
        'status': ['Final', 'Final', 'In Progress'],
        'game_date': ['2023-01-01', '2023-01-01', '2023-01-02'],
        'home_score': [110, 110, 105],
        'away_score': [100, 100, 98],
        'ingestion_timestamp': pd.to_datetime(['2023-01-01 14:00', '2023-01-01 20:30', '2023-01-02 14:00'])
    })
    
    # Aplicar limpeza
    games_df = cleaner.deduplicate_games(games_df)
    games_df = cleaner.normalize_team_names(games_df, team_column='team_name')
    games_df = cleaner.validate_game_status(games_df)
    games_df = cleaner.validate_scores(games_df)
    games_df = cleaner.prevent_lookahead_bias(games_df)
    
    # Exemplo de uso com dados de odds
    odds_df = pd.DataFrame({
        'game_id': ['0022300001', '0022300001', '0022300002'],
        'market': ['moneyline', 'moneyline', 'spread'],
        'bookmaker': ['Betfair', 'Betfair', 'Betfair'],
        'timestamp': ['2023-01-01 14:00', '2023-01-01 14:00', '2023-01-01 14:00'],
        'odd': [1.85, 1.87, 0.95]
    })
    
    odds_df = cleaner.deduplicate_odds(odds_df)
    odds_df = cleaner.validate_odds(odds_df)
    
    # Métricas de qualidade
    metrics = DataQualityMetrics()
    dup_rate = metrics.calculate_duplication_rate(games_df, ['game_id'])
    missing_rate = metrics.calculate_missing_rate(games_df)
    
    print(f"\n📊 Métricas de Qualidade:")
    print(f"  Taxa de duplicação: {dup_rate:.2f}%")
    print(f"  Taxa de missing values: {missing_rate:.2f}%")
    print(f"  Total de correções: {len(cleaner.audit_log)}")
    
    # Relatório de auditoria
    report = cleaner.generate_audit_report()
    print(report)
```

---

## 10. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]] ← Secção mãe
- [[04_Data_Engineering/PIPELINE_ETL_NBA]] → Pipeline que aplica estas regras
- [[04_Data_Engineering/ESQUEMA_BASE_DADOS]] → Schema de base de dados
- [[15_Database/SCHEMA_POSTGRESQL]] → Schema SQL completo
