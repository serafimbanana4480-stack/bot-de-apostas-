---
ID: LEG-002
tags: #status/active #legal #privacy #gdpr #lgpd #data-protection
---

# Política de Privacidade

## Objetivo
Documentar de forma transparente, acessível e juridicamente sólida todas as operações de tratamento de dados pessoais efetuadas pelo sistema de value betting NBA, em conformidade com o Regulamento Geral de Proteção de Dados (GDPR - Reg. UE 2016/679), a Lei n.º 58/2019 (LGPD portuguesa), e as legislações nacionais dos Estados-Membros onde o serviço opera. A política deve funcionar tanto como instrumento de informação ao titular dos dados quanto como prova de accountability perante as autoridades de controlo.

## O que faz
- Identifica o responsável pelo tratamento (controlador), o representante na UE (se aplicável), e o Data Protection Officer (DPO).
- Cataloga todas as categorias de dados pessoais tratados: identificação, contacto, financeiros, comportamentais (dados de jogo), técnicos (logs, IP, device fingerprint), e biométricos (se KYC com selfie).
- Detalha finalidades do tratamento, base jurídica de cada uma (art. 6º GDPR), períodos de conservação, e destinatários (internos, processadores, terceiros).
- Descreve os direitos do titular (acesso, retificação, apagamento, portabilidade, oposição, limitação, não-profilamento) e os meios de exercício.
- Informa sobre transferências internacionais de dados, medidas de segurança, e obrigações de notificação de violação.

## Porque existe
- **Obrigação Legal**: Art. 12º a 14º do GDPR impõem informação concisa, transparente, inteligível e de fácil acesso. A falta ou inadequação da política é infração punível com coimas até €20M ou 4% do CA.
- **Confiança do Subscritor**: Em serviços onde são tratados dados sensíveis sobre comportamento financeiro e de jogo, a transparência é fator crítico de conversão e retenção.
- **Due Diligence de Parceiros**: Fornecedores de pagamento (Stripe), plataformas de análise (Google Analytics), e serviços de identidade (Onfido) exigem política de privacidade atualizada como condição de parceria.
- **Defesa em Litígio**: Se um subscritor alegar tratamento ilícito, a política de privacidade e o registo do seu consentimento constituem prova de conformidade.

## Implementação / Pseudocódigo
```python
class PrivacyPolicyEngine:
    def __init__(self):
        self.controlador = {
            "nome": "[Entidade Responsavel] LDA",
            "morada": "[Morada fiscal em Portugal ou UE]",
            "nipc": "[NIPC]",
            "email_dpo": "dpo@[dominio].pt",
            "telefone": "+351 [numero]"
        }
        self.categorias_dados = {
            "identificacao": {"exemplos": ["nome", "data_nascimento", "nif"], "base_juridica": "CONTRATO", "retencao": "10_anos"},
            "contacto": {"exemplos": ["email", "telefone", "chat_id_telegram"], "base_juridica": "CONTRATO", "retencao": "10_anos"},
            "financeiros": {"exemplos": ["historico_pagamentos", "dados_cartao_tokenizado"], "base_juridica": "CONTRATO", "retencao": "10_anos"},
            "comportamentais": {"exemplos": ["historico_apostas_recomendadas", "stake", "odd", "resultado"], "base_juridica": "CONSENTIMENTO", "retencao": "3_anos_pos_inatividade"},
            "tecnicos": {"exemplos": ["ip", "user_agent", "device_fingerprint", "logs_acesso"], "base_juridica": "INTERESSE_LEGITIMO", "retencao": "2_anos"},
            "biometricos": {"exemplos": ["selfie", "documento_identidade"], "base_juridica": "CONSENTIMENTO_EXPLICITO", "retencao": "5_anos_pos_relacao"}
        }
        self.direitos_titular = {
            "acesso": self.gerar_formulario("form_acesso_dados.md"),
            "retificacao": self.gerar_formulario("form_retificacao.md"),
            "apagamento": self.gerar_formulario("form_apagamento.md"),
            "portabilidade": self.gerar_formulario("form_portabilidade.md"),
            "oposicao": self.gerar_formulario("form_oposicao.md"),
            "limitacao": self.gerar_formulario("form_limitacao.md"),
            "nao_decisao_automatizada": self.gerar_formulario("form_recusa_perfil.md")
        }

    def processar_pedido_titular(self, subscritor_id, tipo_pedido):
        pedido = {
            "subscritor_id": subscritor_id,
            "tipo": tipo_pedido,
            "data_rececao": datetime.utcnow().isoformat(),
            "prazo_resposta_dias": 30,
            "data_limite_resposta": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "status": "RECEBIDO"
        }
        self.db.inserir("pedidos_titular", pedido)
        
        if tipo_pedido == "apagamento":
            return self.executar_direito_apagamento(subscritor_id, pedido)
        elif tipo_pedido == "portabilidade":
            return self.executar_direito_portabilidade(subscritor_id, pedido)
        elif tipo_pedido == "acesso":
            return self.executar_direito_acesso(subscritor_id, pedido)
        else:
            return self.encaminhar_dpo(pedido)

    def executar_direito_apagamento(self, subscritor_id, pedido):
        # Verificar obrigacoes legais de retencao (fiscal, contratual)
        obrigacoes = self.verificar_obrigacoes_retencao(subscritor_id)
        if obrigacoes:
            # Pseudonimizar em vez de apagar; manter dados fiscais minimos
            self.pseudonimizar_subscritor(subscritor_id, excecoes=obrigacoes)
            self.db.atualizar_pedido(pedido["id"], "PARCIALMENTE_CUMPRIDO", "Dados pseudonimizados; retidos apenas dados fiscais obrigatórios por lei.")
        else:
            self.eliminar_dados_subscritor(subscritor_id)
            self.db.atualizar_pedido(pedido["id"], "CUMPRIDO", "Todos os dados eliminados.")
        
        return {"status": "processado", "detalhe": self.db.consultar_pedido(pedido["id"])}

    def executar_direito_portabilidade(self, subscritor_id, pedido):
        dados = self.extrair_dados_subscritor(subscritor_id)
        arquivo_json = json.dumps(dados, ensure_ascii=False, indent=2)
        arquivo_csv = self.converter_para_csv(dados)
        
        self.enviar_email(
            para=self.db.obter_email(subscritor_id),
            assunto="Portabilidade de Dados - [Entidade]",
            anexos=[("dados.json", arquivo_json), ("dados.csv", arquivo_csv)]
        )
        self.db.atualizar_pedido(pedido["id"], "CUMPRIDO", "Dados enviados em formato JSON e CSV.")
        return {"status": "processado"}

    def verificar_obrigacoes_retencao(self, subscritor_id):
        excecoes = []
        transacoes = self.db.obter_transacoes(subscritor_id)
        if any(t["ano"] >= datetime.utcnow().year - 10 for t in transacoes):
            excecoes.append("dados_fiscais_10anos")
        if self.db.subscritor_tem_litigio_aberto(subscritor_id):
            excecoes.append("litigio_pendente")
        return excecoes
```

## Thresholds e Tabelas

| Categoria de Dados | Finalidade | Base Jurídica | Conservação | Pode Ser Apagado |
|--------------------|-----------|---------------|-------------|------------------|
| Identificação | Contrato, faturação, KYC | Contrato / Obrigação legal | 10 anos | Não (obrigação fiscal) |
| Contacto | Comunicação, entrega de sinais | Contrato | 10 anos | Não (fiscal) |
| Financeiros | Faturação, contabilidade, AML | Obrigação legal | 10 anos | Não |
| Comportamentais (jogo) | Análise de performance, melhoria de modelo | Consentimento | 3 anos após inatividade | Sim |
| Técnicos | Segurança, debugging, prevenção de fraude | Interesse legítimo | 2 anos | Sim (após período) |
| Biométricos | Verificação de identidade (KYC) | Consentimento explícito | 5 anos após fim da relação | Sim (se não há litígio) |

| Direito do Titular | Prazo de Resposta | Formato de Entrega | Taxa Pode Ser Cobrada | Verificação Identidade |
|--------------------|-------------------|-------------------|----------------------|------------------------|
| Acesso | 30 dias | JSON + CSV | Não (salvo pedidos manifestamente infundados) | E-mail de confirmação + KYC leve |
| Retificação | 30 dias | Confirmação por e-mail | Não | Sim |
| Apagamento | 30 dias | Confirmação por e-mail | Não | Sim |
| Portabilidade | 30 dias | JSON + CSV | Não | Sim |
| Oposição | Imediata (após verificação) | Confirmação | Não | Sim |
| Limitação | Imediata | Confirmação | Não | Sim |

## Riscos
- **Risco de Base Jurídica Incorreta**: Utilizar "interesse legítimo" para dados comportamentais de jogo pode ser contestado; para esta categoria, o consentimento explícito é mais seguro.
- **Risco de Retenção Excessiva**: Manter dados comportamentais por mais de 3 anos após inatividade expõe a críticas da CNPD/ICO e aumenta o risco em caso de data breach.
- **Risco de Portabilidade Incompleta**: Se o subscritor pedir portabilidade e o sistema não conseguir exportar dados derivados (ex: features calculadas pelo modelo), pode haver reclamação à autoridade de controlo.
- **Risco de Notificação de Violação**: Um breach que exponha dados financeiros ou biométricos obriga à notificação em 72h. Sem processo documentado, a coima é certa.

## Checklist de Política de Privacidade
- [ ] Política validada por advogado especializado em proteção de dados e registada na CNPD (Portugal) ou ICO (UK) conforme sede.
- [ ] DPO nomeado, registado, com contacto visível na política e no site.
- [ ] Inventário de tratamento de dados (registo de atividades) atualizado e alinhado com a política.
- [ ] Formulários de exercício de direitos disponíveis no site e no Telegram (comando /privacidade).
- [ ] Relatório de impacto (DPIA - Data Protection Impact Assessment) realizado para o tratamento de dados comportamentais de jogo e biométricos.
- [ ] Acordos de processamento de dados (DPA) assinados com todos os processadores: VPS, PostgreSQL cloud, Redis cloud, Stripe, Onfido, Telegram, etc.
- [ ] Cláusulas contratuais tipo (SCC) atualizadas (2021) para quaisquer transferências para fora do EEE.
- [ ] Revisão anual da política; notificação de alterações materiais a todos os subscritores ativos.

## Links Cruzados
- [[16_Compliance/REGULAMENTACAO_PT]] - Lei 58/2019 LGPD e especificidades portuguesas.
- [[16_Compliance/REGULAMENTACAO_EU]] - GDPR e transferências internacionais.
- [[16_Compliance/KYC_AML]] - Tratamento de dados biométricos e de identidade.
- [[16_Compliance/AUDIT_TRAIL_COMPLIANCE]] - Registo de pedidos dos titulares e decisões.
- [[34_Security/SECRETS_MANAGEMENT]] - Segurança das chaves de acesso a dados pessoais.
- [[34_Security/POSTGRES_SEGURANCA]] - Encriptação de dados pessoais em repouso.
