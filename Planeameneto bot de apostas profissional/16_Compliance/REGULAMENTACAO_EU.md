---
ID: CMP-002
tags: #status/active #compliance #regulamentacao #eu #gdpr
---

# Regulamentação Europeia

## Objetivo
Estabelecer o quadro de conformidade obrigatória para todos os subscritores e operações no Espaço Económico Europeu (EEE), fora de Portugal, garantindo alinhamento com o GDPR (Regulamento UE 2016/679), a Diretiva dos Serviços de Pagamento (PSD2), o Regulamento UE 2018/302 (discriminação geográfica), e as legislações nacionais de jogo de cada Estado-Membro onde o serviço de informação possa ser acedido.

## O que faz
- Mapeia os 27 regimes nacionais de regulamentação de apostas desportivas na UE/EEE.
- Define regras de tratamento de dados transfronteiriço (Capítulo V do GDPR).
- Estabelece mecanismos de deteção de residência fiscal e de bloqueio condicional baseado em jurisdição.
- Documenta obrigações específicas derivadas de PSD2 no que toca a pagamentos de subscrição e reembolsos.
- Cria matriz de responsabilidade para casos de conflito de leis (Rome I, Rome II, Bruxelas I bis).

## Porque existe
A prestação transfronteiriça de serviços de informação quantitativa de apostas coloca o sistema sob jurisdição múltipla. A ausência de mapeamento regulatório europeu resulta em:
- Inibições de mercado (ex: Alemanha, com o seu regime de monopolio parcial; Países Baixos, com licenciamento obrigatório para afiliados).
- Sanções do GDPR por transferência de dados para fora do EEE sem salvaguardas adequadas (ex: VPS nos EUA sem SCCs atualizadas).
- Responsabilidade civil por danos patrimoniais de subscritores que operem em mercados regulados onde o serviço possa ser considerado "aconselhamento de investimento" ou "intermediação".
- Litígios de consumo em jurisdições desfavoráveis devido a cláusulas de eleição de foro inexistentes ou inválidas.

## Implementação / Pseudocódigo
```python
class ComplianceEU:
    def __init__(self):
        self.matriz_jurisdicao = self.carregar_matriz_27_estados()
        self.transferencias_dados = {
            "modelo": "SCC_2021_EU_Commission",
            "dti_pais": ["EUA", "Reino_Unido", "Suica"],  # DTI = decisão de transferência internacional
            "tdp_adequado": ["UK", "Suica", "Japao", "Coreia_do_Sul"]
        }
        self.pagamentos_psd2 = {
            "provedor_SCA": True,
            "limite_isencao": 30,  # euros
            "reembolso_direito": 14  # dias (direito de livre resolução)
        }

    def classificar_jurisdicao(self, pais_residencia, ip_acesso):
        regime = self.matriz_jurisdicao.get(pais_residencia)
        if not regime:
            return {"status": "BLOQUEIO_PRECAUCIONAL", "motivo": "JURISDICAO_NAO_MAPEADA"}
        
        nivel_risco = regime["risco_legal"]
        if nivel_risco == "PROIBIDO":
            return {"status": "BLOQUEIO_TOTAL", "motivo": "REGIME_PROIBITIVO"}
        elif nivel_risco == "LICENCIAMENTO_OBRIGATORIO":
            return {"status": "RESTRITO", "obrigacoes": ["verificar_licenciamento_local", "disclaimer_reforcado"]}
        else:
            return {"status": "PERMITIDO_CONDICIONAL", "obrigacoes": regime["obrigacoes_minimas"]}

    def validar_transferencia_dados(self, pais_destino, tipo_dados):
        if pais_destino in self.transferencias_dados["tdp_adequado"]:
            return {"status": "LIVRE", "mecanismo": "Decisao_Adequacao"}
        elif pais_destino in self.transferencias_dados["dti_pais"]:
            return {"status": "CONDICIONAL", "mecanismo": "SCC", "tia_required": tipo_dados == "SENSIVEL"}
        else:
            return {"status": "BLOQUEADO", "motivo": "PAIS_NAO_ADEQUADO_SEM_SCC"}
```

## Thresholds e Tabelas

| Estado-Membro | Regime de Apostas | Risco para Info-Serviço | Obrigação Específica | Bloco Recomendado |
|--------------|-------------------|------------------------|---------------------|-------------------|
| Alemanha | Monopolio parcial (Gluecksspielneustaatsvertrag) | Muito Alto | Considerado aconselhamento; requer licença se remunerado | Sim, exceto com parecer legal |
| França | ARJEL/ANJ - Fechado | Alto | Intermediação proibida; info pura tolerada se não vinculada a bookmaker | Restrito |
| Países Baixos | KSA - Licenciamento afiliados | Alto | Licença obrigatória para quem direciona tráfego para operadores | Sim |
| Espanha | DGOJ - Licenciamento | Médio | Registo como socio/afiliado possível; info pura geralmente livre | Não, com disclaimer |
| Itália | ADM - Licenciamento | Médio | Restrições publicitárias severas; info pura tolerada | Não, com disclaimer |
| Reino Unido | UKGC | Médio | Não é UE, mas GDPR aplicável (UK GDPR); afiliação licenciada | Não, com DPA UK |
| Suécia | Spelinspektionen | Médio | Publicidade restrita; serviço pago pode ser classificado como marketing | Restrito |

| Disposição GDPR | Artigo | Aplicação no Sistema | Controlador/Processador |
|----------------|--------|---------------------|------------------------|
| Base jurídica | 6º, 7º | Consentimento explícito para perfilamento de comportamento de jogo | Controlador |
| Direito ao esquecimento | 17º | Eliminação de dados pessoais após 36 meses de inatividade | Controlador |
| Portabilidade | 20º | Exportação de dados de apostas em formato CSV/JSON | Controlador |
| Registo atividades | 30º | Documentação de todos os tratamentos de dados | Controlador |
| DPO | 37º | Obrigatório dado o "monitorização sistemática" (perfilamento de subscritores) | Controlador |
| Violação dados | 33º, 34º | Notificação CNPD/ICO em 72h se vazamento de dados pessoais | Controlador |

## Riscos
- **Risco de Reclassificação Transfronteiriça**: Um subscritor alemão pode alegar que o serviço constitui "jogo organizado" (Glücksspiel) se houver qualquer mecanismo de rastreio de resultados ou leaderboard entre pares.
- **Risco de Transferência de Dados**: Uma VPS nos EUA sem DTI/SCC válidas expõe a coimas até 4% do volume de negócios mundial (GDPR art. 83).
- **Risco PSD2**: Reembolsos de subscrição solicitados dentro de 14 dias exigem devolução integral se o serviço não tiver sido "plenamente prestado com consentimento expresso".
- **Risco de Publicidade Direcionada**: O uso de dados de navegação para remarketing a subscritores em jurisdições com restrições publicitárias ao jogo (ex: Itália, Bélgica) é infração administrativa grave.

## Checklist de Conformidade EU
- [ ] Matriz de jurisdição dos 27 Estados-Membros validada por advogado de direito do jogo (atualização semestral).
- [ ] Standard Contractual Clauses (SCC) 2021/914 da Comissão Europeia assinadas com todos os processadores fora do EEE.
- [ ] Transfer Impact Assessment (TIA) concluída para qualquer transferência de dados pessoais para EUA, UK, Suíça.
- [ ] Mecanismo de deteção de IP + cartão de pagamento para identificação de residência fiscal com bloqueio automático em jurisdições PROIBIDO.
- [ ] Template de fatura de subscrição que cumpre PSD2 (indicação clara de SCA aplicada, direito de livre resolução).
- [ ] Registo de atividades de tratamento (RAT) mantido atualizado e disponível para inspeção das autoridades de proteção de dados.
- [ ] Cláusula de eleição de foro nos termos de subscrição válida no Estado-Membro de residência do consumidor (Rome I).

## Links Cruzados
- [[16_Compliance/REGULAMENTACAO_PT]] - Caso específico de Portugal dentro do EEE.
- [[16_Compliance/KYC_AML]] - Verificação de identidade transfronteiriça com GDPR.
- [[16_Compliance/DISCLAIMERS]] - Disclaimer jurídico adaptado por jurisdição.
- [[17_Legal/PRIVACY_POLICY]] - Política de privacidade com anexos por país.
- [[17_Legal/JURISDICAO_ESTRUTURA]] - Estruturação da jurisdição aplicável e eleição de foro.
- [[34_Security/SECRETS_MANAGEMENT]] - Gestão de secrets com conformidade GDPR.
