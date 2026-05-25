---
ID: LEG-001
tags: #status/active #legal #terms #contract #consumer
---

# Termos de Serviço

## Objetivo
Definir o contrato vinculativo entre o prestador do serviço de informação quantitativa NBA e os subscritores, estabelecendo direitos, obrigações, limitações de responsabilidade, condições de pagamento, rescisão e resolução de litígios. Os Termos de Serviço (ToS) constituem a base jurídica da relação comercial e devem ser redigidos de forma a serem exequíveis nas jurisdições de operação, com especial atenção às normas de defesa do consumidor da UE (Diretiva 2011/83/UE).

## O que faz
- Estabelece a natureza do serviço: prestação de informação e análise quantitativa desportiva, sem qualquer garantia de resultado ou lucro.
- Define as modalidades de subscrição (mensal, trimestral, anual), preços, renovação automática, condições de reembolso e política de cancelamento.
- Limita a responsabilidade do prestador por perdas financeiras resultantes da utilização das informações (cláusula de exoneração de responsabilidade por decisões de apostas).
- Estabelece propriedade intelectual dos modelos, dados e conteúdos; proíbe partilha, revenda ou engenharia reversa.
- Define cláusulas de eleição de foro, lei aplicável (Rome I) e mecanismos alternativos de resolução de litígios (RAL).

## Porque existe
- **Segurança Jurídica**: Sem um contrato claro, o prestador está exposto a litígios por prestação de serviço defeituoso, responsabilidade por danos indiretos, e exigências de reembolso fora de prazo.
- **Defesa do Consumidor**: A legislação da UE impõe informações pré-contratuais obrigatórias (art. 5º e 6º da Diretiva 2011/83/UE). A ausência destas informações invalida cláusulas e expõe a coimas.
- **Propriedade Intelectual**: Os modelos quantitativos e os dados compilados constituem know-how valioso. Sem cláusulas de confidencialidade e não concorrência, um subscritor pode replicar o serviço.
- **Gestão de Expectativas**: Um subscritor que entenda claramente que o serviço é informação pura, e não "dicas vencedoras", tem menor probabilidade de litigar por resultados negativos.

## Implementação / Pseudocódigo
```python
class TermsOfServiceManager:
    def __init__(self):
        self.versoes = {
            "v1.0": {"data_publicacao": "2024-01-01", "data_vigencia": "2024-06-30", "status": "ARQUIVADA"},
            "v1.1": {"data_publicacao": "2024-07-01", "data_vigencia": None, "status": "ATIVA"}
        }
        self.clausulas_obrigatorias = [
            "natureza_servico",
            "limitacao_responsabilidade",
            "propriedade_intelectual",
            "precos_pagamento",
            "direito_livre_resolucao",
            "rescisao",
            "lei_aplicavel_foro",
            "alteracoes_termos",
            "privacidade_dados",
            "comportamento_proibido"
        ]
        self.limite_responsabilidade_eur = 250  # Montante máximo reembolsável em litígio

    def gerar_contrato_personalizado(self, subscritor):
        base = self.carregar_template("terms_of_service_base_v1.1.md")
        variaveis = {
            "subscritor_id": subscritor.id,
            "data_contratacao": datetime.utcnow().isoformat(),
            "jurisdicao": subscritor.pais_residencia,
            "plano": subscritor.plano,
            "preco_mensal": subscritor.preco_mensal,
            "moeda": subscritor.moeda,
            "limite_responsabilidade": self.calcular_limite_responsabilidade(subscritor),
            "direito_resolucao_dias": self.obter_prazo_resolucao(subscritor.pais_residencia),
            "lei_aplicavel": self.obter_lei_aplicavel(subscritor.pais_residencia),
            "foro": self.obter_foro(subscritor.pais_residencia)
        }
        return base.render(**variaveis)

    def calcular_limite_responsabilidade(self, subscritor):
        # Em conformidade com jurisprudência europeia, a limitação não pode ser manifestamente desproporcionada
        if subscritor.pais_residencia in ["PT", "ES", "IT", "FR"]:
            return min(subscritor.total_pago_12m, self.limite_responsabilidade_eur)
        return self.limite_responsabilidade_eur

    def obter_prazo_resolucao(self, pais):
        # Diretiva 2011/83/UE: 14 dias para bens digitais NÃO prestados com consentimento
        # Se o subscritor consentir explícito na prestação imediata, perde o direito
        return 14 if pais in self.eee else 30  # Alguns países oferecem prazos mais longos por lei local

    def notificar_alteracao_termos(self, nova_versao):
        subscritores_ativos = self.db.listar_subscritores_ativos()
        for sub in subscritores_ativos:
            self.email.enviar(
                para=sub.email,
                assunto="Alteração aos Termos de Serviço - Ação Necessária",
                corpo=self.renderizar_notificacao_alteracao(sub, nova_versao),
                obrigatorio=True
            )
            self.db.registrar_notificacao(sub.id, "ALTERACAO_TOS", nova_versao)
        
        # Se o subscritor não aceitar em 30 dias, a conta é suspensa
        self.agendar_suspensao_nao_aceites(nova_versao, dias=30)

    def verificar_aceitacao_atual(self, subscritor_id):
        aceitacao = self.db.consultar_ultima_aceitacao(subscritor_id)
        versao_ativa = self.versoes["v1.1"]  # ou versão ativa dinâmica
        if not aceitacao or aceitacao["versao"] != versao_ativa:
            return {"aceite": False, "versao_requerida": versao_ativa, "acao": "BLOQUEAR_SINAIS_ATE_ACEITACAO"}
        return {"aceite": True}
```

## Thresholds e Tabelas

| Cláusula | Jurisdição | Obrigatória | Penalidade em Falta | Frequência Revisão |
|----------|-----------|-------------|--------------------|--------------------|
| Informação pré-contratual | UE (Dir. 2011/83/UE) | Sim | Coima até €10.000; invalidade de cláusulas | Semestral |
| Direito de livre resolução | UE (art. 9º) | Sim | Reembolso forçado + juros + custas | Anual |
| Limitação de responsabilidade | PT (Código Civil art. 809º) | Condicional | Nulidade da cláusula se manifestamente desproporcionada | Anual |
| Eleição de foro | Bruxelas I bis | Recomendada | Litígio em foro desfavorável do consumidor | Anual |
| Lei aplicável | Rome I | Sim | Aplicação de lei estrangeira menos favorável | Anual |
| Propriedade intelectual | PT / EU | Sim | Ação de violação de know-how | Semestral |

| Plano de Subscrição | Prazo Mínimo | Renovação | Reembolso (DLR) | Reembolso (Pós-DLR) |
|--------------------|-------------|-----------|-----------------|---------------------|
| Mensal | 1 mês | Automática mensal | 14 dias (se não consentiu prestação) | Prorata restante (a critério) |
| Trimestral | 3 meses | Automática trimestral | 14 dias | Não reembolsável após 14 dias |
| Anual | 12 meses | Automática anual | 14 dias | Não reembolsável após 14 dias; upgrade possível |

## Riscos
- **Risco de Nulidade de Cláusulas**: Cláusulas de limitação de responsabilidade ou de eleição de foro podem ser declaradas nulas por tribunais de consumo se consideradas abusivas (Diretiva 93/13/CEE).
- **Risco de Mudança Legislativa**: Alterações na lei do consumidor (ex: novo regime de subscrições digitais na UE) podem invalidar termos existentes e exigir renegociação com subscritores ativos.
- **Risco de Litígio em Massa**: Se uma versão dos ToS tiver uma falha sistemática (ex: omissão de direito de resolução), pode gerar ação coletiva ou reclamações massivas.
- **Risco de Propriedade Intelectual**: Subscritores podem argumentar que os modelos são "factos" desportivos não protegidos; é necessário clareza sobre a proteção da metodologia, não dos dados brutos.

## Checklist de Termos de Serviço
- [ ] Template de ToS validado por advogado especializado em direito do consumidor e do jogo em cada jurisdição ativa.
- [ ] Registo de aceitação eletrónica com timestamp, IP, user-agent e hash do texto aceite (prova de consentimento).
- [ ] Versão ativa dos ToS disponível publicamente no site e referenciada em todas as faturas.
- [ ] Notificação por e-mail de alterações materiais com prazo de 30 dias para aceitação; suspensão automática em caso de não resposta.
- [ ] Cláusula de resolução extrajudicial (RAL / mediação) para litígios até €5.000.
- [ ] Tradução certificada dos ToS para EN, ES, DE, FR (jurisdições principais).
- [ ] Revisão semestral de preços, planos e condições de reembolso por evolução do mercado e concorrência.
- [ ] Integração com [[16_Compliance/DISCLAIMERS]] — o disclaimer é incorporado nos ToS por referência.

## Links Cruzados
- [[17_Legal/PRIVACY_POLICY]] - Política de privacidade referenciada nos ToS.
- [[17_Legal/SUBSCRICAO_AGREEMENT]] - Contrato específico de subscrição que deriva destes ToS.
- [[16_Compliance/REGULAMENTACAO_PT]] - Base regulatória que impõe informações pré-contratuais.
- [[16_Compliance/REGULAMENTACAO_EU]] - Diretiva 2011/83/UE e cláusulas de defesa do consumidor.
- [[25_SOPs/SOP-007_Onboarding_Subscritor]] - Procedimento que garante aceitação dos ToS.
- [[25_SOPs/SOP-008_Offboarding_Subscritor]] - Rescisão em conformidade com os ToS.
