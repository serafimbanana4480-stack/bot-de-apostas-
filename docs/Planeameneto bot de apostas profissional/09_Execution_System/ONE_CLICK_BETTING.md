# ONE_CLICK_BETTING — Fase 2

**ID:** `EX-002` | **Fase:** #phase/6 | **Owner:** Operations Lead + Dev | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar um sistema de one-click betting que permite aos operadores executar apostas rapidamente através de deep links que abrem a aplicação Betfair com o slip (boletim de aposta) já preenchido. O objetivo é reduzir drasticamente o tempo entre o sinal e a execução, minimizando slippage e garantindo que o edge do sinal não seja perdido durante o processo de execução manual. Este é um passo intermediário entre execução completamente manual (copy-paste de odds) e execução completamente automática (API).

---

## 2. CONCEITO E MOTIVAÇÃO

### 2.1 O Problema da Execução Manual

Na execução manual tradicional, o operador precisa:
1. Receber o sinal via Telegram
2. Abrir a aplicação Betfair
3. Navegar até o mercado correto
4. Encontrar a seleção correta
5. Digitar a odd manualmente
6. Digitar o stake manualmente
7. Confirmar a aposta

Este processo leva tipicamente 30-60 segundos, durante os quais a odd pode mudar significativamente, causando slippage ou até tornar a aposta não-executável.

### 2.2 A Solução: Deep Links

Deep links permitem saltar diretamente para o mercado com o slip já preenchido. O operador só precisa:
1. Clicar no link
2. Verificar que o slip está correto
3. Confirmar com um toque

Isto reduz o tempo de execução para 5-10 segundos, drasticamente reduzindo slippage.

### 2.3 Por Que Não Execução Automática?

Execução automática via API é o ideal, mas tem desafios:
- Requer integração complexa com APIs de casas de apostas
- Risco de erros de execução em escala
- Questões regulatórias em algumas jurisdições
- Necessidade de monitorização contínua de erros de API

One-click betting é um compromisso pragmático: reduz significativamente slippage sem a complexidade e risco de execução automática completa.

---

## 3. DEEP LINK BETFAIR

### 3.1 Estrutura do URL

O URL de deep link da Betfair segue este formato:

```
https://www.betfair.com/exchange/plus/{market_id}/
  ?price={odd}
  &size={stake}
  &selection={selection_id}
  &betType=B
  &persist=0
```

**Parâmetros:**
- **market_id:** Identificador único do mercado na Betfair
- **price:** Odd desejada para a aposta
- **size:** Stake (valor monetário) da aposta
- **selection_id:** Identificador da seleção dentro do mercado (ex: time específico)
- **betType:** Tipo de aposta (B = Back, L = Lay)
- **persist=0:** Não manter a aposta aberta se não for executada imediatamente

### 3.2 Mapeamento de Identificadores

Para gerar deep links, o sistema precisa mapear jogos e seleções para IDs da Betfair:

**Mapeamento de Mercado:**
- Jogo "Celtics vs Lakers" → market_id = "12345678"
- Cada tipo de mercado (Moneyline, Spread, Total) tem market_id diferente

**Mapeamento de Seleção:**
- Seleção "Celtics" → selection_id = "87654321"
- Seleção "Lakers" → selection_id = "98765432"
- Seleção "Over 215.5" → selection_id = "11223344"

Este mapeamento deve ser mantido atualizado à medida que novos jogos são adicionados.

### 3.3 Exemplo Prático

Sinal recebido:
- Jogo: Celtics vs Lakers
- Mercado: Moneyline
- Seleção: Celtics
- Odd: 1.85
- Stake: €25

URL gerado:
```
https://www.betfair.com/exchange/plus/12345678/
  ?price=1.85
  &size=25
  &selection=87654321
  &betType=B
  &persist=0
```

Quando o operador clica neste link, abre a app Betfair diretamente no mercado Celtics vs Lakers com Celtics a 1.85 por €25 já preenchido.

---

## 4. IMPLEMENTAÇÃO

### 4.1 Geração de Deep Links

```python
def generate_deep_link(signal):
    """
    Gera deep link para Betfair Exchange.
    
    Args:
        signal: Objeto contendo game_info, market, selection, odd, stake
    
    Returns:
        URL de deep link completo
    
    Requires:
        - Mapeamento de game para market_id
        - Mapeamento de seleção para selection_id
    """
    # Obter market_id do jogo e mercado
    market_id = get_betfair_market_id(
        signal.game_id, 
        signal.market_type
    )
    
    # Obter selection_id da seleção
    selection_id = get_betfair_selection_id(
        signal.game_id,
        signal.market_type,
        signal.selection
    )
    
    # Construir URL base
    base = "https://www.betfair.com/exchange/plus/"
    
    # Construir parâmetros
    params = {
        "price": signal.odd,
        "size": signal.stake,
        "selectionId": selection_id,
        "betType": "B",  # Back
        "persist": "0"
    }
    
    # Construir query string
    query = "&".join([f"{k}={v}" for k, v in params.items()])
    
    return f"{base}{market_id}/?{query}"
```

### 4.2 Mapeamento de IDs

O mapeamento de IDs pode ser implementado de várias formas:

**Opção 1: Lookup Manual**
- Manter tabela manual de mapeamentos
- Atualizado manualmente quando novos jogos são adicionados
- Simples mas trabalhoso

**Opção 2: API da Betfair**
- Usar API da Betfair para buscar market_ids e selection_ids dinamicamente
- Mais automático mas requer integração API adicional
- Pode ter latência

**Opção 3: Web Scraping**
- Scraping da página de mercado da Betfair para extrair IDs
- Frágil a mudanças de UI da Betfair
- Não recomendado para produção

**Recomendação:** Começar com lookup manual para MVP, migrar para API para produção.

### 4.3 Web App Simples

Uma aplicação web simples lista sinais ativos com botões "Abrir Betfair":

```html
<!DOCTYPE html>
<html>
<head>
    <title>Sinais Ativos</title>
    <style>
        .signal-card {
            border: 1px solid #ddd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .btn {
            background: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <h1>Sinais Ativos</h1>
    
    <div class="signal-card">
        <h3>Celtics vs Lakers</h3>
        <p><strong>Mercado:</strong> Moneyline</p>
        <p><strong>Seleção:</strong> Celtics</p>
        <p><strong>Odd:</strong> 1.85</p>
        <p><strong>Stake:</strong> €25</p>
        <p><strong>Edge:</strong> 3.2%</p>
        <p><strong>CLV:</strong> 1.5%</p>
        <a href="https://betfair.com/exchange/plus/12345678/?price=1.85&size=25&selection=87654321&betType=B&persist=0" 
           target="_blank" 
           class="btn">
            Abrir na Betfair
        </a>
    </div>
    
    <!-- Mais sinais aqui -->
    
</body>
</html>
```

### 4.4 Integração com Telegram

O bot Telegram pode enviar deep links diretamente:

```python
async def send_signal_with_link(signal):
    deep_link = generate_deep_link(signal)
    
    message = f"""
🏀 {signal.game}
📊 Mercado: {signal.market}
🎯 Seleção: {signal.selection}
💰 Odd: {signal.odd}
💵 Stake: {signal.stake}€
📈 Edge: {signal.edge}%
📊 CLV: {signal.clv}%

[ABRIR NA BETFAIR]({deep_link})
    """
    
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=message,
        parse_mode='Markdown'
    )
```

---

## 5. FLUXO DE OPERAÇÃO

### 5.1 Fluxo do Operador

1. Sistema gera sinal
2. Sistema calcula stake baseado em Kelly
3. Sistema gera deep link
4. Sistema envia sinal + deep link via Telegram
5. Operador recebe notificação
6. Operador clica no link
7. App Betfair abre com slip preenchido
8. Operador verifica rapidamente (odd, stake, seleção)
9. Operador clica "Place Bet"
10. Sistema registra execução

**Tempo total:** 5-10 segundos do sinal à execução

### 5.2 Fluxo Técnico

```
Sinal Gerado → Calcular Stake → Buscar Market/Selection IDs → Gerar Deep Link → Enviar Telegram → Operador Clica → Betfair Abre → Execução → Registro
```

---

## 6. VALIDAÇÃO E VERIFICAÇÃO

### 6.1 Validação Pré-Execução

Antes de enviar o deep link, o sistema deve validar:
- Market_id existe e é válido
- Selection_id existe e é válido
- Odd está dentro de range razoável (não obviamente errado)
- Stake está dentro de limites de exposição
- Jogo ainda não começou (se aplicável)

### 6.2 Verificação Pós-Execução

Após o operador clicar no link, o sistema deve:
- Registrar que o link foi clicado (se possível via tracking)
- Verificar se a aposta foi executada (via scraping ou API)
- Calcular slippage real (odd obtida vs odd esperada)
- Registrar resultado em audit log

---

## 7. RISCOS E MITIGAÇÃO

### 7.1 Risco: IDs Incorretos

**Problema:** Mapeamento de market_id ou selection_id incorreto leva ao mercado errado.

**Mitigação:**
- Validação rigorosa de mapeamentos
- Testes manuais de deep links antes de enviar
- Sistema de feedback onde operadores reportam erros
- Atualização regular de mapeamentos

### 7.2 Risco: Odds Mudam Entre Link e Execução

**Problema:** Mesmo com one-click, há delay entre geração do link e execução.

**Mitigação:**
- Links com validade curta (ex: expiram após 30 segundos)
- Alerta se odd mudou significativamente (ex: > 2%)
- Opção de regenerar link com odd atualizada

### 7.3 Risco: Erro Humano

**Problema:** Operador clica sem verificar, ou confirma aposta errada.

**Mitigação:**
- Interface clara mostrando todos os detalhes
- Exigir confirmação explícita
- Treinamento de operadores
- Sistema de revisão de apostas

### 7.4 Risco: Betfair Muda Formato de URL

**Problema:** Betfair pode mudar o formato de deep links, quebrando o sistema.

**Mitigação:**
- Monitorização de mudanças na Betfair
- Sistema de fallback para execução manual tradicional
- Testes regulares de deep links

---

## 8. MÉTRICAS DE SUCESSO

### 8.1 Métricas Operacionais

- **Tempo Médio de Execução:** Tempo do sinal à execução. Target: < 10 segundos
- **Taxa de Clique de Links:** Percentagem de links clicados
- **Taxa de Execução:** Percentagem de cliques que resultam em aposta executada
- **Slippage Médio:** Slippage médio com one-click vs manual. Target: redução de 50%+

### 8.2 Métricas de Qualidade

- **Taxa de Erros de ID:** Percentagem de links com IDs incorretos
- **Taxa de Rejeição:** Percentagem de apostas rejeitadas pela Betfair
- **Satisfação do Operador:** Feedback qualitativo dos operadores

---

## 9. BACKLOG TÉCNICO

- [ ] Mapear market_ids e selection_ids NBA para Betfair
- [ ] Criar web app simples (FastAPI + HTML) para dashboard de sinais
- [ ] Implementar geração de deep links no sistema de sinais
- [ ] Integrar deep links no bot Telegram
- [ ] Testar deep links em mobile (iOS + Android)
- [ ] Testar deep links em desktop
- [ ] Implementar tracking de cliques e execuções
- [ ] Criar sistema de feedback para reportar erros de IDs
- [ ] Documentar processo de atualização de mapeamentos

---

## 10. LINKS CRUZADOS

- [[09_Execution_System/INDEX]] ← Secão mãe
- [[09_Execution_System/EXECUCAO_AUTOMATICA]] → Fase 3 (execução automática)
- [[09_Execution_System/SLIPPAGE_TRACKING]] → Tracking de slippage
- [[08_Risk_Management/EXPOSURE_LIMITS]] → Limites de exposição
