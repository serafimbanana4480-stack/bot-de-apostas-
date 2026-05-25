# RISCOS_LIMITACAO — Riscos de Limitação e Banimento

**ID:** `BK-006` | **Fase:** #phase/3-6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar os riscos de limitação e banimento por casas de apostas, identificar padrões de deteção, desenvolver estratégias de mitigação e criar planos de contingência para operação sustentável.

**Princípio:** Limitação é inevitável em soft books; o objetivo é prolongar vida útil e mitigar impacto através de diversificação.

---

## 2. CONCEITOS FUNDAMENTAIS

### 2.1 O Que é Limitação

**Definição:** Redução dos limites de aposta ou restrição de acesso a certos mercados por uma casa de apostas para apostadores considerados "vencedores" ou "profissionais".

**Tipos de Limitação:**

| Tipo | Descrição | Reversível |
|------|-----------|------------|
| **Redução de Stake** | Limite máximo reduzido | Raramente |
| **Bloqueio de Mercados** | Acesso negado a certos mercados | Raramente |
| **Remoção de Promoções** | Bónus e ofertas removidos | Permanente |
| **Aumento de Margem** | Odds piores para conta específica | Raramente |
| **Account Review** | Revisão manual da conta | Temporário |
| **Account Closure** | Conta fechada permanentemente | Não |

### 2.2 O Que é Banimento

**Definição:** Encerramento permanente de conta e proibição de abrir novas contas, frequentemente estendido a todas as casas do mesmo grupo.

**Cenários de Banimento:**
- Violação grave de T&C (fraude, identidade falsa)
- Arbitragem agressiva e detetável
- Uso de bots sem autorização
- Múltiplas contas por mesma pessoa (se proibido)
- Compartilhamento de conta
- Lavagem de dinheiro suspeita

### 2.3 Ciclo de Vida de Conta

**Timeline Típica em Soft Books:**

```
Semana 1-2: Conta Nova
├── Limites normais
├── Sem restrições
└── Oportunidade máxima

Semana 3-4: Monitorização
├── Casa analisa padrões
├── Primeiros sinais de alerta
└── CLV positivo notado

Semana 5-8: Limitação Parcial
├── Limites reduzidos 30-50%
├── Alguns mercados bloqueados
└── Promoções removidas

Semana 9-12: Limitação Total
├── Limites muito baixos (€5-20)
├── Apenas mercados populares
└── Sem promoções

Semana 13+: Encerramento (opcional)
├── Conta fechada
├── Saldo devolvido
└── Banimento do grupo
```

**Variação:** 2 semanas a 6 meses dependendo da casa e estratégia

---

## 3. MÉTODOS DE DETEÇÃO

### 3.1 Padrões Comportamentais

**1. CLV Positivo Consistente**
```
Deteção:
- Apostador consistentemente captura CLV > 2%
- Odds apostadas são melhores que closing
- Padrão claro de value betting

Mitigação:
- Misturar apostas com CLV negativo
- Apostar em mercados menos populares
- Variar timing das apostas
```

**2. Apostas em Linhas que Movem**
```
Deteção:
- Apostas imediatamente após movimento de linha
- Steam chasing (seguir movimentos rápidos)
- Padrão de apostar em odds que caem

Mitigação:
- Esperar 5-10 minutos após movimento
- Não seguir steam moves
- Apostar em linhas estáveis
```

**3. Stakes Máximos Frequentes**
```
Deteção:
- Apostas sempre no limite máximo
- Padrão de maximizar stakes
- Uso agressivo de limites

Mitigação:
- Variar stakes (50-100% do limite)
- Apostas abaixo do limite ocasionalmente
- Misturar stakes pequenos e grandes
```

**4. Arbitragem Óbvia**
```
Deteção:
- Apostas simultâneas em casas diferentes
- Cobertura de todos os resultados
- Padrão de surebets

Mitigação:
- Evitar arbitragem óbvia
- Adicionar delay entre apostas
- Não cobrir todos os resultados sempre
```

### 3.2 Padrões Técnicos

**1. Uso de Bots/Automação**
```
Deteção:
- Apostas com timing perfeito (exatamente X segundos)
- Velocidade de execução humana impossível
- Padrões de timing não naturais
- User-agent suspeito

Mitigação:
- Adicionar delay aleatório (2-10s)
- Variar timing entre apostas
- Usar user-agent realista
- Simular comportamento humano
```

**2. Múltiplos Logins/Dispositivos**
```
Deteção:
- Logins de múltiplos IPs
- Dispositivos diferentes
- Padrões de acesso suspeitos
- Geolocalização inconsistente

Mitigação:
- Usar mesmo IP/dispositivo
- VPN consistente (se necessário)
- Evitar logins excessivos
```

**3. API Usage Patterns**
```
Deteção:
- Requests em intervalos regulares
- Rate limit hitting
- User-agent de API
- Padrões não humanos

Mitigação:
- Randomizar intervalos
- Respeitar rate limits
- Usar headers realistas
- Implementar backoff
```

### 3.3 Padrões de Mercado

**1. Mercados "Sharp"**
```
Deteção:
- Apostas apenas em mercados eficientes
- Evitar mercados recreacionais
- Foco em line value

Mitigação:
- Misturar mercados recreacionais
- Apostar ocasionalmente em favoritos populares
- Incluir apostas "recreacionais"
```

**2. Mercados de Baixa Liquidez**
```
Deteção:
- Apostas em mercados obscuros
- Explorar ineficiências de nicho
- Padrão de arbitragem em nicho

Mitigação:
- Misturar com mercados populares
- Não focar exclusivamente em nicho
- Variar tipos de mercado
```

**3. Timing Incomum**
```
Deteção:
- Apostas sempre no mesmo horário
- Apostas em horários de baixa atividade
- Padrões de timing não naturais

Mitigação:
- Variar horários de aposta
- Apostar em horários de pico ocasionalmente
- Distribuir apostas ao longo do dia
```

---

## 4. ESTRATÉGIAS DE MITIGAÇÃO

### 4.1 Camuflagem Comportamental

**Técnicas:**

1. **Misturar Apostas Recreacionais**
   - 20-30% das apostas em favoritos populares
   - Apostas sem edge claro
   - Cash-out ocasional

2. **Variar Stakes**
   - Não sempre no máximo
   - Distribuir entre 50-100% do limite
   - Apostas pequenas ocasionalmente

3. **Diversificar Mercados**
   - Não focar apenas em value
   - Incluir spread, totals, props
   - Apostar em diferentes ligas

4. **Timing Variável**
   - Não apostar sempre no mesmo momento
   - Distribuir ao longo do dia
   - Evitar padrões de timing

5. **Comportamento "Humano"**
   - Pequenos delays entre ações
   - Navegação no site antes de apostar
   - Pausas ocasionais

### 4.2 Camuflagem Técnica

**Técnicas:**

1. **Randomização de Delays**
```python
import random
import time

def human_delay(min_seconds=2, max_seconds=10):
    """Delay aleatório para simular humano"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
```

2. **User-Agent Realista**
```python
import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    # ... mais user-agents
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)
```

3. **Rate Limiting Respeitoso**
```python
import time

class RateLimiter:
    def __init__(self, requests_per_minute=30):
        self.min_interval = 60 / requests_per_minute
        self.last_request = 0

    def wait(self):
        now = time.time()
        elapsed = now - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()
```

### 4.3 Gestão de Múltiplas Contas

**Estratégias:**

1. **Rotação de Contas**
   - Alternar entre contas
   - Distribuir volume uniformemente
   - Pausas entre uso de mesma conta

2. **Separar Estratégias**
   - Conta A: Value betting
   - Conta B: Arbitragem
   - Conta C: Apostas recreacionais

3. **Diversificar Identidades**
   - Diferentes métodos de pagamento
   - Diferentes dispositivos (se legal)
   - Diferentes IPs (se legal)

---

## 5. DETEÇÃO PRECOCE

### 5.1 Sinais de Alerta

**Sinais Imediatos:**

| Sinal | Ação |
|-------|------|
| **Limite reduzido > 30%** | Reduzir volume, preparar rotação |
| **Mercado bloqueado** | Evitar mercado, verificar outros |
| **Promoção removida** | Esperar limitação adicional |
| **Aumento de margem** | Preparar para encerramento |
| **Account review** | Parar apostas, aguardar |

**Sinais Graduais:**

| Sinal | Ação |
|-------|------|
| **CLV reduzindo** | Ajustar estratégia |
| **Limites estáticos** | Conta pode ser monitorizada |
| **Menos liquidez** | Casa pode estar restringindo |
| **Slow execution** | Possível throttling |

### 5.2 Sistema de Monitorização

**Métricas a Monitorizar:**

```python
class LimitationMonitor:
    def __init__(self):
        self.alerts = []

    def check_account(self, account):
        """Verifica sinais de limitação"""
        alerts = []

        # Verificar limite
        if account['limit_reduction'] > 0.3:
            alerts.append({
                'severity': 'HIGH',
                'message': f"Limite reduzido {account['limit_reduction']*100}%",
                'action': 'reduce_volume'
            })

        # Verificar CLV
        if account['clv_avg_7d'] < 0.01:
            alerts.append({
                'severity': 'MEDIUM',
                'message': "CLV reduzindo",
                'action': 'review_strategy'
            })

        # Verificar mercados bloqueados
        if len(account['blocked_markets']) > 0:
            alerts.append({
                'severity': 'MEDIUM',
                'message': f"Mercados bloqueados: {account['blocked_markets']}",
                'action': 'avoid_markets'
            })

        return alerts
```

---

## 6. PLANO DE CONTINGÊNCIA

### 6.1 Quando Limitação Ocorre

**Passos Imediatos:**

1. **Parar Apostas na Conta**
   - Reduzir volume a 0
   - Não forçar limites

2. **Avaliar Situação**
   - Tipo de limitação
   - Reversível ou permanente
   - Impacto na operação

3. **Ativar Conta Backup**
   - Redirecionar volume para conta alternativa
   - Ajustar alocação de bankroll

4. **Revisar Estratégia**
   - O que causou limitação?
   - Como prevenir no futuro?
   - Ajustar comportamento

### 6.2 Quando Banimento Ocorre

**Passos Imediatos:**

1. **Levantar Fundos**
   - Solicitar levantamento imediato
   - Documentar todas as transações
   - Guardar comprovativos

2. **Contactar Suporte**
   - Clarificar motivo do banimento
   - Tentar apelar se injusto
   - Documentar comunicação

3. **Avaliar Impacto Legal**
   - Consultar advogado se necessário
   - Verificar compliance com T&C
   - Documentar tudo

4. **Ativar Plano de Recuperação**
   - Redirecionar volume para outras casas
   - Abrir novas contas (se legal)
   - Ajustar estratégia geral

### 6.3 Plano de Recuperação

**Estratégias:**

1. **Diversificação Acelerada**
   - Abrir contas em casas adicionais
   - Reduzir dependência de casas limitadas
   - Aumentar número de contas ativas

2. **Mudança de Estratégia**
   - Reduzir arbitragem
   - Aumentar value betting em sharp books
   - Focar em exchanges

3. **Melhoria de Camuflagem**
   - Revisar e melhorar técnicas
   - Implementar mais randomização
   - Aumentar comportamento "recreacional"

4. **Expansão Geográfica**
   - Considerar casas em outros países
   - Verificar legalidade
   - Consultar advogado

---

## 7. PREVENÇÃO

### 7.1 Melhores Práticas

**Antes de Começar:**

1. **Ler e Entender T&C**
   - Conhecer regras de cada casa
   - Entender o que é proibido
   - Documentar restrições

2. **Começar Conservadoramente**
   - Stakes pequenos inicialmente
   - Aumentar gradualmente
   - Construir histórico "normal"

3. **Construir Perfil Recreacional**
   - Misturar apostas recreacionais
   - Apostar em favoritos populares
   - Usar cash-out ocasionalmente

**Durante Operação:**

1. **Monitorizar Continuamente**
   - Métricas de performance
   - Sinais de limitação
   - Comportamento da conta

2. **Variar Comportamento**
   - Não seguir padrões detetáveis
   - Randomizar ações
   - Simular comportamento humano

3. **Diversificar**
   - Múltiplas contas
   - Múltiplas casas
   - Múltiplas estratégias

### 7.2 O Que Evitar

**Práticas de Alto Risco:**

❌ **Nunca:**
- Usar identidade falsa
- Criar múltiplas contas por mesma pessoa (se proibido)
- Usar bots sem autorização
- Violair T&C propositadamente
- Compartilhar contas
- Manipular odds

⚠️ **Evitar:**
- Arbitragem óbvia e frequente
- Apostas sempre no máximo
- CLV extremamente alto consistente
- Steam chasing agressivo
- Padrões de timing não naturais
- Foco exclusivo em value

---

## 8. ANÁLISE DE CASAS

### 8.1 Casas por Nível de Risco

**Baixo Risco (Não limitam):**
- Betfair Exchange (★★★★★)
- Pinnacle (★★★★★)
- Outras sharp books

**Médio Risco (Limitam moderadamente):**
- Smarkets (★★★)
- Matchbook (★★★)
- Algumas soft books europeias

**Alto Risco (Limitam agressivamente):**
- Bet365 (★)
- William Hill (★)
- DraftKings (★)
- FanDuel (★)
- Maioria das soft books

### 8.2 Estratégia por Casa

**Betfair Exchange:**
- Risco: Muito baixo
- Estratégia: Apostar normalmente, sem restrições
- Monitorização: Mínima necessária

**Pinnacle:**
- Risco: Muito baixo
- Estratégia: Apostar normalmente, focar em CLV
- Monitorização: CLV e performance

**Smarkets:**
- Risco: Médio
- Estratégia: Alguma camuflagem, variar stakes
- Monitorização: Limites e CLV

**Soft Books:**
- Risco: Alto
- Estratégia: Camuflagem agressiva, rotação de contas
- Monitorização: Contínua, alertas ativos

---

## 9. MÉTRICAS DE MONITORIZAÇÃO

### 9.1 KPIs

| KPI | Descrição | Target |
|-----|-----------|--------|
| **Vida Média de Conta** | Tempo até limitação | > 3 meses |
| **Taxa de Limitação** | % de contas limitadas por mês | < 20% |
| **CLV Médio** | CLV para evitar deteção | 1-3% |
| **Diversificação** | Nº de contas ativas | > 5 |
| **Impacto de Limitação** | % de volume perdido | < 10% |

### 9.2 Alertas

**Gerar Alerta Se:**
- Conta limitada > 30%
- CLV > 4% consistente
- Vida de conta < 1 mês
- Taxa de limitação > 30%/mês
- Mais de 2 contas limitadas em 7 dias

---

## 10. CONSIDERAÇÕES ÉTICAS E LEGAIS

### 10.1 Ética

**É Ético Tentar Evitar Limitação?**
- Sim: É jogo legítimo dentro das regras
- Sim: Casas aceitam este risco no modelo
- Não: Se usar métodos fraudulentos

**Perspectiva:**
- Camuflagem comportamental é aceitável
- Fraude e identidade falsa não são
- Respeitar T&C é essencial

### 10.2 Legalidade

**Aspectos Legais:**
- Múltiplas contas: Verificar T&C
- Identidades falsas: Ilegal
- Automação: Verificar T&C
- VPN: Pode violar T&C

**Recomendação:**
- Consultar advogado local
- Seguir T&C estritamente
- Documentar compliance
- Evitar práticas ilegais

---

## 11. BACKLOG TÉCNICO

- [ ] Implementar sistema de monitorização de limitação
- [ ] Desenvolver módulo de camuflagem comportamental
- [ ] Criar sistema de alertas automáticos
- [ ] Implementar algoritmo de rotação de contas
- [ ] Desenvolver dashboard de métricas por conta
- [ ] Criar sistema de detecção precoce
- [ ] Implementar plano de contingência automatizado
- [ ] Documentar T&C de cada casa

---

## 12. LINKS CRUZADOS

- [[45_Bookmaker_Analysis/INDEX]] ← Secção mãe
- [[SOFT_BOOKS_ANALYSIS]] → Análise soft vs sharp books
- [[GESTAO_MULTIPLAS_CONTAS]] → Gestão de contas múltiplas
- [[DIVERSIFICACAO_CONTAS]] → Estratégias de diversificação
- [[ARBITRAGEM_BOOKMAKERS]] → Estratégias de arbitragem