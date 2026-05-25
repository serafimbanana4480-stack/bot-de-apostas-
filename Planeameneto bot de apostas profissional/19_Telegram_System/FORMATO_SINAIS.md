---
ID: TEL-002
tags: #status/active #telegram #signals #format #messaging
---

# Formato dos Sinais Telegram

## Objetivo
Especificar de forma rigorosa e exaustiva o formato, conteúdo, estrutura visual e regras de apresentação de cada mensagem de sinal enviada via Telegram aos subscritores do sistema de value betting NBA. O formato deve maximizar a clareza, minimizar a ambiguidade, garantir a inclusão obrigatória de disclaimers e metadados, e permitir a extração automática de dados para tracking e análise de performance.

## O que faz
- Define templates para 6 tipos de mensagem: (1) Sinal Novo, (2) Atualização de Sinal (odds mudaram), (3) Confirmação de Aposta (real money), (4) Resultado do Sinal (win/loss/push), (5) Resumo Diário, (6) Alerta de Sistema.
- Especifica o uso de Markdown e emojis para hierarquia visual, limitações de tamanho (4096 caracteres), e divisão em múltiplas mensagens se necessário.
- Inclui metadados estruturados em cada sinal: ID único do sinal, timestamp de geração, modelo utilizado, confiança, edge calculado, e link para dashboard.
- Garante que o subscritor consiga copiar/colar o sinal para um bookmaker sem erros de interpretação.

## Porque existe
- **Ambiguidade Custa Dinheiro**: Um sinal que diga "Warriors -3" sem especificar se é spread, moneyline, ou total, e sem indicar a odd exata, pode levar o subscritor a apostar errado ou em odds inferiores.
- **Tracking e Accountability**: Sem um ID único e formato estruturado, é impossível rastrear qual sinal corresponde a qual aposta no bookmaker, dificultando a reconciliação de P&L.
- **Compliance**: O sinal é um ponto de contacto regulatório. Deve incluir disclaimer de risco, indicar que é informação e não aconselhamento, e respeitar regras de publicidade.
- **Automação**: Subscritores institucionais (API) ou scripts pessoais podem fazer parse automático de sinais se o formato for estruturado e previsível.

## Implementação / Pseudocódigo
```python
class FormatoSinais:
    def __init__(self):
        self.templates = {
            "SINAL_NOVO": self.carregar_template("sinal_novo_v2.md"),
            "SINAL_ATUALIZACAO": self.carregar_template("sinal_atualizacao_v1.md"),
            "CONFIRMACAO_APOSTA": self.carregar_template("confirmacao_aposta_v1.md"),
            "RESULTADO_SINAL": self.carregar_template("resultado_sinal_v2.md"),
            "RESUMO_DIARIO": self.carregar_template("resumo_diario_v1.md"),
            "ALERTA_SISTEMA": self.carregar_template("alerta_sistema_v1.md")
        }
        self.emojis = {
            "NBA": "🏀",
            "SPREAD": "📊",
            "TOTAL": "🔢",
            "MONEYLINE": "💵",
            "PLAYER_PROP": "🏃",
            "EDGE_ALTO": "🟢",
            "EDGE_MEDIO": "🟡",
            "EDGE_BAIXO": "🟠",
            "WIN": "✅",
            "LOSS": "❌",
            "PUSH": "➖",
            "RELOGIO": "⏰",
            "GRAFICO": "📈",
            "ALERTA": "⚠️",
            "INFO": "ℹ️"
        }

    def gerar_sinal_novo(self, sinal):
        edge = sinal["edge_percentual"]
        cor_edge = self.emojis["EDGE_ALTO"] if edge > 5 else self.emojis["EDGE_MEDIO"] if edge > 2.5 else self.emojis["EDGE_BAIXO"]
        
        mensagem = f"""
{self.emojis['NBA']} **NOVO SINAL NBA** — #{sinal['id']}

📅 **Jogo**: {sinal['equipa_casa']} vs {sinal['equipa_fora']}
{self.emojis['RELOGIO']} **Início**: {sinal['horario_jogo']} ET

📌 **Mercado**: {sinal['mercado']}
🎯 **Pick**: {sinal['pick_descricao']}
💰 **Odd Recomendada**: {sinal['odd_recomendada']} ({sinal['bookmaker_recomendado']})
📊 **Edge Estimado**: {cor_edge} {edge:.2f}%
🧠 **Confiança do Modelo**: {sinal['confianca']:.0%}
📈 **CLV Esperado**: +{sinal['clv_esperado']:.2f}%

🏦 **Stake Sugerida**: {sinal['stake_sugerida']} unidades
💡 **Unidade Recomendada**: €{sinal['valor_unidade_eur']} (ajuste à sua banca)

🔗 **Dashboard**: [Ver análise completa]({sinal['url_dashboard']})

{self.emojis['INFO']} {self.renderizar_disclaimer()}
"""
        
        # Validação de tamanho
        if len(mensagem) > 4000:
            mensagem = self.dividir_mensagem(mensagem)
        
        return {"mensagem": mensagem, "hash": hashlib.sha256(mensagem.encode()).hexdigest(), "metadata": self.extrair_metadata(sinal)}

    def gerar_resultado_sinal(self, sinal, resultado):
        emoji_resultado = self.emojis["WIN"] if resultado == "WIN" else self.emojis["LOSS"] if resultado == "LOSS" else self.emojis["PUSH"]
        pnl = sinal["stake_real"] * (sinal["odd_fechada"] - 1) if resultado == "WIN" else -sinal["stake_real"] if resultado == "LOSS" else 0
        
        return f"""
{emoji_resultado} **RESULTADO** — #{sinal['id']}

🏀 {sinal['equipa_casa']} vs {sinal['equipa_fora']}
📌 {sinal['pick_descricao']} @ {sinal['odd_fechada']}

**Resultado**: {resultado}
💰 **P&L**: {'+' if pnl > 0 else ''}{pnl:.2f} unidades

📊 **Performance Hoje**: {self.calcular_performance_dia(sinal['data_jogo'])}
📈 **Performance Mês**: {self.calcular_performance_mes()}

{self.emojis['INFO']} {self.renderizar_disclaimer()}
"""

    def gerar_resumo_diario(self, data):
        apostas = self.db.obter_apostas_dia(data)
        total = len(apostas)
        wins = sum(1 for a in apostas if a["resultado"] == "WIN")
        losses = sum(1 for a in apostas if a["resultado"] == "LOSS")
        pushes = sum(1 for a in apostas if a["resultado"] == "PUSH")
        pnl = sum(a["pnl"] for a in apostas)
        
        return f"""
{self.emojis['GRAFICO']} **RESUMO DIÁRIO** — {data}

🏀 **Total de Sinais**: {total}
✅ **Wins**: {wins}
❌ **Losses**: {losses}
➖ **Pushes**: {pushes}

💰 **P&L Dia**: {'+' if pnl > 0 else ''}{pnl:.2f} unidades
📊 **Yield**: {(pnl / sum(a['stake'] for a in apostas) * 100):.2f}%

📈 **CLV Médio**: {self.calcular_clv_medio(apostas):.2f}%

{self.emojis['INFO']} {self.renderizar_disclaimer()}
"""

    def extrair_metadata(self, sinal):
        return {
            "sinal_id": sinal["id"],
            "timestamp_geracao": datetime.utcnow().isoformat(),
            "modelo_version": sinal["modelo_version"],
            "mercado": sinal["mercado"],
            "edge": sinal["edge_percentual"],
            "odd_recomendada": sinal["odd_recomendada"],
            "bookmaker": sinal["bookmaker_recomendado"],
            "hash_mensagem": None  # preenchido após renderização
        }

    def renderizar_disclaimer(self):
        return "Este sinal é informação pura baseada em modelos quantitativos. Não constitui aconselhamento financeiro nem garantia de lucro. As apostas envolvem risco. Jogue responsavelmente."
```

## Thresholds e Tabelas

| Elemento do Sinal | Obrigatório | Formato | Exemplo | Validação |
|-------------------|-------------|---------|---------|-----------|
| ID do Sinal | Sim | `#SIG-YYYYMMDD-NNNN` | `#SIG-20240115-0042` | Único, sequencial por dia |
| Data/Hora Jogo | Sim | `YYYY-MM-DD HH:MM ET` | `2024-01-15 19:30 ET` | Deve ser futuro relativamente ao envio |
| Mercado | Sim | Texto padronizado | `Spread`, `Total`, `Moneyline`, `Player Prop` | Lista fechada |
| Pick | Sim | Texto claro | `Warriors -3.5` ou `Over 225.5` | Não ambíguo |
| Odd Recomendada | Sim | Decimal ≥ 1.01 | `1.95` | Capturada no momento do envio |
| Bookmaker | Sim | Nome padronizado | `Bet365`, `Pinnacle`, `Betano` | Lista fechada |
| Edge Estimado | Sim | Percentagem com 2 casas | `3.42%` | Calculado por modelo |
| Confiança do Modelo | Sim | Percentagem inteira | `78%` | Intervalo [50%, 100%] |
| CLV Esperado | Sim | Percentagem com 2 casas | `+2.15%` | >= 0 para sinais válidos |
| Stake Sugerida | Sim | Número de unidades | `1.5` | Intervalo [0.5, 5.0] |
| Disclaimer | Sim | Texto legal padronizado | (ver acima) | Sempre presente, nunca omitido |
| Link Dashboard | Recomendado | URL | `https://...` | HTTPS, funcional |

| Tipo de Mensagem | Frequência | Tamanho Máximo | Emojis Principais | Parseável por API |
|----------------|------------|---------------|-------------------|-------------------|
| Sinal Novo | Por oportunidade | 4096 chars | 🏀 📊 🎯 💰 | Sim |
| Atualização | Quando odd muda > 5% | 4096 chars | 🔄 📊 | Sim |
| Confirmação | Se execução real money | 4096 chars | ✅ 📌 | Sim |
| Resultado | Após jogo final | 4096 chars | ✅ ❌ ➖ | Sim |
| Resumo Diário | Após último jogo | 4096 chars | 📈 📊 | Sim |
| Alerta Sistema | Event-driven | 4096 chars | ⚠️ 🚨 | Sim |

## Riscos
- **Risco de Formato Quebrado**: Emojis ou Markdown mal escapados podem fazer com que a mensagem apareça mal formatada no Telegram do subscritor, reduzindo a credibilidade profissional.
- **Risco de Informação Insuficiente**: Um sinal sem edge ou sem confiança do modelo é apenas "opinião"; o valor quantitativo do serviço desaparece.
- **Risco de Spam**: Enviar atualizações excessivas (ex: odd mudou 0.01) inunda o subscritor e provoca unsubscribes.
- **Risco de Dependência de Parsing**: Se subscritores institucionais parseiam as mensagens automaticamente, qualquer alteração no formato quebra os seus sistemas. Mudanças de formato requerem versão e aviso prévio.

## Checklist de Formato de Sinais
- [ ] Template de cada tipo de mensagem validado por designer de UX (legibilidade) e advogado (disclaimer).
- [ ] Todos os sinais incluem ID único, timestamp, e hash da mensagem para audit trail.
- [ ] Teste visual em Telegram mobile (iOS e Android) e desktop antes de qualquer alteração de template.
- [ ] Sistema de "preview" para staff: antes de enviar a subscritores, o sinal é previewed no canal de teste.
- [ ] Versão do template documentada; alterações materiais (que afetam parsing) comunicadas com 7 dias de antecedência.
- [ ] Edge e confiança calculados em tempo real; se edge < 1.5%, o sinal é suprimido automaticamente (não enviado).
- [ ] Odd recomendada capturada no momento exato do envio; se a odd mudar > 5% em 60 segundos, envia atualização ou cancela.
- [ ] Resumo diário enviado mesmo em dias sem sinais ("Hoje não houve oportunidades com edge suficiente").

## Links Cruzados
- [[19_Telegram_System/BOT_TELEGRAM_CONFIG]] - Configuração do bot que envia os sinais.
- [[19_Telegram_System/COMANDOS_BOT]] - Comandos que o subscritor pode usar para obter informação adicional.
- [[16_Compliance/DISCLAIMERS]] - Disclaimer legal que deve constar em todos os sinais.
- [[21_Paper_Trading/PROTOCOLO_PAPER]] - Como os sinais são validados antes de envio a real money.
- [[22_Real_Money_Operations/TRACKING_APOSTAS]] - Tracking das apostas correspondentes aos sinais.
