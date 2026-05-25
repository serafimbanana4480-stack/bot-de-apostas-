# MITIGACAO_DRIFT — Estratégias de Resposta e Correção

**ID:** `DRIFT-007` | **Fase:** #phase/6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir estratégias e procedimentos para mitigar drift quando detetado, minimizando o impacto no sistema de value betting e garantindo recuperação rápida.

---

## 2. CONTEXTO

Quando drift é detetado, ação rápida é crítica para:
- Minimizar perdas financeiras
- Manter a confiança no sistema
- Evitar degradação contínua
- Restaurar performance do modelo

**Princípios:**
- Resposta proporcional à severidade
- Ação baseada em causa raiz
- Monitorização contínua após correção
- Documentação de lições aprendidas

---

## 3. ESTRATÉGIAS DE MITIGAÇÃO

### 3.1 Estratégia 1: Nenhuma Ação (Monitorização)

**Quando usar:**
- PSI < 0.10 (drift insignificante)
- Mudança esperada (sazonalidade)
- Sem impacto na performance

**Ação:**
- Continuar monitorização
- Logging de métricas
- Reavaliar na próxima verificação

**Risco:** Drift pode piorar sem intervenção.

### 3.2 Estratégia 2: Ajuste de Thresholds

**Quando usar:**
- Drift causado por mudança natural/esperada
- Thresholds demasiado conservadores
- Sem degradação de performance real

**Ação:**
- Ajustar thresholds baseados em nova baseline
- Documentar justificação
- Revalidar periodicamente

**Exemplo:**
- PSI threshold de 0.20 → 0.25 para feature volátil
- Ajuste baseado em análise histórica de 6 meses

**Risco:** Pode mascarar drift real se mal aplicado.

### 3.3 Estratégia 3: Retraining do Modelo

**Quando usar:**
- Feature drift significativo (PSI > 0.25)
- Prediction drift com degradação de performance
- Concept drift confirmado

**Ação:**
- Coletar dados recentes para treino
- Retreinar modelo com novos dados
- Validar em holdout set
- Deploy em produção (canary ou shadow)

**Tipos de Retraining:**

**Retraining Completo:**
- Treinar do zero com todos os dados
- Mais robusto, mas mais demorado
- Recomendado para concept drift severo

**Retraining Incremental:**
- Continuar treino do modelo existente
- Mais rápido, mas pode não capturar mudanças grandes
- Recomendado para drift moderado

**Retraining com Janela Deslizante:**
- Usar apenas dados recentes (ex: últimos 3 meses)
- Adapta-se rapidamente a mudanças
- Risco de overfit a ruído recente

### 3.4 Estratégia 4: Feature Engineering

**Quando usar:**
- Features tornaram-se irrelevantes
- Novas features disponíveis
- Relações entre features mudaram

**Ação:**
- Remover features irrelevantes
- Adicionar novas features
- Criar features adaptativas (ex: trend, velocidade de mudança)
- Re-engineer features existentes

**Exemplos:**
- Remover "vantagem casa" se deixou de ser relevante
- Adicionar "forma recente vs forma histórica"
- Criar "velocidade de mudança de odds"

### 3.5 Estratégia 5: Ensemble Adaptativo

**Quando usar:**
- Concept drift gradual
- Incerteza sobre estabilidade do conceito
- Necessidade de balancear estabilidade e adaptabilidade

**Ação:**
- Treinar múltiplos modelos em diferentes períodos
- Combinar predições com pesos baseados em performance recente
- Ajustar pesos dinamicamente

**Vantagens:**
- Robusto a mudanças graduais
- Não descarta conhecimento histórico
- Adapta-se automaticamente

**Desvantagens:**
- Mais complexo
- Requer mais recursos computacionais
- Difícil de interpretar

### 3.6 Estratégia 6: Pausa de Operações

**Quando usar:**
- Drift CRITICAL (PSI > 0.30)
- Incerteza sobre causa/impacto
- Risco de perdas significativas

**Ação:**
- Pausar novas apostas
- Continuar coleta de dados
- Investigar causa raiz
- Retomar após correção

**Procedimento:**
1. Alertar stakeholders
2. Pausar sistema de apostas
3. Investigar causa
4. Implementar correção
5. Validar em shadow mode
6. Retomar operações

---

## 4. PROCEDIMENTO DE RESPOSTA

### 4.1 Fluxograma de Decisão

```
Drift Detetado
    ↓
Verificar Severidade
    ↓
┌─────────────┬─────────────┬─────────────┐
│   INFO      │  WARNING    │   HIGH      │
└──────┬──────┴──────┬──────┴──────┬──────┘
       │             │             │
       ↓             ↓             ↓
  Monitorizar   Preparar      Retraining
                 Retraining    ou Pausa
       │             │             │
       └─────────────┴─────────────┘
                     ↓
              Verificar Causa
                     ↓
          ┌──────────┴──────────┐
          │                     │
          ↓                     ↓
    Causa Técnica         Causa Externa
          │                     │
          ↓                     ↓
    Corrigir Bug           Retraining
          │                     │
          └──────────┬──────────┘
                     ↓
              Validar Correção
                     ↓
              Deploy em Produção
                     ↓
              Monitorizar 7 dias
```

### 4.2 Tempos de Resposta

| Severidade | Tempo de Resposta | Ação Máxima |
|-----------|-------------------|-------------|
| INFO | 24h | Monitorização |
| WARNING | 4h | Preparar retraining |
| HIGH | 1h | Retraining ou pausa |
| CRITICAL | 15min | Pausar + investigar |

### 4.3 Checklist de Resposta

**Para drift INFO:**
- [ ] Loggar métricas
- [ ] Atualizar dashboard
- [ ] Reagendar próxima verificação
- [ ] Documentar se necessário

**Para drift WARNING:**
- [ ] Notificar equipa
- [ ] Analisar tendência
- [ ] Preparar dados para retraining
- [ ] Documentar plano de ação

**Para drift HIGH:**
- [ ] Alertar stakeholders
- [ ] Iniciar retraining
- [ ] Atualizar thresholds se necessário
- [ ] Preparar para shadow mode
- [ ] Documentar incidente

**Para drift CRITICAL:**
- [ ] Pausar operações
- [ ] Alertar stakeholders críticos
- [ ] Investigar causa raiz urgentemente
- [ ] Implementar correção
- [ ] Validar extensivamente
- [ ] Documentar incidente completo
- [ ] Realizar post-mortem

---

## 5. ESTRATÉGIAS DE DEPLOY

### 5.1 Canary Deployment

Deploy gradual para subset de usuários/ligas.

**Procedimento:**
1. Deploy novo modelo para 10% do tráfego
2. Monitorizar performance por 24h
3. Se estável, aumentar para 50%
4. Se estável, aumentar para 100%

**Vantagens:**
- Risco controlado
- Fácil rollback
- Deteta problemas em produção real

**Desvantagens:**
- Mais complexo
- Requer infraestrutura
- Tempo de rollout mais longo

### 5.2 Shadow Mode

Novo modelo roda em paralelo com antigo, mas não afeta decisões.

**Procedimento:**
1. Deploy novo modelo em shadow mode
2. Coletar predições de ambos os modelos
3. Comparar performance
4. Se novo modelo melhor, fazer switch

**Vantagens:**
- Zero risco para operações
- Comparação direta
- Fácil rollback

**Desvantagens:**
- Não testa em produção real
- Custo computacional duplicado
- Não dete problemas de integração

### 5.3 Blue-Green Deployment

Switch instantâneo entre versões do modelo.

**Procedimento:**
1. Deploy novo modelo em ambiente "green"
2. Validar extensivamente
3. Switch tráfego de "blue" para "green"
4. Manter "blue" disponível para rollback

**Vantagens:**
- Rollback instantâneo
- Zero downtime
- Validação completa antes do switch

**Desvantagens:**
- Requer infraestrutura duplicada
- Custo mais alto
- Não testa gradualmente

### 5.4 A/B Testing

Comparar modelos em produção com split de tráfego.

**Procedimento:**
1. Split tráfego 50/50 entre modelos
2. Coletar métricas de ambos
3. Teste estatístico para determinar vencedor
4. Deploy do vencedor

**Vantagens:**
- Comparação estatística rigorosa
- Teste em produção real
- Deteta diferenças subtis

**Desvantagens:**
- Mais complexo
- Requer mais tempo
- Pode expor usuários a modelo pior temporariamente

---

## 6. MONITORIZAÇÃO PÓS-CORREÇÃO

### 6.1 Período de Observação

Após correção, monitorizar por período mínimo de 7 dias.

**Métricas a monitorizar:**
- PSI das features
- Performance do modelo (accuracy, AUC, EV)
- Volume de apostas
- Lucro/prejuízo
- Alertas de drift

### 6.2 Critérios de Sucesso

Correção considerada bem-sucedida se:
- PSI < threshold por 7 dias consecutivos
- Performance ≥ baseline anterior
- Sem novos alertas CRITICAL
- Stakeholders satisfeitos

### 6.3 Rollback

Se correção não for bem-sucedida:
- Rollback para versão anterior
- Investigar falha
- Planejar nova abordagem
- Documentar lições aprendidas

---

## 7. DOCUMENTAÇÃO E LIÇÕES APRENDIDAS

### 7.1 Post-Mortem

Após cada incidente de drift significativo, realizar post-mortem.

**Seções:**
1. **Resumo:** O que aconteceu
2. **Timeline:** Cronologia do incidente
3. **Impacto:** Quanto custou
4. **Causa raiz:** Por que aconteceu
5. **Resposta:** O que foi feito
6. **Lições aprendidas:** O que aprendemos
7. **Ações preventivas:** Como evitar no futuro

### 7.2 Atualização de Documentação

Atualizar documentação baseada em incidentes:
- Thresholds se necessário
- Procedimentos de resposta
- Base de conhecimento
- Playbooks de incidentes

### 7.3 Melhoria Contínua

Implementar ciclo de melhoria:
1. Detetar incidente
2. Responder
3. Documentar
4. Analisar
5. Melhorar processos
6. Prevenir futuros incidentes

---

## 8. AUTOMAÇÃO

### 8.1 Auto-Retraining

Implementar retraining automático baseado em drift.

**Condições:**
- PSI > 0.25 E performance cai > 10%
- Concept drift confirmado (adversarial AUC > 0.70)
- Causa não técnica (não é bug)

**Safeguards:**
- Validação obrigatória antes do deploy
- Shadow mode obrigatório por 24h
- Aprovação manual para CRITICAL

### 8.2 Auto-Rollback

Implementar rollback automático se novo modelo falhar.

**Condições:**
- Performance cai > 15% em 1h
- Alertas CRITICAL contínuos
- Erros de sistema

**Procedimento:**
1. Detetar falha
2. Rollback automático para versão anterior
3. Alertar equipa
4. Investigar causa

---

## 9. PLAYBOOKS

### 9.1 Playbook: Feature Drift Moderado

**Cenário:** PSI 0.20 - 0.30 em feature não crítica

**Passos:**
1. Verificar se há correlação com eventos externos
2. Se sim, ajustar threshold temporariamente
3. Se não, preparar retraining
4. Retreinar com dados recentes
5. Validar em shadow mode
6. Deploy se performance ≥ baseline

**Tempo estimado:** 8-12h

### 9.2 Playbook: Feature Drift Crítico

**Cenário:** PSI > 0.30 em feature crítica

**Passos:**
1. Pausar operações imediatamente
2. Investigar causa raiz
3. Se causa técnica, corrigir bug
4. Se causa externa, retreinar modelo
5. Validar extensivamente
6. Deploy em canary
7. Monitorizar 48h
8. Retomar operações

**Tempo estimado:** 24-48h

### 9.3 Playbook: Concept Drift

**Cenário:** Performance cai > 15% sem feature drift

**Passos:**
1. Analisar feature importance
2. Identificar features cuja relação mudou
3. Retreinar com janela deslizante (últimos 3 meses)
4. Considerar feature engineering adaptativa
5. Validar em holdout set
6. Deploy em shadow mode por 48h
7. Se melhor, fazer switch completo

**Tempo estimado:** 24-48h

### 9.4 Playbook: Target Drift

**Cenário:** Proporção de outcomes muda > 5%

**Passos:**
1. Verificar se é sazonalidade
2. Se sim, ajustar baseline para mesma época
3. Se não, investigar causa externa
4. Se mudança permanente, retreinar modelo
5. Monitorizar performance
6. Ajustar estratégia de apostas se necessário

**Tempo estimado:** 12-24h

---

## 10. MELHORIAS FUTURAS

- [ ] Implementar auto-remediação para causas comuns
- [ ] Desenvolver sistema de recomendação de ação
- [ ] Adicionar simulação de impacto antes da ação
- [ ] Implementar A/B testing automático de estratégias
- [ ] Desenvolver dashboard de custo-benefício de ações

---

## 11. LINKS CRUZADOS

- [[48_Data_Drift/INDEX]] ← Secção mãe
- [[48_Data_Drift/DETECAO_FEATURE_DRIFT]] → Detecção de feature drift
- [[48_Data_Drift/DETECAO_PREDICTION_DRIFT]] → Detecção de prediction drift
- [[48_Data_Drift/DETECAO_TARGET_DRIFT]] → Detecção de target drift
- [[48_Data_Drift/DETECAO_CONCEPT_DRIFT]] → Detecção de concept drift
- [[48_Data_Drift/ALERTAS_DRIFT]] → Sistema de alertas
- [[48_Data_Drift/ANALISE_CAUSAS_DRIFT]] → Análise de causas
- [[11_MLOps/INDEX]] → Operações de MLOps