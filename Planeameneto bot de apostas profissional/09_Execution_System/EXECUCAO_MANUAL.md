# EXECUCAO_MANUAL — Fase 1

**ID:** `EX-001` | **Fase:** #phase/4 | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar o sistema de execução manual de apostas como primeira fase de maturidade do sistema de execução. Na execução manual, sinais gerados pelo motor de value são enviados via Telegram e email, e um operador humano executa as apostas manualmente na casa de apostas. O objetivo é validar o sistema em produção com dinheiro real antes de implementar automação, permitindo aprendizado sobre slippage real, latência de execução, e qualidade dos sinais. Execução manual é a fase mais segura e controlada, ideal para validação inicial.

---

## 2. POR QUE EXECUÇÃO MANUAL?

### 2.1 Validação em Produção

Antes de automatizar, é essencial validar que:
- Os sinais têm edge real em produção (não apenas em backtest)
- As casas de apostas aceitam as apostas sem problemas
- O slippage real é aceitável
- O timing de sinais é adequado
- Não há bugs críticos no pipeline de geração de sinais

Execução manual permite observar e aprender这些问题 antes de escalar com automação.

### 2.1.1 Aprendizado Operacional

Execução manual gera insights valiosos:
- Quais horários têm mais slippage?
- Quais mercados são mais difíceis de executar?
- Quais tipos de sinais têm maior taxa de rejeição?
- Como as casas de apostas reagem ao nosso padrão de apostas?

Estes insights informam decisões de design para fases posteriores (one-click, automação).

### 2.2 Minimização de Risco

Execução manual minimiza risco de erros em escala:
- Erro humano afeta apenas uma aposta por vez
- Pausa imediata se problema é detetado
- Reversão fácil se estratégia não está funcionando
- Sem risco de erros de API em escala

### 2.3 Complacência Regulatória

Em algumas jurisdições, execução automática pode ter implicações regulatórias. Execução manual é geralmente aceita sem restrições especiais.

---

## 3. FLUXO DE EXECUÇÃO

### 3.1 Fluxo Completo

```
Motor de Value → Sinal Aprovado
                    |
                    v
              Telegram Bot + Email
                    |
                    v
              Operador recebe notificação
                    |
                    v
              Operador valida odd na Betfair
                    |
                    v
        Odd >= mínima? (Sim → Continuar | Não → Rejeitar)
                    |
                    v
              Operador coloca aposta manualmente
                    |
                    v
              Operador confirma via Telegram (/confirm)
                    |
                    v
              Sistema regista aposta na base de dados
                    |
                    v
              Sistema calcula slippage e métricas
```

### 3.2 Tempo de Execução

**Tempo alvo do sinal à execução:** < 5 minutos

**Breakdown:**
- Recebimento de notificação: < 30 segundos
- Validação de odd: 1-2 minutos
- Execução na Betfair: 1-2 minutos
- Confirmação: < 1 minuto

Se execução excede 5 minutos do sinal, a aposta deve ser rejeitada (odd pode ter mudado significativamente).

---

## 4. FORMATO DO SINAL TELEGRAM

### 4.1 Estrutura do Mensagem

```
🎯 SINAL APROVADO #SIG-20261015-001
🏀 Boston Celtics vs LA Lakers
📊 Mercado: Moneyline | Celtics
💰 Odd: 1.85 (mínima aceitável: 1.83)
📈 Edge: 7.3% | Prob: 58%
💵 Stake: €25.00 (2.5% da banca)
⏰ Expira em: 5 minutos
⚠️ NÃO APOSTAR se odd < 1.83

/confirm SIG-20261015-001 para confirmar execução
```

### 4.2 Componentes do Sinal

**ID Único:** #SIG-YYYYMMDD-XXX permite rastreamento e reconciliação

**Jogo:** Times e data para identificação clara

**Mercado e Seleção:** Mercado específico (Moneyline, Spread, Total) e seleção (time, over/under)

**Odd e Mínima:** Odd no momento do sinal e mínima aceitável (geralmente 2% abaixo da odd do sinal para acomodar slippage)

**Edge e Probabilidade:** Edge estimado e probabilidade implícita para contexto

**Stake:** Stake calculado via Kelly fracionado, com percentagem da banca para contexto

**Expiração:** Tempo máximo para execução (tipicamente 5 minutos)

**Aviso de Restrição:** Lembrete de não apostar se odd caiu abaixo da mínima

**Comando de Confirmação:** Comando para confirmar execução no bot Telegram

### 4.3 Email de Backup

Além do Telegram, enviar email com o mesmo conteúdo para backup. Email deve incluir:
- Assunto: "SINAL APROVADO #SIG-20261015-001"
- Corpo: Mesmo conteúdo do Telegram
- Botão de ação: Link para deep link (se implementado) ou link direto para Betfair

---

## 5. SOP DO OPERADOR

### 5.1 Procedimento Padrão

**Passo 1: Recebimento de Sinal**
- Verificar Telegram imediatamente após notificação
- Se não possível ver imediatamente, verificar email de backup
- Notificar timestamp de recebimento para tracking de latência

**Passo 2: Validação de Odd**
- Abrir Betfair Exchange
- Navegar até o jogo e mercado especificado
- Verificar odd atual da seleção especificada
- Confirmar odd >= mínima aceitável
- Se odd < mínima, rejeitar sinal e notificar sistema

**Passo 3: Colocação de Aposta**
- Selecionar mercado correto (Moneyline, Spread, Total)
- Selecionar seleção correta (time específico, over/under)
- Digitar stake exatamente como especificado
- Verificar que stake está dentro de limites de exposição
- Confirmar aposta

**Passo 4: Confirmação**
- Voltar ao Telegram
- Enviar comando: `/confirm SIG-20261015-001`
- Incluir odd obtida (opcional mas recomendado)
- Incluir screenshot do slip (opcional mas recomendado)

**Passo 5: Registro de Exceções**
- Se não foi possível executar (odd mudou, mercado fechou, etc.), notificar sistema
- Enviar comando: `/reject SIG-20261015-001 <motivo>`
- Motivos comuns: odd abaixo mínima, mercado fechado, erro da Betfair

### 5.2 Regras Absolutas

**Nunca Apostar se:**
- Odd < mínima aceitável
- Jogo já começou
- Mercado está fechado ou suspenso
- Stake excede limites de exposição diária
- Operador não está em estado mental adequado (fadiga, stress)

**Nunca Alterar:**
- Stake especificado no sinal
- Seleção especificada no sinal
- Mercado especificado no sinal

**Nunca Executar:**
- Sem confirmação prévia no Telegram
- Sem validar odd na Betfair
- Se houver dúvida sobre o sinal

### 5.3 Checklist de Validação

Antes de cada aposta, verificar:
- [ ] Sinal ID está correto
- [ ] Jogo e times correspondem ao sinal
- [ ] Mercado está correto
- [ ] Seleção está correta
- [ ] Odd atual >= mínima aceitável
- [ ] Stake corresponde ao sinal
- [ ] Exposição diária dentro de limites
- [ ] Jogo ainda não começou
- [ ] Mercado está aberto e ativo

---

## 6. TRATAMENTO DE EXCEÇÕES

### 6.1 Odd Abaixo da Mínima

**Sintoma:** Odd na Betfair é menor que a mínima aceitável especificada no sinal.

**Ação:** Rejeitar sinal. Não executar aposta.

**Comando:** `/reject SIG-20261015-001 odd_below_minimum`

**Razão:** Odd abaixo da mínima indica que edge foi perdido ou reduzido significativamente. Executar seria sub-ótimo ou negativo.

### 6.2 Mercado Fechado

**Sintoma:** Mercado está fechado ou suspenso na Betfair.

**Ação:** Rejeitar sinal.

**Comando:** `/reject SIG-20261015-001 market_closed`

**Razão:** Mercado fechado indica que jogo começou ou foi cancelado. Não é possível executar.

### 6.3 Erro da Betfair

**Sintoma:** Erro técnico ao tentar colocar aposta (API down, erro de conta, etc.).

**Ação:** Tentar novamente uma vez. Se falhar novamente, rejeitar sinal.

**Comando:** `/reject SIG-20261015-001 betfair_error`

**Razão:** Erros técnicos podem ser temporários, mas se persistem, não deve forçar execução.

### 6.4 Operador Indisponível

**Sintoma:** Operador não pode executar (indisponível, sem acesso à Betfair, etc.).

**Ação:** Notificar sistema de indisponibilidade. Sinal expira automaticamente após 5 minutos.

**Razão:** Execução fora do janela de tempo não é aceitável devido a slippage potencial.

---

## 7. MÉTRICAS E MONITORIZAÇÃO

### 7.1 Métricas de Performance

- **Taxa de Execução:** Percentagem de sinais executados vs rejeitados. Target: > 80%
- **Tempo Médio de Execução:** Tempo do sinal à confirmação. Target: < 5 minutos
- **Slippage Médio:** Diferença entre odd do sinal e odd obtida. Target: < 2%
- **Taxa de Erro Humano:** Percentagem de apostas com erro (seleção errada, stake errada). Target: < 1%

### 7.2 Métricas de Qualidade

- **Validação de Odd:** Percentagem de vezes que odd >= mínima. Target: > 90%
- **Taxa de Confirmação:** Percentagem de apostas confirmadas no Telegram. Target: 100%
- **Rejeições por Motivo:** Distribuição de motivos de rejeição para identificar padrões

---

## 8. TREINAMENTO E ONBOARDING

### 8.1 Treinamento Inicial

Antes de começar execução manual em produção, o operador deve:
- Completar treinamento de interface Betfair
- Completar treinamento de Telegram bot
- Executar 10+ apostas em modo shadow (sem dinheiro real)
- Passar em teste de conhecimento do SOP

### 8.2 Simulação

Criar ambiente de simulação onde:
- Sinais falsos são gerados periodicamente
- Operador pratica fluxo completo sem risco
- Sistema valida tempo e precisão
- Feedback é fornecido sobre performance

### 8.3 Checklist SOP-001

Criar checklist físico ou digital que operador usa para cada aposta:
- Verificar ID do sinal
- Validar odd
- Confirmar seleção
- Verificar stake
- Confirmar execução
- Registrar no Telegram

---

## 9. BACKLOG TÉCNICO

- [ ] Treinar operador com simulação completa
- [ ] Criar checklist SOP-001 físico ou digital
- [ ] Implementar comando /confirm no bot Telegram
- [ ] Implementar comando /reject no bot Telegram
- [ ] Implementar tracking de tempo de execução
- [ ] Implementar cálculo automático de slippage
- [ ] Criar dashboard de métricas de execução
- [ ] Implementar sistema de backup por email
- [ ] Criar sistema de alerta para operador indisponível

---

## 10. LINKS CRUZADOS

- [[09_Execution_System/INDEX]] ← Secção mãe
- [[09_Execution_System/SLIPPAGE_TRACKING]] → Tracking de slippage
- [[19_Telegram_System/INDEX]] → Bot Telegram
- [[08_Risk_Management/EXPOSURE_LIMITS]] → Limites de exposição
