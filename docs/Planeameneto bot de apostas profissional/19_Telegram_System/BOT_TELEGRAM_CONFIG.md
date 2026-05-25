---
ID: TEL-001
tags: #status/active #telegram #bot #configuration #messaging
---

# Configuração do Bot Telegram

## Objetivo
Documentar e controlar toda a configuração técnica, funcional e de segurança do bot Telegram que serve como canal principal de entrega de sinais de value betting NBA aos subscritores. Esta nota cobre a criação do bot, gestão do token, configuração de webhooks, gestão de rate limits, handlers de comandos, e integração com o backend de geração de sinais.

## O que faz
- Define o ciclo de vida do bot: criação via @BotFather, obtenção de token, configuração de webhook vs. polling, gestão de updates, e monitorização de health.
- Estabelece a arquitetura de handlers: mensagens de comando, mensagens de sinal, mensagens de administração, e mensagens de heartbeat.
- Configura rate limiting por utilizador (anti-flood) e por grupo (anti-spam), com thresholds adaptativos.
- Define fallback: se o webhook falhar, o sistema deve reverter para polling temporário com alerta.
- Documenta variáveis de ambiente, secrets, e dependências (python-telegram-bot, aiogram, ou telethon).

## Porque existe
- **Ponto Único de Falha**: O Telegram é o canal principal de entrega de valor. Se o bot falhar, o produto deixa de existir para os subscritores. A configuração rigorosa é crítica.
- **Segurança do Token**: O token do bot é equivalente a uma chave API com poder total. Se vazado, um atacante pode enviar mensagens em nome do serviço, aceder a dados de subscritores, ou deletar o bot.
- **Escalabilidade**: Com centenas ou milhares de subscritores, polling não é sustentável. Webhook com load balancer e fila de processamento é obrigatório.
- **Compliance**: Mensagens de sinal devem conter disclaimers; mensagens de marketing devem respeitar opt-out. A configuração do bot deve forçar estas inclusões.

## Implementação / Pseudocódigo
```python
class BotTelegramConfig:
    def __init__(self):
        self.bot_token = os.environ["TELEGRAM_BOT_TOKEN"]  # Nunca hardcoded
        self.webhook_url = os.environ["TELEGRAM_WEBHOOK_URL"]  # HTTPS obrigatório
        self.webhook_secret = os.environ["TELEGRAM_WEBHOOK_SECRET"]  # Para validar origin
        self.backend_url = os.environ["BACKEND_API_URL"]
        self.redis = RedisClient()
        self.db = PostgreSQLConnection()
        
        self.rate_limits = {
            "usuario_comando": {"max": 30, "janela_segundos": 60},  # 30 comandos/min
            "usuario_mensagem": {"max": 100, "janela_segundos": 60},
            "grupo_mensagem": {"max": 50, "janela_segundos": 60},
            "broadcast": {"max": 1, "janela_segundos": 5, "batch_size": 100}  # 100 msg/5s
        }
        
        self.handlers = {
            "comandos": ["/start", "/help", "/status", "/privacidade", "/cancelar", "/stats"],
            "admin": ["/broadcast", "/alerta", "/manutencao", "/circuit_breaker_status"],
            "sinais": ["sinal_novo", "sinal_resultado", "sinal_atualizacao"],
            "heartbeat": "heartbeat_interval_segundos_60"
        }

    def inicializar_bot(self):
        # Configurar webhook
        response = requests.post(
            f"https://api.telegram.org/bot{self.bot_token}/setWebhook",
            json={
                "url": self.webhook_url,
                "secret_token": self.webhook_secret,
                "max_connections": 40,
                "allowed_updates": ["message", "callback_query"]
            }
        )
        
        if response.status_code != 200:
            self.alertar_ops("Falha ao configurar webhook do Telegram; a tentar fallback polling")
            self.iniciar_polling_emergencia()
        
        self.agendar_heartbeat()
        return {"webhook_configurado": response.status_code == 200}

    def processar_update(self, update_raw):
        # Validar webhook secret
        if update_raw.headers.get("X-Telegram-Bot-Api-Secret-Token") != self.webhook_secret:
            self.alertar_seguranca("Webhook secret inválido recebido; possível tentativa de spoofing")
            return {"status": "REJEITADO", "motivo": "SECRET_INVALIDO"}
        
        update = json.loads(update_raw.body)
        
        if "message" in update:
            mensagem = update["message"]
            chat_id = mensagem["chat"]["id"]
            user_id = mensagem["from"]["id"]
            texto = mensagem.get("text", "")
            
            # Rate limiting
            if not self.verificar_rate_limit(user_id, "usuario_comando"):
                self.enviar_mensagem(chat_id, "Muitas mensagens em pouco tempo. Aguarde um momento.")
                return {"status": "RATE_LIMITED"}
            
            if texto.startswith("/"):
                return self.processar_comando(user_id, chat_id, texto)
            else:
                return self.processar_mensagem_generica(user_id, chat_id, texto)
        
        elif "callback_query" in update:
            return self.processar_callback_query(update["callback_query"])
        
        return {"status": "IGNORADO"}

    def processar_comando(self, user_id, chat_id, texto):
        comando = texto.split()[0].lower()
        
        if comando in self.handlers["comandos"]:
            handler = self.mapear_handler(comando)
            return handler.executar(user_id, chat_id, texto)
        elif comando in self.handlers["admin"]:
            if not self.verificar_admin(user_id):
                self.enviar_mensagem(chat_id, "Acesso negado.")
                return {"status": "NAO_AUTORIZADO"}
            handler = self.mapear_handler(comando)
            return handler.executar(user_id, chat_id, texto)
        else:
            self.enviar_mensagem(chat_id, "Comando não reconhecido. Use /help para ver os comandos disponíveis.")
            return {"status": "COMANDO_DESCONHECIDO"}

    def enviar_sinal(self, subscritores, sinal):
        # Rate limiting em broadcast
        batch_size = self.rate_limits["broadcast"]["batch_size"]
        janela = self.rate_limits["broadcast"]["janela_segundos"]
        
        mensagem = self.formatar_sinal(sinal)
        
        for i in range(0, len(subscritores), batch_size):
            batch = subscritores[i:i+batch_size]
            for sub in batch:
                try:
                    self.enviar_mensagem(sub.chat_id, mensagem, parse_mode="Markdown")
                except Exception as e:
                    self.db.registrar_falha_envio(sub.id, sinal["id"], str(e))
            time.sleep(janela)
        
        return {"enviados": len(subscritores), "falhas": self.db.contar_falhas(sinal["id"])}

    def verificar_rate_limit(self, user_id, tipo):
        chave = f"ratelimit:{tipo}:{user_id}"
        atual = self.redis.incr(chave)
        if atual == 1:
            self.redis.expire(chave, self.rate_limits[tipo]["janela_segundos"])
        return atual <= self.rate_limits[tipo]["max"]

    def agendar_heartbeat(self):
        schedule.every(1).minutes.do(self.enviar_heartbeat_ops)

    def enviar_heartbeat_ops(self):
        self.enviar_mensagem(self.ops_chat_id, f"🫀 Bot heartbeat - {datetime.utcnow().isoformat()}")
```

## Thresholds e Tabelas

| Parâmetro | Valor Padrão | Limite Telegram API | Threshold Alerta | Ação |
|-----------|-------------|---------------------|------------------|------|
| Webhook max_connections | 40 | 100 | Se API rejeita | Reduzir para 20 |
| Rate limit comandos/utilizador | 30/min | — | > 80% do limite | Aviso ao utilizador |
| Rate limit broadcast | 100 msg / 5s | 30 msg/s global | > 50% da capacidade | Throttle + alerta |
| Tempo resposta handler | < 200ms | — | > 500ms | Alerta P3 |
| Falhas de envio consecutivas | < 3 | — | ≥ 3 para mesmo subscritor | Marcar subscritor para revisão |
| Heartbeat intervalo | 60 segundos | — | Ausente > 3 minutos | Alerta P2 |
| Tamanho máximo mensagem | 4096 chars | 4096 chars | > 3500 chars | Dividir em múltiplas mensagens |

| Handler | Comando | Quem Pode Usar | O que Faz | Dependências |
|---------|---------|---------------|-----------|-------------|
| /start | Público | Novo subscritor | Envia mensagem de boas-vindas + disclaimer | — |
| /help | Público | Qualquer utilizador | Lista comandos disponíveis | — |
| /status | Subscritor ativo | Subscritor pago | Mostra estado da subscrição, dias restantes | BD subscrições |
| /privacidade | Público | Qualquer utilizador | Enlace para política de privacidade | — |
| /stats | Subscritor ativo | Subscritor pago | Performance pessoal vs. modelo geral | BD apostas |
| /broadcast | Admin | Staff autorizado | Envia mensagem a todos os subscritores | — |
| /alerta | Admin | Staff autorizado | Envia alerta operacional a canal de ops | — |
| /manutencao | Admin | Staff autorizado | Notifica manutenção programada | — |

---

## Operações Diárias

### Rotina Matinal (08:00 UTC)
1. **Health Check**
   - Verificar status do webhook: `curl https://api.telegram.org/bot{TOKEN}/getWebhookInfo`
   - Verificar conexão PostgreSQL: `SELECT 1`
   - Verificar conexão Redis: `PING`
   - Verificar fila de processamento: `LLEN telegram_updates`

2. **Limpeza de Logs**
   - Remover logs com > 7 dias (manter apenas erros)
   - Compactar logs de auditoria
   - Verificar espaço em disco (> 20% livre)

3. **Verificação de Rate Limits**
   - Resetar contadores de rate limit diários
   - Analisar utilizadores que excederam limites
   - Ajustar thresholds se necessário

### Rotina Contínua (24/7)
1. **Monitorização de Updates**
   - Processar updates da fila dentro de 5 segundos
   - Retry automático para falhas transitórias (max 3 tentativas)
   - Alerta P2 se fila > 1000 updates pendentes

2. **Envio de Sinais**
   - Verificar novos sinais a cada 30 segundos
   - Enviar para subscritores elegíveis
   - Registrar estatísticas de envio (sucesso, falha, latência)

3. **Heartbeat**
   - Enviar heartbeat para grupo de ops a cada 60 segundos
   - Incluir timestamp, uptime, e métricas básicas
   - Alerta P3 se heartbeat ausente > 3 minutos

### Rotina Noturna (23:00 UTC)
1. **Backup Diário**
   - Backup da base de dados PostgreSQL
   - Backup do Redis (dump.rdb)
   - Backup dos logs do dia
   - Upload para S3/GCS com retenção 30 dias

2. **Relatórios Diários**
   - Gerar relatório de utilização do bot
   - Gerar relatório de erros e exceções
   - Gerar relatório de performance de envio
   - Enviar email para ops team

3. **Manutenção Preventiva**
   - Limpar cache Redis (entradas expiradas)
   - Vacuum na base de dados PostgreSQL
   - Verificar e atualizar dependências se necessário

---

## Troubleshooting Comum

### Problema: Webhook não responde
**Sintomas:** Updates não chegam, timeout na API Telegram
**Diagnóstico:**
```bash
# Verificar se webhook está configurado
curl https://api.telegram.org/bot{TOKEN}/getWebhookInfo

# Verificar logs do servidor
tail -f /var/log/telegram-bot/webhook.log

# Testar endpoint webhook
curl -X POST https://seu-webhook-url.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"update_id": 123}'
```
**Solução:**
- Verificar se servidor está online
- Verificar certificado SSL (deve ser válido)
- Verificar firewall/portas (443 deve estar aberto)
- Se persistir, reverter para polling temporário

### Problema: Rate limit excedido
**Sintomas:** Erro 429 Too Many Requests da API Telegram
**Diagnóstico:**
```python
# Verificar contadores no Redis
redis.get("ratelimit:broadcast:global")
```
**Solução:**
- Aguardar até limite reset
- Ajustar batch size para menor valor
- Implementar exponential backoff
- Considerar múltiplos bots para distribuir carga

### Problema: Mensagens não são entregues
**Sintomas:** Sem erros, mas subscritores reportam não receber sinais
**Diagnóstico:**
```sql
-- Verificar se subscritor está ativo
SELECT * FROM subscriptions WHERE user_id = X AND status = 'ACTIVE';

-- Verificar se está no grupo correto
SELECT * FROM group_members WHERE user_id = X;
```
**Solução:**
- Verificar se subscrição está ativa
- Verificar sincronização com grupos Telegram
- Verificar se utilizador bloqueou o bot
- Verificar preferências de notificação

---

## Riscos
- **Risco de Token Vazado**: Token exposto em repositório GitHub, log, ou mensagem de erro permite controlo total do bot. Deve estar apenas em environment variables e secrets manager.
- **Risco de Webhook Indisponível**: Falha no servidor, DNS, ou certificado SSL invalida o webhook. O fallback para polling deve ser automático e testado.
- **Risco de Banimento por Spam**: Envio de mensagens a subscritores que deram unsubscribe ou que reportaram o bot como spam pode levar ao banimento da conta pelo Telegram.
- **Risco de Não Entrega Silenciosa**: Algumas mensagens podem falhar sem erro explícito (ex: utilizador bloqueou o bot). Necessário tracking de entrega e reativação.

## Checklist de Configuração do Bot
- [ ] Bot criado via @BotFather com username único e descrição profissional.
- [ ] Bot token armazenado em [[34_Security/SECRETS_MANAGEMENT]] (AWS Secrets Manager, Azure Key Vault, ou HashiCorp Vault); nunca em código ou .env comitado.
- [ ] Webhook configurado com HTTPS válido (Let's Encrypt ou comercial) e secret token para validação de origin.
- [ ] Fallback para polling testado mensalmente em ambiente de staging.
- [ ] Rate limiting implementado e testado com carga sintética (1000 comandos/min).
- [ ] Handler de heartbeat enviando mensagem a canal de ops a cada 60 segundos.
- [ ] Todos os handlers de comandos cobertos por testes unitários (pytest).
- [ ] Logs de todos os updates recebidos e mensagens enviadas arquivados por 90 dias (GDPR compliance).
- [ ] Bot adicionado a todos os grupos/canais como administrador com permissões mínimas necessárias.

## Links Cruzados
- [[19_Telegram_System/FORMATO_SINAIS]] - Como os sinais são formatados antes de serem enviados pelo bot.
- [[19_Telegram_System/COMANDOS_BOT]] - Documentação detalhada de cada comando.
- [[19_Telegram_System/GRUPOS_CANAIS]] - Configuração de grupos e canais onde o bot opera.
- [[19_Telegram_System/SEGURANCA_TELEGRAM]] - Medidas de segurança específicas do Telegram.
- [[26_Runbooks/RB-006_Telegram_Bot_Falha]] - Runbook de resposta a falha do bot.
