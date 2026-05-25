# GESTAO_MULTIPLAS_CONTAS — Gestão de Contas em Múltiplos Bookmakers

**ID:** `BK-005` | **Fase:** #phase/3-6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar estratégias e processos para gerir múltiplas contas em diferentes casas de apostas, maximizando volume, minimizando riscos de limitação e garantindo operação sustentável longo prazo.

**Princípio:** Diversificação de contas = diversificação de risco = sustentabilidade da operação.

---

## 2. CONCEITOS FUNDAMENTAIS

### 2.1 Por Que Múltiplas Contas?

**Benefícios:**

1. **Aumentar Volume Total**
   - Uma conta por casa tem limites
   - Múltiplas contas = múltiplos limites
   - Escalar operação sem bloqueios

2. **Diversificar Risco Operacional**
   - Se uma conta é limitada, outras continuam
   - Se uma casa tem problemas, outras compensam
   - Reduz dependência de única fonte

3. **Aproveitar Oportunidades Únicas**
   - Diferentes casas têm diferentes odds
   - Promoções específicas por conta
   - Arbitragem entre contas

4. **Line Shopping Efetivo**
   - Comparar odds entre múltiplas casas
   - Selecionar sempre a melhor odd
   - Maximizar ROI

5. **Gestão de Liquidez**
   - Distribuir apostas entre contas
   - Não mover mercado em única casa
   - Execução mais eficiente

### 2.2 Tipos de Contas

**Por Casa de Apostas:**

| Casa | Nº Recomendado de Contas | Justificação |
|------|--------------------------|--------------|
| **Betfair Exchange** | 1-2 | Limites altos, não limita |
| **Pinnacle** | 1-2 | Não limita vencedores |
| **Smarkets** | 2-3 | Limites médios, pode limitar |
| **Matchbook** | 1-2 | Liquidez baixa, 1-2 suficiente |
| **Soft Books** | 3-5 cada | Limitam rapidamente |

**Por Função:**

| Tipo | Descrição | Uso |
|------|-----------|-----|
| **Conta Primária** | Conta principal em cada casa | 70-80% do volume |
| **Conta Secundária** | Conta backup | 15-20% do volume |
| **Conta de Arbitragem** | Específica para arbitragem | 5-10% do volume |
| **Conta de Teste** | Para experimentação | Volume mínimo |

### 2.3 Arquitetura de Contas

**Estrutura Recomendada:**

```
Nível 1: Contas Exchange (Não limitam)
├── Betfair Conta 1 (Primária)
├── Betfair Conta 2 (Backup)
├── Smarkets Conta 1 (Primária)
└── Smarkets Conta 2 (Backup)

Nível 2: Contas Sharp (Limitam pouco)
├── Pinnacle Conta 1 (Primária)
└── Pinnacle Conta 2 (Backup, se disponível)

Nível 3: Contas Soft (Limitam rápido)
├── Soft Book A Conta 1
├── Soft Book A Conta 2
├── Soft Book A Conta 3
├── Soft Book B Conta 1
├── Soft Book B Conta 2
└── Soft Book B Conta 3
```

---

## 3. ESTRATÉGIA DE ABERTURA DE CONTAS

### 3.1 Ordem de Prioridade

**Fase 1 (Essencial):**
1. Betfair Exchange (1 conta)
2. Pinnacle (1 conta, se disponível)

**Fase 2 (Recomendado):**
3. Smarkets (1-2 contas)
4. Betfair Conta 2 (backup)

**Fase 3 (Expansão):**
5. Matchbook (1-2 contas)
6. Soft books selecionadas (2-3 contas cada)

**Fase 4 (Escala):**
7. Contas adicionais em soft books
8. Contas em exchanges alternativas

### 3.2 Processo de Abertura

**Checklist por Conta:**

- [ ] Verificar disponibilidade no país
- [ ] Ler e entender T&C
- [ ] Preparar documentação (KYC)
- [ ] Escolher método de depósito
- [ ] Abrir conta com dados corretos
- [ ] Completar KYC
- [ ] Testar depósito pequeno
- [ ] Testar aposta pequena
- [ ] Testar levantamento
- [ ] Configurar autenticação 2FA
- [ ] Guardar credenciais seguramente

**Documentação Necessária:**
- Identificação válida (passaporte/BI)
- Comprovativo de residência
- Comprovativo de renda (algumas casas)
- Foto/selfie (algumas casas)

### 3.3 Gestão de Identidades

**Considerações Legais:**
- Múltiplas contas por pessoa podem violar T&C
- Identidades falsas são ilegais
- Consultar advogado local antes

**Abordagens Legais:**

1. **Contas Individuais**
   - Uma conta por pessoa por casa
   - Legal e compliant
   - Limitado em escala

2. **Contas Familiares**
   - Contas em nome de familiares
   - Legal se com consentimento
   - Requer gestão coordenada

3. **Estrutura Corporativa**
   - Contas em nome de empresa
   - Legal se estrutura adequada
   - Requer setup legal e fiscal

**Recomendação:** Começar com contas individuais, expandir apenas com aconselhamento legal

---

## 4. GESTÃO DE BANKROLL

### 4.1 Distribuição de Capital

**Estrutura Recomendada:**

| Nível | Tipo de Conta | % do Bankroll |
|-------|---------------|---------------|
| **1** | Exchanges (Betfair, Smarkets) | 50% |
| **2** | Sharp Books (Pinnacle) | 20% |
| **3** | Soft Books | 20% |
| **4** | Reserva de Liquidez | 10% |

**Distribuição por Conta:**

```
Bankroll Total: €10,000

Nível 1 - Exchanges (€5,000):
├── Betfair Conta 1: €2,500
├── Betfair Conta 2: €1,500
├── Smarkets Conta 1: €750
└── Smarkets Conta 2: €250

Nível 2 - Sharp Books (€2,000):
├── Pinnacle Conta 1: €2,000

Nível 3 - Soft Books (€2,000):
├── Soft Book A Conta 1: €500
├── Soft Book A Conta 2: €300
├── Soft Book B Conta 1: €500
└── Soft Book B Conta 2: €700

Nível 4 - Reserva (€1,000):
└── Conta bancária ou exchange de cripto
```

### 4.2 Gestão de Fluxo de Caixa

**Depósitos:**
- Estratégico: Depositar em contas com oportunidades
- Regular: Manter saldo mínimo em cada conta
- Oportunidade: Depositar adicional quando arbitragem

**Levantamentos:**
- Regular: Levantar lucros mensalmente
- Rebalanceamento: Mover capital entre contas
- Emergência: Levantar se conta em risco

**Regras:**
- Nunca manter mais de 20% do bankroll em única soft book
- Manter mínimo de 10x stake média em cada conta ativa
- Levantar lucros de soft books semanalmente
- Rebalancear mensalmente baseado em performance

### 4.3 Gestão de Limites

**Monitorização de Limites:**
```
Para cada conta:
- Stake máximo permitido
- Stake máximo por aposta
- Stake máximo por dia/semana
- Mercados disponíveis
- Restrições especiais
```

**Alertas:**
- Limite reduzido > 30% → Alerta
- Limite reduzido > 50% → Ação imediata
- Mercado bloqueado → Considerar rotação
- Conta suspensa → Investigar

---

## 5. GESTÃO DE APOSTAS

### 5.1 Alocação de Apostas

**Estratégia de Distribuição:**

```
Para cada aposta:

1. Identificar casas com melhor odd
2. Verificar liquidez em cada casa
3. Calcular stake por casa baseado em:
   - Liquidez disponível
   - Limite da conta
   - Distribuição desejada
4. Executar em ordem de prioridade
```

**Algoritmo de Alocação:**
```python
def allocate_bet(bet_signal, accounts, total_stake):
    """
    Aloca aposta entre múltiplas contas
    """
    allocations = []

    # Ordenar contas por odd (melhor primeiro)
    sorted_accounts = sorted_by_odds(accounts, bet_signal)

    remaining_stake = total_stake

    for account in sorted_accounts:
        if remaining_stake <= 0:
            break

        # Calcular stake máximo possível nesta conta
        max_stake = min(
            remaining_stake,
            account['limit_per_bet'],
            account['available_balance'],
            account['liquidity_at_odds']
        )

        if max_stake > 0:
            allocations.append({
                'account': account['id'],
                'stake': max_stake,
                'odds': account['odds']
            })
            remaining_stake -= max_stake

    return allocations
```

### 5.2 Rotação de Contas

**Objetivos:**
- Evitar padrões detetáveis
- Prolongar vida de contas soft books
- Distribuir volume uniformemente

**Estratégias:**

1. **Rotação por Tempo**
   - Alternar contas a cada X dias
   - Ex: Conta A dias 1-3, Conta B dias 4-6

2. **Rotação por Volume**
   - Alternar após X apostas
   - Ex: Conta A 10 apostas, Conta B 10 apostas

3. **Rotação por Mercado**
   - Diferentes contas para diferentes mercados
   - Ex: Conta A Moneyline, Conta B Spread

4. **Rotação Aleatória**
   - Seleção aleatória entre contas
   - Mais difícil de detetar padrões

**Implementação:**
```python
class AccountRotator:
    def __init__(self, accounts):
        self.accounts = accounts
        self.rotation_strategy = 'volume'  # time, volume, market, random
        self.rotation_counter = {}

    def select_account(self, market, soft_book):
        """
        Seleciona conta para aposta
        """
        available_accounts = [
            acc for acc in self.accounts
            if acc['soft_book'] == soft_book
            and acc['status'] == 'active'
        ]

        if self.rotation_strategy == 'volume':
            return self._rotate_by_volume(available_accounts)
        elif self.rotation_strategy == 'time':
            return self._rotate_by_time(available_accounts)
        elif self.rotation_strategy == 'random':
            return random.choice(available_accounts)

    def _rotate_by_volume(self, accounts):
        """Rotação por volume de apostas"""
        # Selecionar conta com menos apostas recentes
        return min(accounts, key=lambda x: x['recent_bets'])

    def _rotate_by_time(self, accounts):
        """Rotação por tempo"""
        current_day = datetime.now().day
        account_index = current_day % len(accounts)
        return accounts[account_index]
```

---

## 6. MONITORIZAÇÃO E MANUTENÇÃO

### 6.1 Métricas por Conta

**Métricas a Monitorizar:**

| Métrica | Descrição | Freqüência |
|---------|-----------|------------|
| **Saldo** | Balance atual | Diária |
| **Lucro/Prejuízo** | P/L total | Diária |
| **ROI** | Retorno sobre investimento | Semanal |
| **Nº de Apostas** | Volume de apostas | Diária |
| **Stake Médio** | Tamanho médio de aposta | Semanal |
| **Limite Atual** | Stake máximo permitido | Diária |
| **Status** | Ativa/Limitada/Suspensa | Diária |
| **Última Atividade** | Data da última aposta | Diária |

### 6.2 Dashboard de Contas

**Componentes:**

```
┌─────────────────────────────────────┐
│  DASHBOARD DE CONTAS                │
├─────────────────────────────────────┤
│  Resumo Global                      │
│  - Bankroll Total: €10,000         │
│  - Lucro Hoje: €150                │
│  - Contas Ativas: 8/10             │
│  - Alertas: 2                      │
├─────────────────────────────────────┤
│  Status por Conta                   │
│  Betfair 1: €2,500 | Ativa ✓       │
│  Betfair 2: €1,500 | Ativa ✓       │
│  Pinnacle 1: €2,000 | Ativa ✓       │
│  Soft A 1: €500 | Limitada ⚠       │
│  Soft A 2: €300 | Ativa ✓          │
├─────────────────────────────────────┤
│  Alertas                            │
│  - Soft A 1: Limite reduzido 50%   │
│  - Soft B 1: Necessita depósito    │
└─────────────────────────────────────┘
```

### 6.3 Manutenção Regular

**Tarefas Diárias:**
- [ ] Verificar saldo de todas as contas
- [ ] Rever alertas
- [ ] Verificar limites
- [ ] Confirmar que todas as APIs estão funcionando

**Tarefas Semanais:**
- [ ] Analisar performance por conta
- [ ] Levantar lucros de soft books
- [ ] Rebalancear bankroll se necessário
- [ ] Rever estratégia de rotação

**Tarefas Mensais:**
- [ ] Análise completa de todas as contas
- [ ] Avaliar necessidade de novas contas
- [ ] Revisar T&C de cada casa
- [ ] Atualizar documentação

---

## 7. SEGURANÇA

### 7.1 Gestão de Credenciais

**Melhores Práticas:**

1. **Password Manager**
   - Usar password manager (1Password, Bitwarden)
   - Passwords únicas e fortes
   - Nunca reutilizar passwords

2. **Two-Factor Authentication (2FA)**
   - Ativar 2FA em todas as contas
   - Usar app autenticador (Google Authenticator)
   - Nunca usar SMS 2FA (vulnerável)

3. **Acesso Separado**
   - Contas de produção vs teste
   - Níveis de acesso diferentes
   - Princípio de menor privilégio

4. **Backup**
   - Backup seguro de credenciais
   - Armazenado offline
   - Acessível apenas por pessoas autorizadas

### 7.2 Segurança de APIs

**Práticas:**

1. **API Keys**
   - Nunca hardcoded em código
   - Armazenar em environment variables
   - Rotacionar regularmente

2. **Rate Limiting**
   - Respeitar rate limits de cada API
   - Implementar backoff exponencial
   - Monitorizar usage

3. **Logging**
   - Log todas as chamadas de API
   - Não logar credenciais
   - Logs armazenados seguramente

### 7.3 Detecção de Fraude

**Monitorizar:**
- Login incomuns (IP, localização)
- Acesso múltiplos simultâneos
- Mudanças de senha não autorizadas
- Transações não reconhecidas

**Resposta a Incidentes:**
1. Mudar password imediatamente
2. Revogar todas as sessões
3. Ativar 2FA se não ativo
4. Contactar suporte da casa
5. Rever todas as transações recentes

---

## 8. COMPLIANCE LEGAL

### 8.1 Conformidade com T&C

**Princípios:**
- Ler e entender T&C de cada casa
- Seguir todas as regras
- Não violar termos propositadamente
- Documentar compliance

**Comum em T&C:**
- Uma conta por pessoa
- Proibido uso de bots (sem autorização)
- Proibido arbitragem (algumas casas)
- Proibido compartilhamento de conta

### 8.2 Impostos

**Considerações:**
- Lucros de apostas podem ser tributáveis
- Diferente por país
- Requer consulta contabilista
- Manter registos detalhados

**Documentação Necessária:**
- Histórico de todas as apostas
- Registo de depósitos e levantamentos
- Cálculo de lucro/prejuízo
- Comprovativos de transações

### 8.3 KYC/AML

**Know Your Customer:**
- Fornecer documentação correta
- Manter informação atualizada
- Cooperar com verificações

**Anti-Money Laundering:**
- Fonte de fundos documentada
- Transações justificadas
- Compliance com regulamentos locais

---

## 9. ESTRATÉGIA POR FASE

### 9.1 Fase 4-6 (Micro-Small Banca: €100-1,000)

**Estratégia:**
- 1-2 contas (Betfair + Pinnacle se disponível)
- Gestão manual simples
- Foco em aprender processo
- Sem rotação necessária

### 9.2 Fase 7-9 (Medium Banca: €1,000-10,000)

**Estratégia:**
- 4-6 contas (exchanges + 2-3 soft books)
- Sistema semi-automatizado
- Rotação básica de contas
- Dashboard de monitorização

### 9.3 Fase 10+ (Large Banca: €10,000+)

**Estratégia:**
- 8-15 contas (todas as categorias)
- Sistema completamente automatizado
- Rotação sofisticada
- Dashboard avançado com alertas

---

## 10. BACKLOG TÉCNICO

- [ ] Implementar sistema de gestão de contas
- [ ] Criar dashboard de monitorização em tempo real
- [ ] Desenvolver algoritmo de rotação de contas
- [ ] Implementar sistema de alocação de apostas
- [ ] Criar sistema de alertas automáticos
- [ ] Desenvolver módulo de segurança de credenciais
- [ ] Implementar sistema de backup de contas
- [ ] Criar relatórios de performance por conta

---

## 11. LINKS CRUZADOS

- [[45_Bookmaker_Analysis/INDEX]] ← Secção mãe
- [[SOFT_BOOKS_ANALYSIS]] → Análise soft vs sharp books
- [[ARBITRAGEM_BOOKMAKERS]] → Estratégias de arbitragem
- [[RISCOS_LIMITACAO]] → Riscos de limitação/banimento
- [[DIVERSIFICACAO_CONTAS]] → Estratégias de diversificação