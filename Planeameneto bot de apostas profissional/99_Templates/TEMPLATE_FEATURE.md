# TPL-008 — Documentação de Feature (Feature Specification)

**ID:** `FEAT-XXX`  
**Nome:** *Nome técnico da feature*  
**Nome Amigável:** *Nome descritivo para não-técnicos*  
**Status:** *[Research/Pending/In Development/Testing/Production/Deprecated]*  
**Owner:** *Nome do responsável*  
**Data de Criação:** *YYYY-MM-DD*  
**Última Atualização:** *YYYY-MM-DD*  
**Versão:** *v1.0*

---

## 1. RESUMO EXECUTIVO

| Campo | Descrição |
|-------|-----------|
| **O que é?** | *Descrição em 1-2 frases* |
| **Tipo** | *[Feature bruta / Transformada / Interação / Agregada]* |
| **Granularidade** | *[Jogo / Equipa / Jogador / Temporada]* |
| **Latência** | *[Real-time / Batch - especificar frequência]* |
| **Uso Principal** | *Para que modelo/análise é usada* |

---

## 2. DESCRIÇÃO DETALHADA

### 2.1 Definição Conceitual
*[Explicação detalhada do que a feature representa do ponto de vista de negócio]*

**Exemplo:**
- *Esta feature mede a forma recente da equipa casa, calculada como...*
- *Representa a vantagem de descanso entre jogos...*

### 2.2 Intuição de Negócio
*[Por que acreditamos que esta feature é preditiva? Que hipótese de negócio está por trás?]*

---

## 3. Especificação Técnica

### 3.1 Fórmula / Algoritmo
*[Como a feature é calculada. Incluir fórmulas matemáticas ou pseudo-código]*

```python
# Pseudo-código ou fórmula
def calculate_feature(game_id, team_id, window=5):
    """
    Calcula feature para um dado jogo e equipa.
    
    Args:
        game_id: ID do jogo
        team_id: ID da equipa
        window: Janela temporal (default: 5 jogos)
    
    Returns:
        Valor da feature (float)
    """
    # Lógica de cálculo
    games = get_last_n_games(team_id, before=game_id, n=window)
    feature_value = games['points'].mean()
    return feature_value
```

### 3.2 Input
| Campo | Tipo | Descrição | Fonte |
|-------|------|-----------|-------|
| *input_1* | *tipo* | *descrição* | *tabela/campo* |
| *input_2* | *tipo* | *descrição* | *tabela/campo* |

### 3.3 Output
| Campo | Tipo | Descrição |
|-------|------|-----------|
| *output* | *float/int/bool* | *descrição do valor retornado* |

### 3.4 Dependências
- [[FEAT-YYY]] — *Feature dependência 1 (pré-requisito)*
- [[FEAT-ZZZ]] — *Feature dependência 2*
- *Tabela raw: bronze.raw_games*

---

## 4. REQUISITOS E RESTRIÇÕES

### 4.1 Requisitos Funcionais
- [ ] *RF1: Deve calcular em menos de X ms*
- [ ] *RF2: Deve ser determinística (mesmo input → mesmo output)*
- [ ] *RF3: Deve lidar com missing values de forma Y*

### 4.2 Requisitos Não-Funcionais
- [ ] *RNF1: Latência máxima: X ms*
- [ ] *RNF2: Disponibilidade: 99.9%*

### 4.3 Restrições
- *[Ex: "Apenas calculada para jogos regulares, não playoffs"]*
- *[Ex: "Não usar dados de jogos adiados"]*

---

## 5. IMPLEMENTAÇÃO

### 5.1 Localização do Código
```
src/features/
├── __init__.py
├── feat_xxx.py          # Implementação principal
└── tests/
    └── test_feat_xxx.py # Testes unitários
```

### 5.2 Interface
```python
class FeatureXXX(BaseFeature):
    """Docstring da feature."""
    
    name = "feat_xxx"
    version = "1.0"
    
    def compute(self, game_id: str, team_id: int) -> float:
        """Método principal de cálculo."""
        pass
    
    @property
    def dependencies(self) -> List[str]:
        """Lista de features/tabelas necessárias."""
        return ["bronze.raw_games"]
```

### 5.3 Data de Implementação
- **Planeada:** *YYYY-MM-DD*
- **Real:** *YYYY-MM-DD*
- **Deploy:** *YYYY-MM-DD*

---

## 6. QUALIDADE E VALIDAÇÃO

### 6.1 Testes Unitários
- [ ] *Teste: Cálculo correto com dados conhecidos*
- [ ] *Teste: Lida com missing values*
- [ ] *Teste: Lida com edge cases (primeiro jogo da época)*
- [ ] *Teste: Performance dentro do esperado*

### 6.2 Testes de Integração
- [ ] *Teste: Integração com pipeline de features*
- [ ] *Teste: Integração com modelos*

### 6.3 Validação Estatística
| Métrica | Valor | Threshold | Status |
|---------|-------|-----------|--------|
| *Missing rate* | *X%* | *< 5%* | *[Pass/Fail]* |
| *Variance* | *Y* | *> 0.01* | *[Pass/Fail]* |
| *Correlation with target* | *Z* | *> 0.05* | *[Pass/Fail]* |
| *Stability (PSI)* | *W* | *< 0.25* | *[Pass/Fail]* |

### 6.4 Análise de Data Quality
- **Completude:** *X% dos jogos têm esta feature*
- **Precisão:** *Validado contra fonte externa?*
- **Consistência:** *Mesmo valor para mesmas condições?*
- **Timeliness:** *Feature disponível antes do jogo?*

---

## 7. MONITORIZAÇÃO

### 7.1 Métricas de Operação
| Métrica | Query | Alert Threshold |
|---------|-------|-----------------|
| *Latência média* | `avg(feature_compute_time)` | *> 100ms* |
| *Taxa de erro* | `count(errors) / count(total)` | *> 0.1%* |
| *Missing rate* | `count(null) / count(total)` | *> 5%* |

### 7.2 Alertas
- **Alerta A:** *[Condição e ação]*
- **Alerta B:** *[Condição e ação]*

### 7.3 Dashboard
- Link: `http://grafana/d/feature-xxx`
- Panels: *Distribuição, tendência, drift*

---

## 8. ANÁLISE DE IMPACTO

### 8.1 Importância do Modelo
| Modelo | Feature Importance | Rank |
|--------|-------------------|------|
| *XGBoost v1.2* | *0.045* | *12/80* |
| *LightGBM v1.2* | *0.038* | *15/80* |

### 8.2 Análise de Drift
*[Monitorização de como a feature muda ao longo do tempo]*
- **PSI (Population Stability Index):** *X (threshold: 0.25)*
- **Mean drift:** *Y% desde baseline*
- **Variance drift:** *Z% desde baseline*

---

## 9. DOCUMENTAÇÃO DE NEGÓCIO

### 9.1 Interpretação
*[Como explicar esta feature a stakeholders não-técnicos]*
- *"Esta feature mede..."*
- *"Valores altos significam..."*

### 9.2 Exemplos
| Jogo | Equipa | Valor | Interpretação |
|------|--------|-------|---------------|
| *LAL vs BOS 2024-01-15* | *LAL* | *0.85* | *Muito forte recentemente* |

---

## 10. GOVERNANÇA

### 10.1 Responsabilidades
| Atividade | Responsável | Frequência |
|-----------|-------------|------------|
| *Monitorização* | *MLOps* | *Diária* |
| *Revisão de qualidade* | *Data Engineer* | *Semanal* |
| *Atualização de lógica* | *Owner* | *Quando necessário* |

### 10.2 Data de Revisão
**Próxima revisão:** *YYYY-MM-DD*

---

## 11. HISTÓRICO

| Data | Versão | Alteração | Autor |
|------|--------|-----------|-------|
| *YYYY-MM-DD* | *v1.0* | *Criação inicial* | *Nome* |
| *YYYY-MM-DD* | *v1.1* | *Ajuste na fórmula* | *Nome* |

---

## 12. LINKS CRUZADOS

- [[32_Feature_Store/INDEX]] ← Feature Store geral
- [[32_Feature_Store/CATALOG]] → Catálogo de todas as features
- [[FEAT-YYY]] → Features relacionadas
- [[30_Model_Registry/INDEX]] → Modelos que usam esta feature
- [[31_Data_Validation/INDEX]] → Validação de dados
