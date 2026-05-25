---
ID: CMP-004
tags: #status/active #compliance #kyc #aml #fraud #identity
---

# Know Your Customer (KYC) e Anti-Money Laundering (AML)

## Objetivo
Implementar um programa robusto de identificação e verificação da identidade dos subscritores (KYC) e de deteção/prevenção de atividades suspeitas que possam constituir branqueamento de capitais ou financiamento do terrorismo (AML), alinhado com a Diretiva UE 2018/843 (5ª Diretiva AML/CFT) e a legislação portuguesa (Lei 83/2017 e Portaria 252/2012, com as alterações da Lei 97/2020). Embora o serviço seja de informação, a receita de subscrições e a natureza do setor (jogo) justificam precauções AML elevadas.

## O que faz
- Estabelece níveis de due diligence (SDD - Simplified, CDD - Customer, EDD - Enhanced) consoante o perfil de risco do subscritor.
- Define documentação obrigatória por nível: e-mail + telefone (SDD); documento de identidade + comprovativo de morada + selfie (CDD); fonte de fundos + PEP screening + proveniência de riqueza (EDD).
- Integra com serviços de verificação de identidade (Onfido, Jumio, Trulioo) e bases de dados PEP/sanções (Refinitiv World-Check, Dow Jones Risk & Compliance).
- Implementa monitorização contínua (ongoing monitoring) de transações de subscrição e padrões de uso para deteção de atividade suspeita.

## Porque existe
- **Obrigação Legal Indireta**: A 5ª Diretiva AML alargou o âmbito a prestadores envolvidos em atividades virtuais; embora serviços de informação não estejam explicitamente incluídos, a intermediação de pagamentos via gateway (Stripe, Paypal) pode impor obrigações contratuais de AML.
- **Risco Reputacional**: Subscritores que utilizam o serviço para "mascarar" perdas de fontes ilícitas ou para integrar fundos através de reembolsos fraudulentos comprometem a viabilidade do negócio.
- **Risco de Congelamento de Contas**: Gateways de pagamento (Stripe, Adyen) suspendem contas merchant com chargeback rates >1% ou sem KYC documentado.
- **Risco Penal**: Art. 368º e seguintes do Código Penal Português (branqueamento de capitais); responsabilidade do gestor se houve negligência grave na identificação.

## Implementação / Pseudocódigo
```python
class KYCAMLProgram:
    def __init__(self):
        self.niveis_due_diligence = {
            "SDD": {"limite_eur": 0, "docs": ["email_verificado", "telefone_verificado"]},
            "CDD": {"limite_eur": 250, "docs": ["doc_identidade", "comprovativo_morada", "selfie_liveness"]},
            "EDD": {"limite_eur": 2500, "docs": ["fonte_fundos", "pep_screening", "proveniencia_riqueza"]}
        }
        self.pep_provider = PEPWorldCheckClient(api_key=os.environ["WORLDCHECK_API_KEY"])
        self.id_provider = OnfidoClient(api_key=os.environ["ONFIDO_API_KEY"])
        self.suspicious_thresholds = {
            "multiplas_contas_mesmo_ip": 3,
            "frequencia_pagamentos_irregular": ">5_pagamentos_24h",
            "jurisdicao_risco": ["HK", "AE", "RU", "BY"],  # Hong Kong, UAE, Russia, Belarus (exemplos)
            "chargeback_rate_mensal": 0.01
        }

    def avaliar_risco_subscritor(self, subscritor):
        score = 0
        fatores = []
        
        if subscritor.pais_residencia in self.suspicious_thresholds["jurisdicao_risco"]:
            score += 40
            fatores.append("JURISDICAO_ALTO_RISCO")
        
        if subscritor.total_pago_eur > self.niveis_due_diligence["EDD"]["limite_eur"]:
            score += 30
            fatores.append("EXPOSICAO_FINANCEIRA_ELEVADA")
        
        contas_mesmo_ip = self.db.contar_contas_por_ip(subscritor.ip_registo)
        if contas_mesmo_ip >= self.suspicious_thresholds["multiplas_contas_mesmo_ip"]:
            score += 20
            fatores.append("MULTIPLAS_CONTAS_IP")
        
        if self.pep_provider.check(subscritor.nome_completo, subscritor.data_nascimento):
            score += 50
            fatores.append("PEP_DETECTADO")
        
        nivel = "SDD" if score < 30 else "CDD" if score < 60 else "EDD"
        return {"score": score, "fatores": fatores, "nivel_diligence": nivel}

    def submeter_verificacao(self, subscritor_id, documentos):
        subscritor = self.db.obter(subscritor_id)
        risco = self.avaliar_risco_subscritor(subscritor)
        
        resultado = self.id_provider.verificar(
            documento=documentos["doc_identidade"],
            comprovativo=documentos.get("comprovativo_morada"),
            selfie=documentos.get("selfie")
        )
        
        if resultado["status"] == "CLEAR" and risco["nivel_diligence"] != "EDD":
            self.db.atualizar_kyc(subscritor_id, "VERIFICADO", risco["nivel_diligence"], resultado["report_id"])
            return {"status": "APROVADO", "nivel": risco["nivel_diligence"]}
        elif risco["nivel_diligence"] == "EDD":
            self.db.atualizar_kyc(subscritor_id, "PENDENTE_EDD", "EDD", None)
            self.alertar_compliance_officer(subscritor_id, risco)
            return {"status": "PENDENTE_EDD", "acoes_requeridas": self.niveis_due_diligence["EDD"]["docs"]}
        else:
            self.db.atualizar_kyc(subscritor_id, "REJEITADO", risco["nivel_diligence"], resultado["report_id"])
            return {"status": "REJEITADO", "motivo": resultado["razao_rejeicao"]}

    def monitoramento_continuo(self):
        for subscritor in self.db.subscritores_ativos():
            transacoes_24h = self.db.contar_transacoes(subscritor.id, horas=24)
            if transacoes_24h > 5:
                self.gerar_alerta_suspicious("FREQUENCIA_PAGAMENTOS_ANORMAL", subscritor.id, {"transacoes_24h": transacoes_24h})
            
            if subscritor.chargeback_rate_mensal > self.suspicious_thresholds["chargeback_rate_mensal"]:
                self.gerar_alerta_suspicious("CHARGEBACK_ELEVADO", subscritor.id, {"rate": subscritor.chargeback_rate_mensal})
```

## Thresholds e Tabelas

| Nível de Due Diligence | Limite Acumulado Subscrições | Documentação Obrigatória | Frequência Revisão | Ação em Falta |
|-----------------------|------------------------------|-------------------------|-------------------|---------------|
| SDD | €0 - €250 | E-mail verificado, telefone verificado | Automática | Bloqueio de upgrade |
| CDD | €250 - €2.500 | Documento identidade (passaporte/CC), comprovativo morada < 3 meses, selfie com liveness | Anual | Suspensão de sinais |
| EDD | > €2.500 | Tudo do CDD + fonte de fundos (declaração + documento), PEP screening, proveniência de riqueza | Semestral | Congelamento de conta, reporte interno |

| Indicador de Risco AML | Threshold | Classificação | Resposta Automática |
|------------------------|-----------|-------------|---------------------|
| Múltiplas contas mesmo IP | ≥ 3 contas | Médio | Requer verificação adicional |
| PEP detectado | Qualquer match | Alto | EDD obrigatório, reporte CO |
| Sanções ONU/UE | Qualquer match | Crítico | Bloqueio imediato, não abrir conta |
| Pagamentos em 24h | > 5 transações | Médio | Alerta + revisão manual |
| Chargeback rate mensal | > 1% | Alto | Suspensão pagamentos, revisão |
| País de risco (FATF grey/black list) | Residência ou pagamento | Alto | EDD ou bloqueio |

## Riscos
- **Risco de Falso Negativo**: Tecnologia de verificação de identidade não é infalível; documentos sofisticados podem passar se não houver revisão humana aleatória.
- **Risco de Discriminação Algorítmica**: Screening automatizado de PEP/sanções pode gerar falsos positivos discriminatórios (ex: nomes árabes comuns correspondem a listas de sanções por similaridade fonética).
- **Risco de Dados Biométricos**: Armazenamento de selfies e documentos de identidade exige medidas de segurança especiais (art. 9º GDPR); vazamento é catastrófico.
- **Risco de Gateway**: Se o chargeback rate exceder 1%, Stripe/PayPal podem reter fundos por 90-180 dias, comprometendo a tesouraria.

## Checklist KYC/AML
- [ ] Política KYC/AML escrita e aprovada pelo gestor de compliance (revisão anual).
- [ ] Contrato com fornecedor de verificação de identidade (Onfido/Jumio/Trulioo) com DPA (Data Processing Addendum) assinado.
- [ ] Subscrição ativa a base de dados PEP/sanções (World-Check, Dow Jones, ou LexisNexis).
- [ ] Pipeline de KYC integrado no onboarding com webhook assíncrono (subscritor não fica bloqueado à espera, mas não recebe sinais até aprovação).
- [ ] Revisão manual de 10% das verificações CDD aprovadas automaticamente (amostragem de controlo).
- [ ] Registo de todas as decisões KYC com justificação, timestamp e identificação do agente (humano ou sistema).
- [ ] Formação anual do pessoal de operações em deteção de atividade suspeita e obrigações de reporte.
- [ ] Relatório anual de atividade suspeita (RAS) preparado para envio à Unidade de Informação Financeira (UIF/BdP) se aplicável.

## Links Cruzados
- [[16_Compliance/REGULAMENTACAO_PT]] - Lei 83/2017 e obrigações portuguesas AML.
- [[16_Compliance/REGULAMENTACAO_EU]] - 5ª Diretiva AML/CFT transposição.
- [[16_Compliance/AUDIT_TRAIL_COMPLIANCE]] - Registo imutável de decisões KYC.
- [[17_Legal/PRIVACY_POLICY]] - Tratamento de dados biométricos e de identidade.
- [[34_Security/SECRETS_MANAGEMENT]] - Gestão segura de API keys dos fornecedores KYC.
