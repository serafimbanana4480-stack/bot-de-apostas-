---
ID: TEL-004
tags: #status/active #telegram #groups #channels #community
---

# Grupos e Canais Telegram

## Objetivo
Estruturar, documentar e gerir a arquitetura de grupos e canais Telegram utilizados pelo sistema de value betting NBA, definindo o propósito de cada comunidade, as regras de conduta, a configuração de permissões, o mecanismo de onboarding/offboarding de membros, e as políticas de moderação. A estrutura deve escalar desde um pequeno grupo de subscritores até uma comunidade de milhares, mantendo a qualidade da informação e o cumprimento das obrigações legais.

## O que faz
- Define a estrutura hierárquica de comunidades: Canal Oficial (broadcast unidirecional), Grupo de Subscritores (bidirecional, moderado), Grupo VIP/Pro (subscritores de plano superior), Grupo de Operações (privado, staff), Grupo de Testes (QA), Canal de Alertas (ops).
- Especifica configurações de privacidade: quem pode enviar mensagens, adicionar membros, editar informações, e acessar histórico.
- Estabelece regras de conduta (community guidelines) e política de moderação: o que constitui spam, off-topic, ou comportamento proibido; quem são os moderadores; e o processo de sanções (aviso, mute, kick, ban).
- Implementa mecanismo de sincronização de subscrições: quando um subscritor paga, é adicionado automaticamente ao grupo correto; quando cancela ou a subscrição expira, é removido automaticamente.

## Porque existe
- **Segregação de Informação**: Subscritores do plano Essencial não devem ver sinais do plano Pro. A estrutura de grupos/canais garante que a informação flui apenas para quem pagou pelo acesso.
- **Qualidade da Comunidade**: Um grupo de subscritores sem moderação degenera rapidamente em spam de bookmakers, "dicas" não verificadas, e discussões tóxicas, devaluizando o produto.
- **Compliance**: O canal oficial é um ponto de contacto regulatório. Deve respeitar regras de publicidade, incluir disclaimers, e não prometer ganhos.
- **Suporte Escala**: Canais unidirecionais (broadcast) permitem enviar sinais a milhares sem sobrecarregar o bot; grupos bidirecionais permitem Q&A controlado.

## Implementação / Pseudocódigo
```python
class GruposCanais:
    def __init__(self):
        self.estrutura = {
            "canal_oficial": {
                "tipo": "CANAL",
                "id": "@nba_value_signals",
                "descricao": "Sinais oficiais e anúncios. Unidirecional.",
                "permissoes": {"enviar": ["bot", "admin"], "comentar": False, "historico": True},
                "publico": False,  # canal privado, acesso por link de convite
                "planos_permitidos": ["ESSENCIAL", "PRO", "INSTITUCIONAL"]
            },
            "grupo_subscritores": {
                "tipo": "GRUPO",
                "id": "-1001234567890",
                "descricao": "Comunidade geral de subscritores. Moderado.",
                "permissoes": {"enviar": "MEMBROS", "media": True, "links": True, "historico": True},
                "publico": False,
                "planos_permitidos": ["ESSENCIAL", "PRO", "INSTITUCIONAL"],
                "moderadores": ["admin1", "admin2", "bot_moderador"]
            },
            "grupo_vip": {
                "tipo": "GRUPO",
                "id": "-1009876543210",
                "descricao": "Grupo exclusivo subscritores PRO e Institucional.",
                "permissoes": {"enviar": "MEMBROS", "media": True, "links": True, "historico": True},
                "publico": False,
                "planos_permitidos": ["PRO", "INSTITUCIONAL"],
                "moderadores": ["admin1", "bot_moderador"]
            },
            "grupo_operacoes": {
                "tipo": "GRUPO",
                "id": "-1001112223334",
                "descricao": "Staff apenas. Alertas, handoffs, decisões.",
                "permissoes": {"enviar": "MEMBROS", "media": True, "links": True, "historico": True},
                "publico": False,
                "planos_permitidos": [],  # manual
                "moderadores": ["gestor_ops"]
            },
            "grupo_testes": {
                "tipo": "GRUPO",
                "id": "-1005556667778",
                "descricao": "QA e testes de bot.",
                "permissoes": {"enviar": "MEMBROS", "media": True, "links": True, "historico": False},
                "publico": False,
                "planos_permitidos": [],  # manual
                "moderadores": ["qa_lead"]
            },
            "canal_alertas": {
                "tipo": "CANAL",
                "id": "@nba_ops_alerts",
                "descricao": "Alertas operacionais P1 e P2. Unidirecional.",
                "permissoes": {"enviar": ["bot", "admin"], "comentar": False, "historico": True},
                "publico": False,
                "planos_permitidos": []  # staff only
            }
        }
        self.regras_conduta = [
            "Respeito mútuo; zero tolerância para insultos ou discriminação",
            "Não partilhar sinais fora do grupo (violação de IP)",
            "Não promover outros serviços de apostas sem autorização",
            "Não solicitar dados pessoais ou bancários de outros membros",
            "Mensagens off-topic devem ser limitadas; canal #offtopic se necessário",
            "Denunciar spam ao bot ou moderador"
        ]
        self.sancoes = {
            "AVISO": {"descricao": "Mensagem privada de aviso", "acumulacoes": 2},
            "MUTE_24H": {"descricao": "Silenciamento por 24 horas", "acumulacoes": 2},
            "KICK": {"descricao": "Remoção do grupo; pode reentrar", "acumulacoes": 1},
            "BAN": {"descricao": "Banimento permanente", "acumulacoes": 1}
        }

    def sincronizar_acessos(self):
        subscritores_ativos = self.db.listar_subscritores_ativos_com_plano()
        
        for grupo_id, config in self.estrutura.items():
            if not config["planos_permitidos"]:
                continue  # gestão manual
            
            membros_atuais = self.telegram.listar_membros(config["id"])
            ids_subscritores = {s["chat_id"] for s in subscritores_ativos if s["plano"] in config["planos_permitidos"]}
            ids_membros = {m["user_id"] for m in membros_atuais}
            
            # Adicionar novos
            para_adicionar = ids_subscritores - ids_membros
            for user_id in para_adicionar:
                self.telegram.adicionar_membro(config["id"], user_id)
                self.db.registrar_acao_grupo(user_id, config["id"], "ADICIONADO")
            
            # Remover expirados
            para_remover = ids_membros - ids_subscritores
            for user_id in para_remover:
                self.telegram.remover_membro(config["id"], user_id)
                self.db.registrar_acao_grupo(user_id, config["id"], "REMOVIDO")
                self.enviar_notificacao(user_id, "O seu acesso ao grupo foi removido devido ao término da subscrição.")

    def moderar_mensagem(self, grupo_id, mensagem):
        # Filtros automáticos
        if self.detectar_spam(mensagem["texto"]):
            self.telegram.apagar_mensagem(grupo_id, mensagem["message_id"])
            self.aplicar_sancao(mensagem["from"]["id"], "AVISO")
            return {"acao": "SPAM_REMOVIDO"}
        
        if self.detectar_link_nao_autorizado(mensagem["texto"]):
            self.telegram.apagar_mensagem(grupo_id, mensagem["message_id"])
            return {"acao": "LINK_REMOVIDO"}
        
        if self.detectar_dados_sensiveis(mensagem["texto"]):
            self.telegram.apagar_mensagem(grupo_id, mensagem["message_id"])
            self.aplicar_sancao(mensagem["from"]["id"], "MUTE_24H")
            return {"acao": "DADOS_SENSIVEIS_REMOVIDOS"}
        
        return {"acao": "APROVADO"}

    def aplicar_sancao(self, user_id, tipo_sancao):
        historico = self.db.obter_historico_sancoes(user_id)
        sancao = self.sancoes[tipo_sancao]
        
        if tipo_sancao == "AVISO" and historico["avisos"] >= sancao["acumulacoes"]:
            tipo_sancao = "MUTE_24H"
        elif tipo_sancao == "MUTE_24H" and historico["mutes"] >= sancao["acumulacoes"]:
            tipo_sancao = "KICK"
        
        self.telegram.aplicar_restricao(user_id, tipo_sancao)
        self.db.registrar_sancao(user_id, tipo_sancao)
        
        if tipo_sancao in ["KICK", "BAN"]:
            self.enviar_notificacao(user_id, f"Foi removido do grupo devido a violação das regras. Contacte suporte para apelo.")
```

## Thresholds e Tabelas

| Comunidade | Tipo | Permissão Enviar | Planos | Moderação | Histórico | Link Público |
|-----------|------|-----------------|--------|-----------|-----------|-------------|
| Canal Oficial | Canal | Bot + Admin | Todos | Pré-publicação | Sim | Não (privado) |
| Grupo Subscritores | Grupo | Membros | Essencial+ | Bot + Humanos | Sim | Não (convite) |
| Grupo VIP | Grupo | Membros | Pro+ | Bot + Humanos | Sim | Não (convite) |
| Grupo Operações | Grupo | Staff | Manual | Gestor Ops | Sim | Não |
| Grupo Testes | Grupo | QA | Manual | QA Lead | Não | Não |
| Canal Alertas | Canal | Bot | Staff | Automático | Sim | Não |

| Infração | Deteção | 1ª Ocorrência | 2ª Ocorrência | 3ª Ocorrência |
|----------|---------|--------------|---------------|----------------|
| Spam | Bot (keywords, frequência) | Aviso + Apagar | Mute 24h | Kick |
| Promo não autorizada | Bot (links externos) | Aviso + Apagar | Mute 24h | Kick |
| Dados sensíveis | Bot (regex NIF, IBAN, CC) | Apagar + Mute 24h | Kick | Ban |
| Insultos | Humanos + Bot (NLP) | Aviso | Mute 24h | Kick |
| Partilha de sinais | Denúncia + Bot | Aviso | Kick | Ban |
| Off-topic excessivo | Humanos | Aviso | Mute 12h | — |

## Riscos
- **Risco de Vazamento**: Um subscritor do grupo VIP pode fazer screenshot dos sinais e partilhar fora. A moderação não previne vazamento, mas a cláusula contratual de IP permite ação legal.
- **Risco de Comunidade Tóxica**: Moderação insuficiente afasta subscritores de valor. Necessário investimento em moderadores humanos qualificados, não apenas bots.
- **Risco de Sincronização Falhada**: Se o sistema de pagamentos não sincronizar corretamente com o Telegram, um subscritor pago pode ser removido do grupo ou um não-pago pode ficar.
- **Risco de Dependência da Plataforma**: O Telegram pode suspender o canal ou grupo por violação das suas TOS (ex: conteúdo relacionado com jogo). Necessário canal alternativo (e-mail, Discord) e backup de lista de subscritores.

## Checklist de Grupos e Canais
- [ ] Todos os grupos/canais criados com privacidade adequada; nenhum link público sem controlo.
- [ ] Bot adicionado como administrador em todos os grupos com permissões de apagar mensagens, banir, e adicionar/remover membros.
- [ ] Regras de conduta fixadas no topo de cada grupo; mensagem de boas-vindas automática com regras.
- [ ] Sincronização de acessos executada a cada 6 horas (cron); log de todas as adições/remoções.
- [ ] Moderadores humanos treinados em políticas de moderação; nenhuma ação arbitrária sem registo.
- [ ] Filtros automáticos de spam, links não autorizados, e dados sensíveis ativos e testados.
- [ ] Canal de contingência (e-mail ou Discord) configurado para caso de banimento do Telegram.
- [ ] Métrica de saúde da comunidade: mensagens/dia, ratio de spam, tempo médio de resposta de moderadores.

## Links Cruzados
- [[19_Telegram_System/BOT_TELEGRAM_CONFIG]] - Configuração do bot que gere os grupos.
- [[19_Telegram_System/COMANDOS_BOT]] - Comandos que interagem com a gestão de grupos.
- [[16_Compliance/DISCLAIMERS]] - Disclaimer presente nas regras do grupo.
- [[17_Legal/TERMS_OF_SERVICE]] - Cláusulas de propriedade intelectual que proíbem partilha.
