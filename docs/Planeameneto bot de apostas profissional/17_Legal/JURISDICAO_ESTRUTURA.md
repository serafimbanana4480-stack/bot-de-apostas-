---
ID: LEG-005
tags: #status/active #legal #jurisdiction #conflict-of-laws #forum
---

# Estruturação da Jurisdição Aplicável

## Objetivo
Definir, documentar e implementar a estrutura jurídica de eleição de foro, lei aplicável e resolução de litígios para o sistema de value betting NBA, de forma a minimizar a incerteza jurídica, reduzir o risco de litígio em foros desfavoráveis, e garantir a exequibilidade de cláusulas contratuais nos 27 Estados-Membros da UE e outras jurisdições de operação. Esta nota serve como referência para a redação de todas as cláusulas contratuais e para a tomada de decisão em processos judiciais ou arbitrais.

## O que faz
- Identifica o país de estabelecimento do prestador (sede fiscal) e os seus efeitos na lei aplicável por defeito (Rome I).
- Analisa a validade e os limites da cláusula de eleição de foro nos contratos com consumidores (Bruxelas I bis, art. 18º a 20º).
- Define a hierarquia de jurisdições: (1) foro dos Tribunais do domicílio do consumidor (imperativo), (2) foro eleito por acordo (subsidiário, apenas para não-consumidores), (3) arbitragem para litígios B2B.
- Estabelece protocolos para notificação judicial internacional, citações, e execução de sentenças (Regulamento Bruxelas I bis para UE; Convenção de Nova Iorque para arbitragem).

## Porque existe
- **Conflito de Leis**: O sistema pode ter subscritores em 20+ países. Sem estruturação da jurisdição, cada litígio pode ser processado na jurisdição do consumidor, com lei local, expondo o prestador a 20+ regimes processuais distintos.
- **Cláusulas Abusivas**: O direito europeu do consumidor considera nulas de pleno direito cláusulas que privam o consumidor do seu foro (Diretiva 93/13/CEE, art. 6º). A estruturação deve respeitar estes limites.
- **Arbitragem B2B**: Para clientes institucionais, a arbitragem (ICC, LCIA, PCA) é mais rápida, confidencial, e neutra. Necessita de cláusula arbitral clara e de renúncia expressa ao foro judicial.
- **Execução de Créditos**: Se um subscritor devedor reside noutro país, a execução de sentença exige mecanismos de reconhecimento (ex: European Payment Order, European Small Claims Procedure).

## Implementação / Pseudocódigo
```python
class JurisdicaoEstrutura:
    def __init__(self):
        self.sede_fiscal = "PT"  # Portugal como exemplo
        self.lei_aplicavel_default = "Lei Portuguesa (Código Civil, Código do Processo Civil)"
        self.foro_consumidor_obrigatorio = True  # True para subscritores individuais
        self.foro_eleito_negociavel = False  # Consumidor não pode negociar foro
        self.arbitragem_b2b = {
            "instituicao": "ICC",
            "sede": "Lisboa",
            "idioma": "Português / Inglês",
            "lei_substancial": "Lei Portuguesa",
            "numero_arbitros": 3,
            "prazo_decisao_meses": 12
        }

    def determinar_foro_aplicavel(self, subscritor, natureza_litigio):
        if subscritor.tipo == "CONSUMIDOR":
            # Art. 18º Bruxelas I bis: consumidor pode ser demandado apenas no foro do seu domicílio
            # O prestador pode ser demandado no foro do domicílio do consumidor
            return {
                "foro_prestador": "Tribunais da Comarca de Lisboa (PT)",
                "foro_consumidor": f"Tribunais do domicílio do consumidor ({subscritor.pais_residencia})",
                "foro_valido_eleito": False,
                "nota": "Cláusula de eleição de foro nula para consumidor. Litígio processa-se no domicílio do consumidor se ele for autor."
            }
        elif subscritor.tipo == "EMPRESA" and natureza_litigio == "CONTRATO":
            return {
                "foro_valido_eleito": True,
                "foro_eleito": self.arbitragem_b2b["sede"],
                "mecanismo": "ARBITRAGEM",
                "instituicao": self.arbitragem_b2b["instituicao"],
                "nota": "Cláusula arbitral válida. Renúncia expressa ao foro judicial."
            }
        else:
            return {
                "foro_valido_eleito": False,
                "foro_por_defeito": "Tribunais da sede do réu (Portugal)",
                "nota": "Aplicável Rome I e Bruxelas I bis por defeito."
            }

    def determinar_lei_aplicavel(self, subscritor, tipo_contrato):
        # Rome I: lei do país com que o contrato apresenta ligação mais estreita
        # Para contratos de consumo: lei do país de residência habitual do consumidor se o prestador direciona atividade para esse país
        if subscritor.tipo == "CONSUMIDOR" and self.direciona_atividade_para(subscritor.pais_residencia):
            return {
                "lei_aplicavel": f"Lei do {subscritor.pais_residencia}",
                "base": "Art. 6º Rome I - Contrato de consumo",
                "clausula_eleicao_valida": False,
                "nota": "Cláusula de eleição de lei portuguesa pode ser inválida se contrária a normas imperativas do país do consumidor."
            }
        else:
            return {
                "lei_aplicavel": "Lei Portuguesa",
                "base": "Art. 3º Rome I - Escolha das partes (para B2B) ou ligação mais estreita",
                "clausula_eleicao_valida": True
            }

    def direciona_atividade_para(self, pais):
        # Critérios Rome I: website no idioma local, moeda local, publicidade local, presença comercial
        return pais in self.paises_direcionados

    def gerar_clausula_contratual(self, subscritor):
        if subscritor.tipo == "CONSUMIDOR":
            return {
                "clausula_foro": "Qualquer litígio entre as partes será dirimido nos tribunais do domicílio do consumidor, nos termos do art. 18º do Regulamento (UE) n.º 1215/2012.",
                "clausula_lei": f"O presente contrato rege-se pela lei portuguesa, sem prejuízo das normas imperativas de proteção do consumidor da jurisdição de residência do subscritor ({subscritor.pais_residencia}).",
                "clausula_arbitragem": None,
                "ral": "Medião através do Centro Nacional de Informação e Arbitragem de Conflitos de Consumo (CNIACC) em Portugal, ou equivalente no país do consumidor."
            }
        else:
            return {
                "clausula_foro": f"Qualquer litígio decorrente do presente contrato será submetido a arbitragem de acordo com o Regulamento de Arbitragem da {self.arbitragem_b2b['instituicao']}, com sede em {self.arbitragem_b2b['sede']}, em {self.arbitragem_b2b['idioma']}, com {self.arbitragem_b2b['numero_arbitros']} árbitro(s).",
                "clausula_lei": f"O presente contrato rege-se pela {self.arbitragem_b2b['lei_substancial']}, à exclusão de qualquer outra.",
                "clausula_arbitragem": self.arbitragem_b2b,
                "ral": None
            }

    def processar_notificacao_judicial(self, documento, pais_origem):
        # Registo e encaminhamento para advogado externo
        registo = {
            "tipo": "NOTIFICACAO_JUDICIAL",
            "pais_origem": pais_origem,
            "data_rececao": datetime.utcnow().isoformat(),
            "prazo_resposta_dias": self.obter_prazo_processual(pais_origem),
            "advogado_responsavel": self.designar_advogado(pais_origem),
            "urgencia": documento.urgencia
        }
        self.db.inserir("registo_litigios", registo)
        self.alertar_equipa_legal(registo)
        return registo
```

## Thresholds e Tabelas

| Tipo de Subscritor | Foro Válido | Lei Válida | Mecanismo de RAL | Execução Sentença |
|--------------------|------------|-----------|------------------|--------------------|
| Consumidor (B2C) | Foro do domicílio do consumidor (Bruxelas I bis art. 18º) | Lei do país de residência se atividade direcionada (Rome I art. 6º) | CNIACC / Equivalente local | European Payment Order ou execução local |
| Empresa (B2B) | Arbitragem (ICC/LCIA) ou foro eleito | Lei portuguesa (escolha livre das partes) | Arbitragem | Convenção de Nova Iorque (1958) |
| Free Trial | Aplica-se B2C se posteriormente subscritor pago | Lei do país de residência | CNIACC | N/A (sem obrigação financeira) |

| País de Residência do Consumidor | Atividade Direcionada? | Lei Imperativa Relevante | RAL Recomendado |
|----------------------------------|------------------------|--------------------------|-----------------|
| Portugal | Sim | DL 66/2015, Lei 58/2019 | CNIACC |
| Espanha | Sim | Ley 7/1998, LO 3/2014 | Sistema Arbitral de Consumo |
| França | Sim | Code de la consommation | Médiateur du Commerce Coopératif |
| Alemanha | Sim | BGB, UWG | Verbraucherschlichtungsstelle |
| Reino Unido | Sim | Consumer Rights Act 2015 | CEDR / UK-based ADR |
| Brasil | Não (extra-UE) | CDC | N/A - litígio internacional |

## Riscos
- **Risco de Cláusula Nula**: Uma cláusula de eleição de foro em Lisboa para consumidores espanhóis é nula de pleno direito; o litígio será processado em Madrid com maior probabilidade de decisão desfavorável.
- **Risco de Normas Imperativas Estrangeiras**: Mesmo com lei portuguesa eleita, se o consumidor francês invocar o Code de la consommation, o tribunal francês pode aplicar normas imperativas francesas (ex: direito de resolução de 14 dias ineragível).
- **Risco de Arbitragem Ineficiente**: Arbitragem ICC com 3 árbitros em Lisboa pode custar €50.000+; inviável para litígios de €1.000. Deve haver cláusula de arbitragem rápida (fast-track) para valores menores.
- **Risco de Execução Transfronteiriça**: Uma sentença arbitral portuguesa contra um subscritor alemão exige reconhecimento no tribunal alemão; pode ser contestada se o subscritor alegar que não teve acesso a defesa adequada.

## Checklist de Jurisdição
- [ ] Análise de direcionamento de atividade por país (idioma do site, moeda, publicidade) para determinar aplicação de Rome I art. 6º.
- [ ] Cláusulas contratuais distintas para B2C e B2B; nenhuma cláusula de eleição de foro para consumidores.
- [ ] Registo de litígios e notificações judiciais em base de dados centralizada com prazos processuais, advogados externos, e estados de processo.
- [ ] Orçamento anual para litígios (provisão contabilística) baseado em taxa histórica de reclamações * valor médio de litígio.
- [ ] Parceria com advogados locais nos 5 principais mercados (PT, ES, FR, DE, UK) para resposta rápida a notificações.
- [ ] Cláusula de RAL (resolução extrajudicial de litígios) obrigatória para consumidores, conforme ODR Regulation (UE) 524/2013.
- [ ] Revisão anual da estrutura de jurisdição por alterações ao Rome I, Bruxelas I bis, ou nova legislação nacional.

## Links Cruzados
- [[17_Legal/TERMS_OF_SERVICE]] - Cláusulas de foro e lei aplicável incorporadas.
- [[17_Legal/SUBSCRICAO_AGREEMENT]] - Contrato individual com cláusulas personalizadas por tipo de subscritor.
- [[16_Compliance/REGULAMENTACAO_EU]] - Diretivas Rome I, Bruxelas I bis, ODR.
- [[16_Compliance/REGULAMENTACAO_PT]] - Normas imperativas portuguesas de defesa do consumidor.
- [[35_Financial_Tracking/PLANO_CONTAS]] - Provisão para litígios e custas judiciais.
