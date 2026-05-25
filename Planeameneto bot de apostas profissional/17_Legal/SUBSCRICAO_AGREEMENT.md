---
ID: LEG-004
tags: #status/active #legal #subscription #contract #billing
---

# Contrato de Subscrição

## Objetivo
Formalizar a relação comercial individual entre o prestador do serviço de informação quantitativa NBA e cada subscritor, especificando o plano contratado, o preço, a periodicidade, os serviços incluídos, as exclusões, os direitos de resolução, e as condições de suspensão e rescisão. O Contrato de Subscrição é o instrumento executivo que deriva dos [[17_Legal/TERMS_OF_SERVICE]] e serve como prova pericial em litígios de cobrança ou prestação de serviço.

## O que faz
- Gera um contrato individual por subscritor no momento do checkout, com todas as variáveis personalizadas: plano, preço, moeda, data de início, data de renovação, método de pagamento, e descontos aplicados.
- Integra com o gateway de pagamento (Stripe / PayPal) para garantir que o contrato só é considerado ativo após confirmação de pagamento ou autorização de cobrança recorrente.
- Regista automaticamente o contrato no sistema de documentação e no [[16_Compliance/AUDIT_TRAIL_COMPLIANCE]] com hash e timestamp.
- Garante que o subscritor tenha acesso permanente ao seu contrato no dashboard ("Os Meus Documentos").

## Porque existe
- **Prova Contratual**: Em litígio, o contrato individual é mais forte do que os termos gerais, pois demonstra que aquele subscritor específico aceitou aqueles termos específicos naquela data.
- **Cobrança e Reembolso**: O contrato define claramente o que foi pago, quando, e por que serviço, evitando chargebacks por "produto não reconhecido".
- **Gestão de Planos**: Subscritores podem fazer upgrade, downgrade, ou adicionar add-ons (ex: acesso a múltiplos desportos). Sem contrato versionado por alteração, a gestão torna-se caótica.
- **Revisão de Preços**: O contrato inclui cláusulas de reajuste que permitem alterar preços com pré-aviso, protegendo a sustentabilidade do negócio.

## Implementação / Pseudocódigo
```python
class SubscriptionAgreementManager:
    def __init__(self):
        self.planos = {
            "ESSENCIAL": {"preco_mensal_eur": 49.00, "sinais_dia": 1, "mercados": ["spread", "total"], "suporte": "email_48h"},
            "PRO": {"preco_mensal_eur": 99.00, "sinais_dia": 3, "mercados": ["spread", "total", "moneyline", "player_props"], "suporte": "telegram_priority"},
            "INSTITUCIONAL": {"preco_mensal_eur": 499.00, "sinais_dia": 5, "mercados": "todos", "suporte": "dedicado", "api": True, "white_label": True}
        }
        self.ciclo_faturacao = ["mensal", "trimestral", "anual"]
        self.descontos_ciclo = {"trimestral": 0.10, "anual": 0.20}

    def criar_contrato(self, subscritor_id, plano_codigo, ciclo, codigo_desconto=None):
        subscritor = self.db.obter_subscritor(subscritor_id)
        plano = self.planos[plano_codigo]
        
        preco_base = plano["preco_mensal_eur"]
        if ciclo == "trimestral":
            preco_ciclo = preco_base * 3 * (1 - self.descontos_ciclo["trimestral"])
        elif ciclo == "anual":
            preco_ciclo = preco_base * 12 * (1 - self.descontos_ciclo["anual"])
        else:
            preco_ciclo = preco_base
        
        desconto = self.aplicar_codigo_desconto(codigo_desconto, preco_ciclo) if codigo_desconto else 0
        preco_final = max(0, preco_ciclo - desconto)
        
        contrato = {
            "id": f"SUB-{subscritor_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "subscritor_id": subscritor_id,
            "plano": plano_codigo,
            "ciclo": ciclo,
            "preco_base_mensal_eur": preco_base,
            "preco_ciclo_eur": preco_ciclo,
            "desconto_aplicado_eur": desconto,
            "preco_final_eur": preco_final,
            "moeda_faturacao": subscritor.moeda_preferida or "EUR",
            "data_inicio": datetime.utcnow().isoformat(),
            "data_renovacao": self.calcular_data_renovacao(datetime.utcnow(), ciclo),
            "metodo_pagamento": subscritor.metodo_pagamento,
            "gateway_id": None,  # preenchido após confirmação Stripe
            "status": "PENDENTE_PAGAMENTO",
            "termos_aceites_versao": self.obter_versao_tos_ativa(),
            "timestamp_aceitacao": datetime.utcnow().isoformat()
        }
        
        self.db.inserir("contratos_subscricao", contrato)
        self.audit_trail.registrar("CONTRATO", "contrato", contrato["id"], "CREATE", None, contrato, f"user:{subscritor_id}")
        return contrato

    def confirmar_pagamento(self, contrato_id, gateway_payment_id):
        contrato = self.db.obter_contrato(contrato_id)
        self.db.atualizar_contrato(contrato_id, {"status": "ATIVO", "gateway_id": gateway_payment_id})
        self.audit_trail.registrar("CONTRATO", "contrato", contrato_id, "PAGAMENTO_CONFIRMADO", contrato, {"status": "ATIVO", "gateway_id": gateway_payment_id}, "sistema:stripe_webhook")
        self.telegram.notificar_subscritor(contrato["subscritor_id"], "Pagamento confirmado. Acesso ativado.")
        return {"status": "ATIVO"}

    def processar_upgrade(self, contrato_id, novo_plano):
        contrato = self.db.obter_contrato(contrato_id)
        if contrato["status"] != "ATIVO":
            return {"erro": "UPGRADE_INVALIDO", "motivo": "Contrato não está ativo"}
        
        # Criar contrato novo com prorata do antigo
        dias_restantes = (contrato["data_renovacao"] - datetime.utcnow()).days
        valor_credito = (contrato["preco_final_eur"] / self.dias_ciclo(contrato["ciclo"])) * dias_restantes
        
        novo_contrato = self.criar_contrato(contrato["subscritor_id"], novo_plano, contrato["ciclo"])
        novo_contrato["credito_upgrade_eur"] = valor_credito
        novo_contrato["preco_final_eur"] = max(0, novo_contrato["preco_final_eur"] - valor_credito)
        
        self.db.atualizar_contrato(contrato_id, {"status": "UPGRADED", "contrato_sucessor": novo_contrato["id"]})
        return novo_contrato

    def calcular_data_renovacao(self, data_inicio, ciclo):
        if ciclo == "mensal":
            return data_inicio + relativedelta(months=1)
        elif ciclo == "trimestral":
            return data_inicio + relativedelta(months=3)
        elif ciclo == "anual":
            return data_inicio + relativedelta(years=1)

    def dias_ciclo(self, ciclo):
        return {"mensal": 30, "trimestral": 90, "anual": 365}[ciclo]
```

## Thresholds e Tabelas

| Plano | Preço Mensal (EUR) | Sinais/Dia | Mercados | Suporte | API | White Label |
|-------|-------------------|------------|----------|---------|-----|-------------|
| ESSENCIAL | €49 | 1 | Spread, Total | E-mail (48h) | Não | Não |
| PRO | €99 | 3 | Spread, Total, ML, Player Props | Telegram Priority | Não | Não |
| INSTITUCIONAL | €499 | 5 | Todos + Derivados | Dedicado | Sim | Sim |

| Ciclo | Desconto | Faturação | Renovação Automática | Prazo Cancelamento |
|-------|----------|-----------|---------------------|--------------------|
| Mensal | 0% | Mensal | Sim, aviso 7 dias antes | 7 dias antes da renovação |
| Trimestral | 10% | Trimestral antecipada | Sim, aviso 7 dias antes | 7 dias antes da renovação |
| Anual | 20% | Anual antecipada | Sim, aviso 14 dias antes | 14 dias antes da renovação |

| Situação | Política de Reembolso | Nota |
|----------|----------------------|------|
| Cancelamento no prazo DLR (14 dias) | 100% do valor pago | Se serviço não prestado com consentimento expresso |
| Cancelamento após DLR, antes de 50% do ciclo | 50% prorata | A critério do gestor; exige justificação |
| Cancelamento após 50% do ciclo | Não reembolsável | Salvo caso de força maior ou falha grave do serviço |
| Upgrade mid-ciclo | Crédito prorata no novo contrato | Diferença cobrada ou creditada automaticamente |
| Downgrade | Efetivo na próxima renovação | Não há reembolso parcial no ciclo atual |

## Riscos
- **Risco de Chargeback**: Subscritores insatisfeitos que não conseguem cancelar facilmente recorrem ao chargeback no gateway. Chargeback rates > 1% suspendem a conta Stripe.
- **Risco de Renovação Não Comunicada**: Se o aviso de renovação automática não for enviado no prazo, o subscritor pode alegar cobrança não autorizada.
- **Risco de Promoções Ilegais**: Códigos de desconto excessivos ou permanentes podem criar expectativas de preço que inviabilizam o modelo de negócio.
- **Risco de Planos Confusos**: Subscritores que compram "Essencial" e acreditam ter acesso a Player Props geram litígios de "serviço não conforme".

## Checklist do Contrato de Subscrição
- [ ] Template de contrato validado por advogado e sincronizado com a versão ativa dos [[17_Legal/TERMS_OF_SERVICE]].
- [ ] Geração automática de contrato em PDF (assinado digitalmente ou com hash de integridade) disponível no dashboard.
- [ ] Integração de webhook Stripe para confirmação automática de pagamento e ativação.
- [ ] Mecanismo de cobrança recorrente com retentativa em falha (dia 1: tentativa; dia 3: aviso; dia 7: aviso final; dia 10: suspensão).
- [ ] Comunicação obrigatória de renovação: 7 dias (mensal/trimestral) ou 14 dias (anual) antes da cobrança.
- [ ] Log de todas as alterações contratuais (upgrade, downgrade, cancelamento) no [[16_Compliance/AUDIT_TRAIL_COMPLIANCE]].
- [ ] Relatório mensal de MRR (Monthly Recurring Revenue), churn rate, LTV, e CAC por plano.

## Links Cruzados
- [[17_Legal/TERMS_OF_SERVICE]] - Base contratual geral.
- [[17_Legal/PRIVACY_POLICY]] - Tratamento de dados no contexto do contrato.
- [[16_Compliance/REGULAMENTACAO_EU]] - Diretiva 2011/83/UE e direitos do consumidor.
- [[25_SOPs/SOP-007_Onboarding_Subscritor]] - Procedimento de criação de contrato.
- [[25_SOPs/SOP-008_Offboarding_Subscritor]] - Cancelamento e rescisão.
- [[35_Financial_Tracking/PLANO_CONTAS]] - Classificação contabilística das receitas de subscrição.
