---
ID: CMP-001
tags: #status/active #compliance #regulamentacao #pt
---

# Regulamentação Portuguesa

## Objetivo
Documentar, mapear e garantir a conformidade total do sistema de value betting quantitativo NBA com o enquadramento legal e regulamentar português aplicável às atividades de apostas desportivas, tratamento de dados pessoais, prestação de serviços de informação remunerada e obrigações fiscais associadas. Esta nota serve como fonte de verdade única para decisões de arquitetura do sistema que tenham implicações jurídicas em Portugal.

## O que faz
- Cataloga todos os diplomas legais aplicáveis: Decreto-Lei n.º 66/2015 (regime jurídico dos jogos e apostas online), Regulamento do SRIJ/IGAC, Lei n.º 58/2019 (Lei Geral de Proteção de Dados - LGPD, transposta do GDPR), CIRS e CIVA.
- Define restrições de operação para utilizadores/comerciantes com residência fiscal em Portugal.
- Estabelece procedimentos de verificação de idade e de bloqueio geográfico.
- Mapeia as entidades reguladoras competentes e os canais de comunicação obrigatórios.

## Porque existe
Sem um mapeamento explícito da regulamentação portuguesa, o sistema incorre em risco de:
- Co-responsabilização na prestação de serviços a menores ou a jogadores autoexcluídos.
- Infringimento da LGPD por tratamento ilícito de dados sensíveis (comportamento de jogo, dados biométricos se existirem).
- Atuação da IGAC/SRIJ com sanções que podem ir até ao encerramento de atividade e responsabilização criminal do gestor de operações.
- Perda de confiança de subscritores e stakeholders devido a operação em "zona cinzenta" legal.

## Implementação / Pseudocódigo
```python
class CompliancePT:
    def __init__(self):
        self.entidades_reguladoras = ["SRIJ", "CNPD", "IGAC", "Autoridade Tributária"]
        self.diplomas = [
            "DL_66_2015_Jogos_Apostas_Online",
            "Lei_58_2019_LGPD",
            "CIRS",
            "CIVA",
            "Regulamento_SRIJ_licenciamento"
        ]
        self.proibicoes_geograficas = self.carregar_lista_jogadores_autoexcluidos()

    def validar_subscritor_pt(self, utilizador):
        if utilizador.residencia_fiscal != "PT":
            return {"status": "NA", "obrigacoes": []}
        
        checks = {
            "maior_idade": utilizador.idade >= 18,
            "nao_autoexcluido": utilizador.nif not in self.proibicoes_geograficas,
            "consentimento_lgpd": utilizador.consentimento_tratamento == "EXPLICITO",
            "verificacao_kyc": utilizador.kyc_status == "VERIFICADO"
        }
        
        if not all(checks.values()):
            return {"status": "BLOQUEADO", "motivo": checks}
        
        return {"status": "APROVADO", "obrigacoes": [
            "declaracao_irs_anual",
            "comprovativo_morada",
            "consentimento_renovavel_12_meses"
        ]}

    def gerar_relatorio_trimestral_srij(self):
        relatorio = {
            "total_subscritores_pt": self.contar_subscritores_pt(),
            "total_apostas_recomendadas_pt": self.contar_recomendacoes_pt(),
            "reclamacoes_registadas": self.contar_reclamacoes(),
            "intervencoes_responsible_gambling": self.contar_intervencoes()
        }
        self.arquivar_audit_trail("relatorio_trimestral_srij", relatorio)
        return relatorio
```

## Thresholds e Tabelas

| Obrigação Legal | Entidade | Frequência | Threshold de Ação | Penalidade em Falta |
|----------------|----------|-----------|------------------|---------------------|
| Comunicação alterações serviço | SRIJ/IGAC | Imediata | Qualquer alteração no modelo de negócio | Coima até €44.890 |
| Declaração dados subscritores PT | CNPD | Anual | > 5000 registos tratados | Coima até €20M ou 4% CA |
| Manutenção registo autoexcluídos | SRIJ | Contínua | Matching em tempo real | Suspensão de atividade |
| Comprovativo idade (KYC) | Interno | Por subscritor | < 18 anos detetado | Cancelamento imediato + denúncia |
| Emissão faturas (CIVA) | AT | Por transação | Ausência de fatura em 5 dias úteis | Coima, inquérito tributário |

## Riscos
- **Risco Regulatório Elevado**: O enquadramento legal português para serviços de informação de apostas não é explicitamente claro; pode haver reclassificação da atividade como "intermediação de apostas", o que exigiria licenciamento SRIJ.
- **Risco de Conformidade LGPD**: Dados de comportamento de jogo (histórico de apostas, stakes, win/loss) são considerados dados pessoais sensíveis. O tratamento sem base jurídica adequada ou sem DPO designado expõe a sanções.
- **Risco de Bloqueio de Conteúdo**: ISP portugueses podem ser obrigados a bloquear domínios associados a serviços não licenciados se a atividade for reclassificada.
- **Risco Tributário**: Os subscritores portugueses devem declarar rendimentos de jogo (CIRS, categoria G). O não fornecimento de informações claras pode gerar responsabilização subsidiária.

## Checklist de Conformidade PT
- [ ] Designação de DPO (Data Protection Officer) registado na CNPD.
- [ ] Contrato de processamento de dados (DPA) com todos os subcontratantes (VPS, cloud, APIs).
- [ ] Lista atualizada de NIFs autoexcluídos carregada diariamente via feed SRIJ (se disponível) ou verificação mensual manual.
- [ ] Cláusulas contratuais com subscritores PT que excluem menores de idade e jogadores autoexcluídos.
- [ ] Mecanismo de geoblocking para IPs portugueses em caso de ordem judicial ou reclassificação regulamentar.
- [ ] Template de declaração de responsabilidade fiscal entregue a cada subscritor PT no onboarding.
- [ ] Revisão trimestral por advogado especializado em direito do jogo (atualização desta nota).

## Links Cruzados
- [[16_Compliance/KYC_AML]] - Verificação de identidade obrigatória para subscritores PT.
- [[16_Compliance/DISCLAIMERS]] - Isenção de responsabilidade legal a apresentar em PT.
- [[16_Compliance/RESPONSIBLE_GAMBLING]] - Intervenção obrigatória em jogadores com comportamento de risco.
- [[17_Legal/TERMS_OF_SERVICE]] - Termos que incorporam as restrições PT.
- [[17_Legal/PRIVACY_POLICY]] - Política de privacidade adaptada à LGPD.
- [[35_Financial_Tracking/IMPOSTOS_PROVISAO]] - Modelo de provisão fiscal para subscritores e empresa.
