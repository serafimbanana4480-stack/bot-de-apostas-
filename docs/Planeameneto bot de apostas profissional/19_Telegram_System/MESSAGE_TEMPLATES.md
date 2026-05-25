---
ID: TEL-008
tags: #status/active #telegram #templates #messages #personalization
---

# Templates de Mensagens

## Objetivo
Documentar todos os templates de mensagens utilizados pelo bot Telegram, incluindo placeholders de personalização, variantes por idioma, formatação Markdown, e regras de renderização. Os templates devem ser consistentes, profissional, e adaptáveis a diferentes contextos (onboarding, sinais, alertas, suporte).

## O que faz
- Define templates para 15 categorias de mensagens: boas-vindas, onboarding, sinais, resultados, resumos, alertas, erros, confirmações, lembretes, marketing, suporte, compliance, manutenção, cancelamento, e notificações administrativas.
- Especifica sistema de placeholders: `{nome}`, `{plano}`, `{data}`, `{valor}`, etc., com validação de tipos.
- Implementa personalização baseada em preferências do utilizador: idioma, timezone, formato de moeda, e nível de detalhe.
- Define variantes de templates para diferentes canais (DM vs. grupo) e diferentes planos (Essencial vs. Pro).

## Porque existe
- **Consistência**: Templates padronizados garantem que todas as mensagens sigam o mesmo tom, formato, e nível de detalhe, reforçando a marca.
- **Eficiência**: Em vez de escrever mensagens ad-hoc em cada ponto do código, os templates permitem reutilização e manutenção centralizada.
- **Personalização**: Placeholders permitem que cada mensagem seja adaptada ao utilizador individual, melhorando a experiência.
- **Multilinguismo**: A estrutura de templates facilita a adição de novos idiomas sem alterar o código.

---

## Sistema de Placeholders

### Placeholders Disponíveis

| Placeholder | Tipo | Descrição | Exemplo |
|-------------|------|-----------|---------|
| `{nome}` | String | Primeiro nome do utilizador | João |
| `{nome_completo}` | String | Nome completo | João Silva |
| `{plano}` | String | Plano de subscrição | PRO |
| `{data_inicio}` | Date | Data de início da subscrição | 2024-01-15 |
| `{data_fim}` | Date | Data de fim da subscrição | 2024-02-15 |
| `{dias_restantes}` | Integer | Dias até ao fim da subscrição | 12 |
| `{valor_mensal}` | Currency | Valor mensal em EUR | €29.00 |
| `{email}` | String | Email do utilizador | joao@email.com |
| `{sinal_id}` | String | ID do sinal | #SIG-20240115-0042 |
| `{mercado}` | String | Tipo de mercado | Spread |
| `{odd}` | Decimal | Odd da aposta | 1.95 |
| `{stake}` | Decimal | Stake sugerida | 1.5 |
| `{edge}` | Percentagem | Edge estimado | 3.42% |
| `{timestamp}` | DateTime | Timestamp atual | 2024-01-15 14:30 |
| `{timezone}` | String | Timezone do utilizador | Europe/Lisbon |

### Validação de Placeholders
```python
class TemplateValidator:
    """
    Valida que todos os placeholders requeridos estão presentes.
    """
    REQUIRED_PLACEHOLDERS = {
        "WELCOME": ["nome"],
        "SIGNAL_NEW": ["sinal_id", "mercado", "odd", "stake", "edge"],
        "SUBSCRIPTION_EXPIRED": ["nome", "data_fim"],
        "PAYMENT_CONFIRMATION": ["nome", "valor_mensal", "plano"]
    }

    def validate(self, template_name, context):
        required = self.REQUIRED_PLACEHOLDERS.get(template_name, [])
        missing = [p for p in required if p not in context]

        if missing:
            raise TemplateError(f"Missing placeholders: {missing}")

        return True
```

---

## Templates por Categoria

### 1. Boas-Vindas (Welcome)

#### Template: WELCOME_NEW
```markdown
👋 **Bem-vindo, {nome}!**

Obrigado por juntares-te ao NBA Value Signals!

Sou o teu assistente de value betting NBA. Aqui vais receber sinais de alta qualidade baseados em modelos quantitativos rigorosos.

📊 **O que vais receber:**
• Sinais em tempo real
• Análises detalhadas
• Estatísticas de performance
• Suporte dedicado

🚀 **Próximos passos:**
1. Escolhe o teu plano
2. Configura as tuas preferências
3. Começa a apostar com edge!

Se precisares de ajuda, usa o comando /help a qualquer momento.

{disclaimer}
```

#### Template: WELCOME_BACK
```markdown
👋 **Bem-vindo de volta, {nome}!**

Bom ver-te aqui! A tua subscrição {plano} está ativa até {data_fim}.

📊 **Resumo da tua conta:**
• Plano: {plano}
• Dias restantes: {dias_restantes}
• Estatísticas disponíveis: /stats

Tens algum sinal pendente? Vamos lá! 🏀

{disclaimer}
```

---

### 2. Onboarding

#### Template: ONBOARDING_PLAN_SELECTION
```markdown
📋 **Escolhe o teu plano**

Para começares a receber sinais, seleciona o plano que melhor se adapta a ti:

🔹 **ESSENCIAL** — 29€/mês
   ✓ Sinais de spread e total
   ✓ 5-10 sinais por dia
   ✓ Estatísticas pessoais
   ✓ Suporte por email

🔹 **PRO** — 79€/mês
   ✓ Tudo do Essencial
   ✓ Sinais de player props
   ✓ 10-15 sinais por dia
   ✓ Acesso a API
   ✓ Suporte prioritário

🔹 **INSTITUCIONAL** — 299€/mês
   ✓ Tudo do Pro
   ✓ Sinais em tempo real
   ✓ API completa
   ✓ Consultoria personalizada
   ✓ SLA garantido

Clica no botão abaixo para escolher o teu plano:
```

#### Template: ONBOARDING_PREFERENCES
```markdown
⚙️ **Configura as tuas preferências**

Para personalizarmos a tua experiência, define as seguintes opções:

💰 **Unidade de stake:**
Quanto vale 1 unidade para ti em euros?
Exemplo: se a tua banca é 1000€, 1 unidade = 10€ (1%)

📊 **Mercados preferidos:**
Quais tipos de apostas preferes?
• Spread
• Total (Over/Under)
• Moneyline
• Player Props

🔔 **Notificações:**
Queres receber notificações de:
• Sinais novos
• Resultados
• Atualizações de sistema

Usa os comandos abaixo para configurar:
/unidade 10
/alertas sinais on
/alertas resultados on
```

---

### 3. Sinais

#### Template: SIGNAL_NEW (Detalhado)
```markdown
🏀 **NOVO SINAL** — #{sinal_id}

📅 **Jogo:** {equipa_casa} vs {equipa_fora}
⏰ **Início:** {horario_jogo} ET

📌 **Mercado:** {mercado}
🎯 **Pick:** {pick_descricao}
💰 **Odd Recomendada:** {odd_recomendada} ({bookmaker})
📊 **Edge Estimado:** {edge_emoji} {edge_percentual}%
🧠 **Confiança do Modelo:** {confianca}%
📈 **CLV Esperado:** +{clv_esperado}%

🏦 **Stake Sugerida:** {stake_sugerida} unidades
💡 **Unidade Recomendada:** €{valor_unidade_eur}

🔗 **Dashboard:** [Ver análise completa]({url_dashboard})

{disclaimer}
```

#### Template: SIGNAL_UPDATE
```markdown
🔄 **ATUALIZAÇÃO DE SINAL** — #{sinal_id}

⚠️ A odd mudou significativamente:

📌 **Pick:** {pick_descricao}
❌ **Odd Anterior:** {odd_anterior}
✅ **Nova Odd:** {odd_nova} ({bookmaker})
📊 **Novo Edge:** {edge_novo}%

🏦 **Ação Recomendada:**
{acao_recomendada}

{disclaimer}
```

---

### 4. Resultados

#### Template: RESULT_WIN
```markdown
✅ **WIN** — #{sinal_id}

🏀 {equipa_casa} vs {equipa_fora}
📌 {pick_descricao} @ {odd_fechada}

💰 **P&L:** +{pnl:.2f} unidades
📊 **Yield:** {yield:.2f}%

📈 **Performance Hoje:**
• Sinais: {total_hoje}
• Wins: {wins_hoje}
• Losses: {losses_hoje}
• P&L: {pnl_hoje:.2f} unidades

{disclaimer}
```

#### Template: RESULT_LOSS
```markdown
❌ **LOSS** — #{sinal_id}

🏀 {equipa_casa} vs {equipa_fora}
📌 {pick_descricao} @ {odd_fechada}

💰 **P&L:** -{pnl:.2f} unidades
📊 **Yield:** {yield:.2f}%

📈 **Performance Hoje:**
• Sinais: {total_hoje}
• Wins: {wins_hoje}
• Losses: {losses_hoje}
• P&L: {pnl_hoje:.2f} unidades

💡 **Nota:** Value betting é um jogo de longo prazo. Um resultado não define a estratégia.

{disclaimer}
```

#### Template: RESULT_PUSH
```markdown
➖ **PUSH** — #{sinal_id}

🏀 {equipa_casa} vs {equipa_fora}
📌 {pick_descricao} @ {odd_fechada}

💰 **P&L:** 0.00 unidades (stake devolvido)

{disclaimer}
```

---

### 5. Resumos

#### Template: DAILY_SUMMARY
```markdown
📊 **RESUMO DIÁRIO** — {data}

🏀 **Total de Sinais:** {total_sinais}
✅ **Wins:** {wins} ({win_rate:.1%})
❌ **Losses:** {losses} ({loss_rate:.1%})
➖ **Pushes:** {pushes} ({push_rate:.1%})

💰 **P&L Dia:** {pnl_emoji} {pnl:.2f} unidades
📊 **Yield:** {yield:.2f}%
📈 **CLV Médio:** +{clv_medio:.2f}%

💡 **Melhor Sinal:** {melhor_sinal}
⚠️ **Pior Sinal:** {pior_sinal}

{disclaimer}
```

#### Template: WEEKLY_SUMMARY
```markdown
📈 **RESUMO SEMANAL** — Semana {semana}

🏀 **Estatísticas da Semana:**
• Sinais: {total_sinais}
• Win Rate: {win_rate:.1%}
• P&L: {pnl_emoji} {pnl:.2f} unidades
• Yield: {yield:.2f}%

📊 **Comparação com Semana Anterior:**
• P&L: {pnl_diff_emoji} {pnl_diff:.2f} unidades
• Win Rate: {wr_diff_emoji} {wr_diff:.1%}

🎯 **Top Mercados:**
1. {mercado_1}: {count_1} sinais
2. {mercado_2}: {count_2} sinais
3. {mercado_3}: {count_3} sinais

{disclaimer}
```

---

### 6. Alertas

#### Template: ALERT_HIGH_EDGE
```markdown
🚨 **ALERTA DE EDGE ALTO** — #{sinal_id}

⚠️ Detetado edge excepcionalmente alto!

📌 **Pick:** {pick_descricao}
📊 **Edge:** {edge}% (normal: 2-5%)
💰 **Odd:** {odd}

⏰ **Janela de oportunidade:** {janela_minutos} minutos

🏦 **Ação Recomendada:** Aumentar stake para {stake_recomendado} unidades

{disclaimer}
```

#### Template: ALERT_ODD_DROP
```markdown
⚠️ **QUEDA DE ODD** — #{sinal_id}

📌 **Pick:** {pick_descricao}
❌ **Odd Anterior:** {odd_anterior}
✅ **Nova Odd:** {odd_nova}
📉 **Queda:** {queda_percentual}%

🏦 **Ação Recomendada:**
{acao_recomendada}

{disclaimer}
```

---

### 7. Erros

#### Template: ERROR_SUBSCRIPTION_EXPIRED
```markdown
❌ **Subscrição Expirada**

Olá, {nome}!

A tua subscrição {plano} expirou a {data_fim}.

Para continuares a receber sinais, renova a tua subscrição:
/billing

Se já renovaste, aguarda alguns minutos para que o sistema processe o pagamento.

{disclaimer}
```

#### Template: ERROR_RATE_LIMIT
```markdown
⚠️ **Muitas Solicitações**

Estás a enviar demasiadas mensagens num curto período de tempo.

Por favor, aguarda alguns minutos antes de tentar novamente.

Se precisas de ajuda urgente, contacta o suporte:
/suporte
```

#### Template: ERROR_COMMAND_NOT_RECOGNIZED
```markdown
❓ **Comando Não Reconhecido**

O comando que enviaste não é válido.

Use /help para ver a lista de comandos disponíveis.
```

---

### 8. Confirmações

#### Template: CONFIRMATION_SUBSCRIPTION
```markdown
✅ **Subscrição Ativada com Sucesso!**

Parabéns, {nome}! 🎉

A tua subscrição {plano} está agora ativa.

📅 **Período:** {data_inicio} a {data_fim}
💰 **Valor:** {valor_mensal}/mês
🔄 **Renovação Automática:** {auto_renew}

🚀 **Já podes começar a receber sinais!**

Configura as tuas preferências:
/unidade 10
/alertas sinais on

{disclaimer}
```

#### Template: CONFIRMATION_PREFERENCES
```markdown
✅ **Preferências Atualizadas**

As tuas preferências foram guardadas com sucesso:

💰 **Unidade de stake:** €{valor_unidade}
📊 **Mercados:** {mercados}
🔔 **Notificações:** {notificacoes}

{disclaimer}
```

---

### 9. Lembretes

#### Template: REMINDER_SUBSCRIPTION_EXPIRING
```markdown
⏰ **Lembrete: Subscrição a Expirar**

Olá, {nome}!

A tua subscrição {plano} expira em {dias_restantes} dias ({data_fim}).

Para não perderes o acesso aos sinais, renova agora:
/billing

Se já renovaste, disregard this message.

{disclaimer}
```

#### Template: REMINDER_UNCONFIGURED
```markdown
⚙️ **Configuração Pendente**

Olá, {nome}!

Ainda não configuraste as tuas preferências. Para personalizarmos a tua experiência:

/unidade 10  ← Define o valor da tua unidade
/alertas sinais on  ← Ativa notificações de sinais

Configura agora para receberes sinais personalizados!
```

---

### 10. Marketing

#### Template: MARKETING_PROMO
```markdown
🎁 **Oferta Especial!**

Por tempo limitado, obtém {plano} com {desconto}% de desconto!

💰 **Preço Normal:** {preco_normal}/mês
✨ **Preço Promo:** {preco_promo}/mês

⏰ **Oferta válida até:** {data_limite}

Aproveita agora:
/promo_{codigo}

{disclaimer}
```

---

### 11. Suporte

#### Template: SUPPORT_TICKET_CREATED
```markdown
🎫 **Ticket de Suporte Criado**

O teu ticket foi criado com sucesso!

📋 **Ticket ID:** #{ticket_id}
📝 **Assunto:** {assunto}
⏰ **Criado em:** {timestamp}

A nossa equipa responderá dentro de {sla_horas} horas.

Podes acompanhar o estado do ticket:
/ticket {ticket_id}
```

---

### 12. Compliance

#### Template: COMPLIANCE_DISCLAIMER
```markdown
⚠️ **Disclaimer**

Este sinal é informação pura baseada em modelos quantitativos. Não constitui aconselhamento financeiro nem garantia de lucro.

As apostas envolvem risco. Nunca apostes mais do que podes perder. Jogue responsavelmente.

Para mais informações:
/privacidade
/termos
```

#### Template: COMPLIANCE_PRIVACY
```markdown
🔒 **Política de Privacidade**

A tua privacidade é importante para nós.

📋 **O que recolhemos:**
• Nome e username Telegram
• Email (se fornecido)
• Dados de subscrição
• Preferências de notificação

🔐 **Como protegemos:**
• Encriptação de dados
• Acesso restrito
• Compliance GDPR

📧 **Os teus direitos:**
• Aceder aos teus dados: /meusdados
• Corrigir dados: /atualizarperfil
• Eliminar conta: /eliminarconta

Para ler a política completa: [Link]({url_privacidade})
```

---

### 13. Manutenção

#### Template: MAINTENANCE_SCHEDULED
```markdown
🔧 **Manutenção Programada**

Olá, {nome}!

Vamos realizar manutenção no sistema:

📅 **Data:** {data_manutencao}
⏰ **Horário:** {horario_inicio} - {horario_fim} (timezone: {timezone})
⏱️ **Duração estimada:** {duracao_minutos} minutos

🚫 **Impacto:**
• Sinais podem ser atrasados
• Algumas funcionalidades podem estar indisponíveis

Pedimos desculpa pelo inconveniente.

{disclaimer}
```

#### Template: MAINTENANCE_IN_PROGRESS
```markdown
🔧 **Manutenção em Curso**

O sistema está atualmente em manutenção.

⏰ **Início:** {horario_inicio}
⏱️ **Duração estimada:** {duracao_minutos} minutos

Estamos a trabalhar para restaurar o serviço o mais rápido possível.

Agradecemos a tua paciência.
```

---

### 14. Cancelamento

#### Template: CANCELLATION_CONFIRMATION
```markdown
✅ **Cancelamento Confirmado**

Olá, {nome}!

A tua subscrição {plano} foi cancelada com sucesso.

📅 **Acesso até:** {data_fim}
💰 **Próximo cobrança:** Nenhuma

O que acontece agora:
• Continuarás a ter acesso até ao fim do período atual
• Serás removido dos grupos Telegram automaticamente
• Os teus dados serão mantidos por 30 dias (conforme GDPR)

Se mudares de ideia, podes reativar a qualquer momento:
/reactivar

Agradecemos a tua preferência!
```

---

### 15. Notificações Administrativas

#### Template: ADMIN_BROADCAST
```markdown
📢 **Comunicado Oficial**

{mensagem}

— Equipa NBA Value Signals
```

#### Template: ADMIN_ALERT
```markdown
🚨 **ALERTA DE SISTEMA**

{mensagem}

Prioridade: {prioridade}
Timestamp: {timestamp}

Ação requerida: {acao_requerida}
```

---

## Sistema de Renderização

```python
class TemplateRenderer:
    """
    Renderiza templates com placeholders e personalização.
    """
    def __init__(self, templates_dir, default_language="pt"):
        self.templates_dir = templates_dir
        self.default_language = default_language
        self.validator = TemplateValidator()

    def render(self, template_name, context, language=None):
        """
        Renderiza um template com o contexto fornecido.
        """
        language = language or self.default_language

        # 1. Carregar template
        template = self._load_template(template_name, language)

        # 2. Validar placeholders
        self.validator.validate(template_name, context)

        # 3. Formatar valores
        formatted_context = self._format_context(context)

        # 4. Substituir placeholders
        message = template
        for key, value in formatted_context.items():
            placeholder = f"{{{key}}}"
            message = message.replace(placeholder, str(value))

        # 5. Adicionar disclaimer se não presente
        if "{disclaimer}" not in template:
            message += "\n\n" + self._load_template("COMPLIANCE_DISCLAIMER", language)

        return message

    def _format_context(self, context):
        """
        Formata valores monetários, datas, etc.
        """
        formatted = {}

        for key, value in context.items():
            if key.endswith("_eur") or key.startswith("valor_"):
                formatted[key] = f"€{value:.2f}"
            elif key.endswith("_percentual") or key.endswith("%"):
                formatted[key] = f"{value:.2f}%"
            elif isinstance(value, datetime):
                formatted[key] = value.strftime("%Y-%m-%d %H:%M")
            elif isinstance(value, date):
                formatted[key] = value.strftime("%Y-%m-%d")
            else:
                formatted[key] = value

        return formatted

    def _load_template(self, template_name, language):
        """
        Carrega template do ficheiro.
        """
        path = f"{self.templates_dir}/{language}/{template_name}.md"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
```

---

## Thresholds e Tabelas

| Template | Tamanho Máximo | Variáveis Obrigatórias | Personalização |
|----------|----------------|------------------------|----------------|
| WELCOME_NEW | 2000 chars | nome | Idioma |
| SIGNAL_NEW | 4000 chars | sinal_id, mercado, odd, stake, edge | Idioma, timezone |
| RESULT_WIN | 1500 chars | sinal_id, pnl | Idioma |
| DAILY_SUMMARY | 2000 chars | data, total_sinais, wins, losses, pnl | Idioma |
| ERROR_SUBSCRIPTION_EXPIRED | 1000 chars | nome, data_fim | Idioma |

| Categoria | Frequência de Envio | Prioridade | Rate Limit |
|-----------|---------------------|------------|------------|
| Sinais | Event-driven | Alta | Sem limite |
| Resultados | Event-driven | Alta | Sem limite |
| Resumos | Diário/Semanal | Média | 1/dia |
| Alertas | Event-driven | Alta | Sem limite |
| Marketing | Semanal | Baixa | 1/semana |
| Lembretes | Diário | Média | 1/dia |

---

## Links Cruzados

- [[FORMATO_SINAIS]] → Especificação técnica de sinais
- [[COMANDOS_BOT]] → Comandos que usam templates
- [[USER_MANAGEMENT]] → Dados do utilizador para personalização
- [[TELEGRAM_BOT_ARCHITECTURE]] → Componente de renderização