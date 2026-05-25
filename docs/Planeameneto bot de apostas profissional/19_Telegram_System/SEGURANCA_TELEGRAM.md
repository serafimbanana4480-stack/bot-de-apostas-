---
ID: TEL-005
tags: #status/active #telegram #security #threat-model #anti-fraud
---

# Segurança do Sistema Telegram

## Objetivo
Implementar uma camada defensiva completa em torno do bot Telegram, dos grupos, e dos canais do sistema de value betting NBA, protegendo contra ameaças específicas da plataforma Telegram: spoofing de bots, phishing, engenharia social, spam bots, scrapers de conteúdo, e ataques de Denial of Service via mensagens massivas. A segurança do Telegram é crítica porque é o canal principal de entrega de valor e de comunicação com subscritores.

## O que faz
- Estabelece ameaças específicas (threat model) para o ecossistema Telegram: bots clone, phishing via DM, scraping de sinais, takeover de conta admin, e abuso de forward.
- Define contramedidas técnicas: validação de webhook secret, verificação de assinatura de updates, hash de mensagens, watermarking de sinais, e restrições de forward.
- Implementa monitorização de comportamento anómalo: múltiplas contas com mesmo IP, padrões de scraping (baixa latência de forward), e mensagens suspeitas no grupo.
- Define protocolos de resposta a incidente: se um clone do bot for detetado, se um admin for comprometido, ou se houver vazamento massivo de sinais.

## Porque existe
- **Clonagem de Bots**: Um atacante pode criar um bot com nome e foto idênticos ao oficial, enviar DMs a subscritores com "promoções" ou pedir credenciais. Subscritores menos atentos podem cair.
- **Scraping de Sinais**: Um competidor ou um subscritor mal-intencionado pode usar um bot scraper para copiar todos os sinais do canal/grupo e revendê-los ou publicá-los gratuitamente, destruindo o modelo de subscrição.
- **Takeover de Admin**: Se o telemóvel de um admin for comprometido (SIM swap, malware), o atacante ganha controlo total dos grupos e pode banir subscritores, apagar conteúdo, ou enviar mensagens maliciosas.
- **Abuso de Forward**: A funcionalidade de forward do Telegram permite que um subscritor envie um sinal para um grupo público de milhares em segundos. Embora não seja prevenível tecnicamente, deve ser monitorizado e dissuadido contratualmente.

## Implementação / Pseudocódigo
```python
class SegurancaTelegram:
    def __init__(self):
        self.threat_model = {
            "T1_BOT_CLONE": {"probabilidade": "ALTA", "impacto": "ALTO", "vetor": "Atacante cria bot com nome/foto idênticos"},
            "T2_PHISHING_DM": {"probabilidade": "MEDIA", "impacto": "ALTO", "vetor": "Atacante DMs subscritores pedindo dados/pagamentos"},
            "T3_SCRAPING": {"probabilidade": "ALTA", "impacto": "ALTO", "vetor": "Bot automatizado copia todos os sinais do canal"},
            "T4_ADMIN_TAKEOVER": {"probabilidade": "BAIXA", "impacto": "CRITICO", "vetor": "Conta admin comprometida"},
            "T5_FORWARD_ABUSE": {"probabilidade": "ALTA", "impacto": "MEDIO", "vetor": "Sinais partilhados em grupos públicos"},
            "T6_DOS_SPAM": {"probabilidade": "MEDIA", "impacto": "MEDIO", "vetor": "Flood de mensagens para consumir quota API"}
        }
        self.contramedidas = {
            "T1": ["verificacao_username_bot", "mensagem_educativa_subscritores", "report_to_telegram"],
            "T2": ["avisos_grupo", "verificacao_links_dm", "kyc_reforcado_suspeitos"],
            "T3": ["rate_limiting_leitura", "watermarking_sinais", "monitoracao_comportamento"],
            "T4": ["2fa_admin", "numero_recuperacao_seguro", "limitacao_permissoes_admin"],
            "T5": ["clausula_contratual", "monitoracao_forward", "watermarking"],
            "T6": ["rate_limiting", "cloudflare_waf", "ban_ip"]
        }
        self.indicadores_scraping = {
            "tempo_leitura_mensagem_ms": {"threshold": 500, "nota": "Humano demora > 500ms para ler; bot scraper < 100ms"},
            "forwards_rapidos_seguidos": {"threshold": 3, "nota": "3+ forwards em < 10 segundos indica bot"},
            "nova_conta_actividade_imediata": {"threshold": True, "nota": "Conta criada hoje e já lê todos os sinais"},
            "sem_interacao_escrita": {"threshold": True, "nota": "Nunca escreve mensagem; apenas lê"}
        }

    def validar_webhook(self, request):
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret != os.environ["TELEGRAM_WEBHOOK_SECRET"]:
            self.alertar_seguranca("WEBHOOK_INVALIDO", {"ip": request.remote_addr})
            return False
        return True

    def detetar_bot_clone(self):
        # Pesquisa por bots com nomes similares ao oficial
        nome_oficial = "nba_value_signals_bot"
        variantes = ["nba_value_signal_bot", "nba_values_signals_bot", "nba-value-signals", "nbavaluesignalsbot"]
        clones = []
        for var in variantes:
            try:
                info = self.telegram.get_bot_info(var)
                if info:
                    clones.append({"username": var, "info": info})
            except:
                pass
        
        if clones:
            self.alertar_seguranca("BOT_CLONE_DETECTADO", clones)
            self.enviar_aviso_subscritores("Atenção: existe um bot falso a circular. O nosso bot oficial é @nba_value_signals_bot. Nunca partilhe dados pessoais por DM.")
        return clones

    def monitorizar_scraping(self, grupo_id):
        membros = self.telegram.listar_membros(grupo_id)
        suspeitos = []
        
        for membro in membros:
            perfil = self.analisar_perfil(membro["user_id"])
            score = 0
            
            if perfil["idade_conta_dias"] < 7:
                score += 30
            if perfil["mensagens_escritas"] == 0 and perfil["mensagens_lidas"] > 100:
                score += 40
            if perfil["tempo_medio_leitura_ms"] < 100:
                score += 30
            if perfil["forwards_ultima_semana"] > 20:
                score += 20
            
            if score >= 70:
                suspeitos.append({"user_id": membro["user_id"], "score": score, "razoes": self.obter_razoes(score)})
        
        if suspeitos:
            self.alertar_seguranca("SCRAPING_DETECTADO", suspeitos)
            for s in suspeitos:
                self.telegram.restringir_membro(grupo_id, s["user_id"], pode_enviar=False)
        
        return suspeitos

    def aplicar_watermark(self, sinal, subscritor_id):
        # Incluir metadata imperceptível ou ID único por subscritor no sinal
        # Nota: Telegram não suporta watermark visual; alternativa: hash único no texto
        sinal["watermark"] = hashlib.sha256(f"{sinal['id']}:{subscritor_id}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:8]
        sinal["texto"] += f"\n`ID: {sinal['watermark']}`"
        return sinal

    def responder_admin_takeover(self, admin_id):
        # Se detetado comportamento anómalo de admin (ex: apagar todas as mensagens, banir massivamente)
        self.telegram.revocar_admin(admin_id)
        self.telegram.notificar_outros_admins(f"Conta de admin {admin_id} suspensa por comportamento anómalo. Verificar imediatamente.")
        self.db.registrar_incidente_seguranca("ADMIN_TAKEOVER_SUSPEITO", admin_id)

    def educar_subscritores_anti_phishing(self):
        mensagem = """
⚠️ **ALERTA DE SEGURANÇA**

Nunca partilhe:
- Dados bancários por DM
- Passwords ou códigos de acesso
- Informação pessoal com "supostos" representantes

O nosso bot oficial é: @nba_value_signals_bot
Não aceitamos pagamentos por DM.

Se receber mensagens suspeitas, denuncie imediatamente.
        """
        self.enviar_para_todos(mensagem)
```

## Thresholds e Tabelas

| Ameaça | Probabilidade | Impacto | Deteção | Resposta | Frequência Monitorização |
|--------|--------------|---------|---------|----------|-------------------------|
| Bot Clone | Alta | Alto | Pesquisa diária por variantes de nome | Report + Alerta subscritores | Diária |
| Phishing DM | Média | Alto | Denúncias + NLP em DMs | Ban + Aviso comunidade | Contínua |
| Scraping | Alta | Alto | Heurísticas de comportamento | Mute/Kick + Ação legal | Contínua |
| Admin Takeover | Baixa | Crítico | Comportamento anómalo admin | Revogação + 2FA reset | Contínua |
| Forward Abuse | Alta | Médio | Heurísticas + Denúncias | Ação legal contratual | Semanal |
| DoS Spam | Média | Médio | Rate limit + WAF | Ban IP + Rate adjust | Contínua |

| Indicador de Scraping | Threshold | Ação Automática | Ação Manual |
|-----------------------|-----------|-----------------|-------------|
| Conta < 7 dias + lê 100+ msgs | Score ≥ 70 | Restringir envio | Revisão em 24h |
| Tempo médio leitura < 100ms | Score ≥ 30 | Flag para revisão | — |
| 0 mensagens escritas + 100+ lidas | Score ≥ 40 | Restringir envio | Revisão em 24h |
| > 20 forwards/semana | Score ≥ 20 | Flag para revisão | Aviso privado |
| Múltiplas contas mesmo IP no grupo | ≥ 3 contas | Ban secundárias | Verificar KYC |

## Riscos
- **Risco de Falso Positivo em Scraping**: Um subscritor legítimo que usa um leitor de ecrã ou que simplesmente lê muito e não escreve pode ser sinalizado como scraper. A revisão humana é obrigatória antes de ban.
- **Risco de Evasão de Deteção**: Scrapers sofisticados podem simular comportamento humano (delay artificial, escrever mensagens ocasionais). Nenhum sistema é infalível.
- **Risco de Plataforma**: O Telegram pode suspender o bot oficial por denúncias massivas organizadas por concorrentes ou por scrapers. Necessário plano de contingência.
- **Risco de Privacidade vs. Segurança**: Monitorar comportamento de leitura pode ser considerado excessivo por alguns subscritores. Deve ser transparente nas políticas de privacidade.

## Checklist de Segurança Telegram
- [ ] Webhook secret configurado e validado em cada request; rotação trimestral.
- [ ] Pesquisa diária automática por clones do bot; alerta se detetado.
- [ ] Sistema de heurísticas de scraping ativo em todos os grupos; revisão humana obrigatória antes de ban.
- [ ] 2FA ativado em TODAS as contas de admin do Telegram (incluindo backup admin).
- [ ] Número de recuperação de admin não associado a SIM físico vulnerável (ex: uso de Google Voice ou similar).
- [ ] Permissões de admin minimizadas: nem todos os admins precisam de "banir" ou "apagar todas as mensagens".
- [ ] Aviso de segurança anti-phishing enviado a todos os subscritores no onboarding e trimestralmente.
- [ ] Plano de contingência: canal alternativo (e-mail ou Discord) testado mensalmente; lista de subscritores exportada semanalmente.
- [ ] Watermark por subscritor em sinais VIP (hash único) para rastrear origem de vazamentos.
- [ ] Relatório mensal de segurança: clones detetados, scrapers removidos, incidentes de phishing, ações legais iniciadas.

## Links Cruzados
- [[19_Telegram_System/BOT_TELEGRAM_CONFIG]] - Configuração que inclui webhook secret.
- [[19_Telegram_System/GRUPOS_CANAIS]] - Gestão de grupos onde a segurança é aplicada.
- [[16_Compliance/PRIVACY_POLICY]] - Transparência sobre monitorização de comportamento.
- [[34_Security/SECRETS_MANAGEMENT]] - Gestão do token e webhook secret.
- [[26_Runbooks/RB-006_Telegram_Bot_Falha]] - Resposta a falha/compromisso do bot.
