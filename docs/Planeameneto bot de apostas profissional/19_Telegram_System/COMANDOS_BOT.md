---
ID: TEL-003
tags: #status/active #telegram #bot #commands #interaction
---

# Comandos do Bot Telegram

## Objetivo
Documentar de forma exaustiva todos os comandos, interações e respostas do bot Telegram, especificando a sintaxe, os parâmetros, as permissões, as dependências de backend, e os possíveis estados de erro para cada comando. Esta nota serve como especificação técnica para desenvolvimento e como referência para testes e onboarding de subscritores.

## O que faz
- Cataloga comandos públicos (disponíveis a todos os subscritores), comandos administrativos (disponíveis a staff), e comandos de manutenção (disponíveis a engenharia).
- Define o parser de comandos: como o texto da mensagem é decomposto em comando, subcomando, e argumentos.
- Especifica o formato de resposta para cada comando: texto simples, Markdown, inline keyboards, ou mensagens editáveis.
- Documenta estados de erro: comando não reconhecido, permissão insuficiente, subscrição expirada, serviço indisponível, e rate limit excedido.

## Porque existe
- **Descoberta de Funcionalidades**: Subscritores novos precisam de uma lista clara do que podem fazer. Sem documentação, o bot subutilizado perde valor percebido.
- **Consistência de Implementação**: Desenvolvedores que adicionam novos comandos precisam seguir um padrão para garantir que o parser, rate limiting, e logging sejam consistentes.
- **Testes Automatizados**: Cada comando documentado com entradas e saídas esperadas permite testes de regressão automatizados (ex: pytest com mock do Telegram API).
- **Suporte ao Cliente**: Quando um subscritor pergunta "como vejo as minhas estatísticas?", a equipa de suporte consulta esta nota e responde imediatamente.

## Implementação / Pseudocódigo
```python
class ComandosBot:
    def __init__(self):
        self.comandos = {
            "/start": {
                "descricao": "Inicia interação com o bot; envia boas-vindas e disclaimer",
                "permissoes": "PUBLICO",
                "parametros": [],
                "resposta": "mensagem_boas_vindas",
                "dependencias": ["verificar_subscricao"],
                "rate_limit": "baixo"
            },
            "/help": {
                "descricao": "Lista todos os comandos disponíveis para o utilizador",
                "permissoes": "PUBLICO",
                "parametros": ["categoria_opcional"],
                "resposta": "lista_comandos_filtrada",
                "dependencias": [],
                "rate_limit": "baixo"
            },
            "/status": {
                "descricao": "Mostra estado atual da subscrição: plano, dias restantes, renovação",
                "permissoes": "SUBSCRITOR_ATIVO",
                "parametros": [],
                "resposta": "estado_subscricao",
                "dependencias": ["bd_subscricoes"],
                "rate_limit": "baixo"
            },
            "/stats": {
                "descricao": "Estatísticas pessoais de performance vs. modelo global",
                "permissoes": "SUBSCRITOR_ATIVO",
                "parametros": ["periodo_opcional"],  # hoje, semana, mes, total
                "resposta": "estatisticas_performance",
                "dependencias": ["bd_apostas", "calculadora_metrics"],
                "rate_limit": "medio"
            },
            "/historico": {
                "descricao": "Lista últimos N sinais enviados ao subscritor com resultados",
                "permissoes": "SUBSCRITOR_ATIVO",
                "parametros": ["n_opcional", "filtro_opcional"],  # ex: /historico 10 WIN
                "resposta": "lista_sinais",
                "dependencias": ["bd_sinais"],
                "rate_limit": "medio"
            },
            "/unidade": {
                "descricao": "Define o valor monetário da unidade de stake para cálculos de P&L",
                "permissoes": "SUBSCRITOR_ATIVO",
                "parametros": ["valor_eur"],
                "resposta": "confirmacao_unidade",
                "dependencias": ["bd_subscricoes"],
                "rate_limit": "baixo"
            },
            "/alertas": {
                "descricao": "Configura preferências de notificação (sinais, resultados, manutenção)",
                "permissoes": "SUBSCRITOR_ATIVO",
                "parametros": ["tipo", "acao"],  # /alertas sinais on
                "resposta": "confirmacao_alertas",
                "dependencias": ["bd_preferencias"],
                "rate_limit": "baixo"
            },
            "/privacidade": {
                "descricao": "Envia link para política de privacidade e direitos do titular",
                "permissoes": "PUBLICO",
                "parametros": [],
                "resposta": "link_privacidade",
                "dependencias": [],
                "rate_limit": "baixo"
            },
            "/cancelar": {
                "descricao": "Inicia processo de cancelamento da subscrição",
                "permissoes": "SUBSCRITOR_ATIVO",
                "parametros": [],
                "resposta": "confirmacao_cancelamento",
                "dependencias": ["gateway_pagamentos", "bd_subscricoes"],
                "rate_limit": "baixo"
            },
            "/suporte": {
                "descricao": "Abre ticket de suporte ou encaminha para canal de ajuda",
                "permissoes": "PUBLICO",
                "parametros": ["mensagem_opcional"],
                "resposta": "confirmacao_ticket",
                "dependencias": ["sistema_tickets"],
                "rate_limit": "medio"
            },
            # Admin
            "/broadcast": {
                "descricao": "Envia mensagem a todos os subscritores ativos",
                "permissoes": "ADMIN",
                "parametros": ["mensagem"],
                "resposta": "confirmacao_envio",
                "dependencias": ["bd_subscricoes", "bot_sender"],
                "rate_limit": "critico"
            },
            "/stats_global": {
                "descricao": "Estatísticas agregadas de todos os subscritores (anonimizado)",
                "permissoes": "ADMIN",
                "parametros": ["periodo_opcional"],
                "resposta": "dashboard_texto",
                "dependencias": ["bd_apostas", "calculadora_metrics"],
                "rate_limit": "medio"
            },
            "/manutencao": {
                "descricao": "Notifica subscritores de manutenção programada",
                "permissoes": "ADMIN",
                "parametros": ["data_hora", "duracao", "descricao"],
                "resposta": "confirmacao_manutencao",
                "dependencias": ["bd_subscricoes", "bot_sender"],
                "rate_limit": "critico"
            },
            "/circuit_breaker_status": {
                "descricao": "Mostra estado atual dos circuit breakers",
                "permissoes": "ADMIN",
                "parametros": [],
                "resposta": "estado_cb",
                "dependencias": ["sistema_risco"],
                "rate_limit": "baixo"
            }
        }

    def processar_comando(self, user_id, chat_id, texto_completo):
        partes = texto_completo.split()
        comando = partes[0].lower()
        args = partes[1:]
        
        if comando not in self.comandos:
            return self.resposta_erro("COMANDO_DESCONHECIDO", chat_id)
        
        config = self.comandos[comando]
        
        # Verificar permissões
        if not self.verificar_permissao(user_id, config["permissoes"]):
            return self.resposta_erro("PERMISSAO_INSUFICIENTE", chat_id)
        
        # Verificar rate limit
        if not self.verificar_rate_limit(user_id, config["rate_limit"]):
            return self.resposta_erro("RATE_LIMIT", chat_id)
        
        # Verificar dependências
        for dep in config["dependencias"]:
            if not self.verificar_dependencia(dep):
                return self.resposta_erro("SERVICO_INDISPONIVEL", chat_id)
        
        # Validar argumentos
        validacao = self.validar_argumentos(comando, args)
        if not validacao["valido"]:
            return self.resposta_erro("ARGUMENTO_INVALIDO", chat_id, detalhe=validacao["erro"])
        
        # Executar handler
        handler = getattr(self, f"handler_{comando.lstrip('/')}")
        return handler(user_id, chat_id, args)

    def resposta_erro(self, codigo, chat_id, detalhe=None):
        mensagens = {
            "COMANDO_DESCONHECIDO": "❓ Comando não reconhecido. Use /help para ver os comandos disponíveis.",
            "PERMISSAO_INSUFICIENTE": "🚫 Não tem permissão para executar este comando.",
            "RATE_LIMIT": "⏳ Muitos comandos em pouco tempo. Aguarde um momento.",
            "SERVICO_INDISPONIVEL": "🔧 Serviço temporariamente indisponível. Tente novamente mais tarde.",
            "ARGUMENTO_INVALIDO": f"⚠️ Argumento inválido. Detalhe: {detalhe}",
            "SUBSCRICAO_EXPIRADA": "⏰ A sua subscrição expirou. Renove em [link] para continuar a receber sinais."
        }
        return {"chat_id": chat_id, "texto": mensagens.get(codigo, "Erro desconhecido.")}

    def handler_start(self, user_id, chat_id, args):
        subscritor = self.db.obter_ou_criar_subscritor(user_id, chat_id)
        boas_vindas = self.renderizar_boas_vindas(subscritor)
        self.enviar_mensagem(chat_id, boas_vindas)
        return {"status": "OK", "acao": "subscritor_iniciado"}

    def handler_stats(self, user_id, chat_id, args):
        periodo = args[0] if args else "mes"
        metricas = self.calculadora.calcular_metricas_subscritor(user_id, periodo)
        resposta = self.renderizar_stats(metricas)
        self.enviar_mensagem(chat_id, resposta)
        return {"status": "OK", "acao": "stats_enviado"}

    def handler_broadcast(self, user_id, chat_id, args):
        mensagem = " ".join(args)
        subscritores = self.db.listar_subscritores_ativos()
        resultado = self.bot_sender.broadcast(subscritores, mensagem)
        self.enviar_mensagem(chat_id, f"Broadcast enviado para {resultado['enviados']} subscritores. Falhas: {resultado['falhas']}.")
        return {"status": "OK", "acao": "broadcast_executado"}
```

## Thresholds e Tabelas

| Comando | Permissão | Rate Limit | Argumentos | Dependências | Tempo Resposta |
|---------|-----------|------------|------------|-------------|----------------|
| /start | Público | 10/min | Nenhum | BD subscritores | < 1s |
| /help | Público | 10/min | [categoria] | Nenhuma | < 1s |
| /status | Subscritor ativo | 10/min | Nenhum | BD subscrições | < 1s |
| /stats | Subscritor ativo | 5/min | [periodo] | BD apostas, calculadora | < 2s |
| /historico | Subscritor ativo | 5/min | [N] [filtro] | BD sinais | < 2s |
| /unidade | Subscritor ativo | 5/min | valor_eur | BD subscrições | < 1s |
| /alertas | Subscritor ativo | 5/min | tipo, ação | BD preferências | < 1s |
| /privacidade | Público | 10/min | Nenhum | Nenhuma | < 1s |
| /cancelar | Subscritor ativo | 2/min | Nenhum | Gateway, BD subscrições | < 3s |
| /suporte | Público | 5/min | [mensagem] | Sistema tickets | < 2s |
| /broadcast | Admin | 1/5min | mensagem | BD subscritores, sender | < 5s |
| /stats_global | Admin | 5/min | [periodo] | BD apostas | < 2s |
| /manutencao | Admin | 1/5min | data, duração, desc | BD subscritores | < 3s |
| /circuit_breaker_status | Admin | 10/min | Nenhum | Sistema risco | < 1s |

| Código de Erro | Mensagem ao Utilizador | Log de Sistema | Ação do Operador |
|---------------|------------------------|----------------|------------------|
| COMANDO_DESCONHECIDO | "Comando não reconhecido" | INFO | Nenhuma |
| PERMISSAO_INSUFICIENTE | "Não tem permissão" | WARNING | Revisar se admin necessário |
| RATE_LIMIT | "Muitos comandos" | INFO | Monitorizar abuso |
| SERVICO_INDISPONIVEL | "Serviço indisponível" | ERROR | Verificar dependência |
| ARGUMENTO_INVALIDO | "Argumento inválido: X" | WARNING | Nenhuma |
| SUBSCRICAO_EXPIRADA | "Subscrição expirada" | INFO | Encaminhar para renew |

## Riscos
- **Risco de Comando Malicioso**: Um comando de admin mal implementado pode permitir que um subscritor comum aceda a dados de outros subscritores ou envie broadcasts.
- **Risco de Vazamento por Broadcast**: Um /broadcast enviado para o grupo errado ou com informação sensível compromete a privacidade de todos os subscritores.
- **Risco de Flood**: Comandos sem rate limit adequado podem ser explorados para DoS do bot ou da base de dados.
- **Risco de Complexidade Crescente**: Cada novo comando adiciona código, testes, e documentação. Sem disciplida, o bot torna-se um monolito difícil de manter.

## Checklist de Comandos do Bot
- [ ] Todos os comandos listados acima implementados, testados, e documentados.
- [ ] Testes unitários para cada handler cobrindo: sucesso, permissão negada, argumento inválido, serviço indisponível.
- [ ] Rate limiting testado com carga de 1000 comandos/min sem degradação.
- [ ] Comandos admin requerem 2FA ou confirmação explícita antes de ações destrutivas (broadcast, manutenção).
- [ ] Log de todos os comandos executados (incluindo falhas) arquivado por 90 dias.
- [ ] Mensagens de erro padronizadas e amigáveis; nunca expõem stack traces ou detalhes internos.
- [ ] Comando /help atualizado automaticamente sempre que um novo comando é adicionado.
- [ ] Comando /suporte cria ticket no sistema de helpdesk (Zendesk, Jira Service Management, ou similar) com chat_id e contexto.

## Links Cruzados
- [[19_Telegram_System/BOT_TELEGRAM_CONFIG]] - Configuração geral do bot que processa os comandos.
- [[19_Telegram_System/FORMATO_SINAIS]] - Como os sinais são apresentados (output do bot).
- [[19_Telegram_System/SEGURANCA_TELEGRAM]] - Segurança dos comandos admin.
- [[16_Compliance/DISCLAIMERS]] - Disclaimer incluído nas respostas de /start e /help.
