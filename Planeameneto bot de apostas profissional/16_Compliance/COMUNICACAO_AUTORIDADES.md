---
ID: CMP-009
tags: #status/active #compliance #autoridades #comunicacao #regulador
---

# Procedimentos de Comunicação com Autoridades Reguladoras

## Objetivo
Estabelecer protocolos claros e estruturados para toda a comunicação com autoridades reguladoras, fiscais e de proteção de dados, assegurando que o sistema de value betting NBA responde adequadamente a solicitações, notificações, inspeções e investigações, mantendo registos completos e protegendo os direitos dos subscritores e da organização.

## Autoridades Relevantes

### Autoridades Portuguesas

| Autoridade | Sigla | Competência | Contacto Principal |
|------------|-------|-------------|-------------------|
| Serviço de Regulação e Inspeção de Jogos | SRIJ | Regulação de jogos e apostas online | +351 213 893 700 |
| Inspeção-Geral das Atividades Culturais | IGAC | Supervisão do SRIJ | +351 213 928 200 |
| Comissão Nacional de Proteção de Dados | CNPD | Supervisão GDPR/LGPD | +351 217 828 100 |
| Autoridade Tributária e Aduaneira | AT | Fiscalidade, IRS | +351 217 206 707 |
| Autoridade de Supervisão de Seguros e Fundos de Pensões | ASF | Se aplicável (investimentos) | +351 217 902 100 |
| Banco de Portugal | BdP | Se aplicável (AML/UIF) | +351 213 130 000 |
| Unidade de Informação Financeira | UIF | Branqueamento de capitais | +351 213 130 000 |

### Autoridades Europeias

| Autoridade | Sigla | Competência | Contacto |
|------------|-------|-------------|----------|
| European Data Protection Board | EDPB | Coordenação GDPR a nível UE | edpb@edpb.europa.eu |
| European Banking Authority | EBA | Se aplicável (AML) | info@eba.europa.eu |
| Comissão Europeia - DG GROW | CE | Mercado interno, consumo | growth-info@ec.europa.eu |

### Autoridades de Outros Estados-Membros

| País | Autoridade Proteção Dados | Autoridade Jogo | Autoridade AML |
|------|---------------------------|-----------------|----------------|
| Espanha | AEPD | DGOJ | SEPBLAC |
| França | CNIL | ANJ | TRACFIN |
| Alemanha | DSK (varios) | GGL | FIU |
| Reino Unido | ICO | UKGC | NCA |
| Itália | GPDP | ADM | UIF |

---

## Tipos de Comunicação

### 1. Notificações Obrigatórias (Proativas)

#### 1.1 Notificação de Violação de Dados Pessoais (GDPR Art. 33º)

**Quando notificar:**
- Sempre que ocorra uma violação de dados pessoais
- Prazo: 72 horas após ter conhecimento da violação

**O que notificar:**
- Natureza da violação (categorias de dados, número de titulares afetados)
- Nome e contactos do DPO
- Descrição das consequências prováveis
- Medidas tomadas ou propostas para remediar

**Processo:**
```
1. Equipa de segurança deteta violação
2. CISO notifica Compliance Officer e DPO
3. Avaliação de risco para titulares (alto/baixo)
4. Se risco alto: notificação CNPD + notificação titulares
5. Se risco baixo: apenas notificação CNPD (pode ser diferida)
6. Registo detalhado no audit trail
7. Follow-up com CNPD até resolução
```

**Template de Notificação:**
```
Assunto: NOTIFICAÇÃO DE VIOLAÇÃO DE DADOS PESSOAIS - [Nome Empresa]

À atenção da CNPD,

Informamos que ocorreu uma violação de dados pessoais no dia [data].

[Descrição detalhada do incidente]

Categorias de dados afetadas: [lista]
Número de titulares afetados: [número]
Risco para titulares: [alto/baixo] - [justificação]

Medidas tomadas:
- [medida 1]
- [medida 2]
- [medida 3]

Contacto DPO: [nome] - [email] - [telefone]

Disponibilizamo-nos para fornecer informações adicionais.

Cumps,
[Nome Responsável]
[Cargo]
[Data]
```

**Responsável:** DPO + Compliance Officer

#### 1.2 Notificação de Atividade Suspeita (AML)

**Quando notificar:**
- Sempre que houver suspeita fundada de branqueamento de capitais ou financiamento do terrorismo
- Se aplicável (depende de enquadramento legal do serviço)

**O que notificar:**
- Identificação do subscritor
- Descrição da atividade suspeita
- Documentação de suporte
- Medidas tomadas

**Processo:**
```
1. Sistema ou Compliance Officer deteta atividade suspeita
2. Investigação preliminar para confirmar suspeita
3. Se confirmada: preparação de relatório detalhado
4. Submissão à UIF/BdP via sistema seguro
5. Bloqueio de conta se necessário
6. Registo no audit trail (sem revelar ao subscritor)
```

**Responsável:** Compliance Officer + Diretor Compliance

#### 1.3 Notificação de Alterações ao Serviço (SRIJ)

**Quando notificar:**
- Alterações ao modelo de negócio
- Alterações aos termos de serviço
- Alterações às políticas de jogo responsável
- Alterações significativas à tecnologia

**Prazo:** Imediato ou conforme definido pelo SRIJ

**Processo:**
```
1. Decisão de alteração aprovada
2. Redação de documento descritivo da alteração
3. Submissão ao SRIJ via email/formulário
4. Acompanhamento até confirmação de receção
5. Registo no audit trail
```

**Responsável:** Compliance Officer + Legal

### 2. Resposta a Solicitações (Reativas)

#### 2.1 Solicitações de Informação da CNPD

**Tipos de solicitações:**
- Pedidos de esclarecimento sobre tratamento de dados
- Solicitações de documentos (RAT, políticas, contratos)
- Notificações de reclamações de titulares
- Pedidos de inspeção

**Processo de resposta:**
```
1. Receção de solicitação (email, carta)
2. Registo no sistema de gestão de solicitações
3. Atribuição de responsável (DPO/Compliance Officer)
4. Recolha de informações/documentos solicitados
5. Revisão legal da resposta
6. Envio da resposta dentro do prazo indicado
7. Registo no audit trail
8. Follow-up se necessário
```

**Prazo típico:** 10-30 dias (depende da complexidade)

**Responsável:** DPO + Legal

#### 2.2 Solicitações da Autoridade Tributária

**Tipos de solicitações:**
- Pedidos de informação sobre subscritores portugueses
- Solicitações de faturas/recibos
- Pedidos de esclarecimento sobre modelo de negócio
- Inspeções fiscais

**Processo de resposta:**
```
1. Receção de solicitação (ofício)
2. Verificação de autenticidade da solicitação
3. Consulta ao contador/advogado fiscal
4. Recolha de documentação
5. Preparação de resposta
6. Revisão legal
7. Envio da resposta
8. Registo no audit trail
```

**Responsável:** Financeiro + Legal + Contador

#### 2.3 Solicitações do SRIJ/IGAC

**Tipos de solicitações:**
- Pedidos de informações sobre operações
- Solicitações de dados de subscritores portugueses
- Pedidos de relatórios de jogo responsável
- Inspeções

**Processo de resposta:**
```
1. Receção de solicitação
2. Avaliação de legalidade/proporcionalidade do pedido
3. Consulta a advogado especializado em direito do jogo
4. Recolha de informações (respeitando limites de dados pessoais)
5. Preparação de resposta
6. Revisão legal
7. Envio da resposta
8. Registo no audit trail
```

**Responsável:** Compliance Officer + Legal

### 3. Inspeções e Investigações

#### 3.1 Inspeção da CNPD

**Preparação:**
- Verificação de que RAT está atualizado
- Organização de documentos (políticas, contratos, registos)
- Preparação de sala para inspetores
- Designação de ponto de contacto principal

**Durante inspeção:**
- Acompanhamento constante por DPO/Compliance Officer
- Fornecimento proativo de documentos solicitados
- Notas detalhadas de questões colocadas
- Não fornecer informação não solicitada sem consulta legal

**Após inspeção:**
- Relatório interno do que foi discutido
- Plano de ação para não conformidades identificadas
- Follow-up com CNPD até encerramento

**Responsável:** DPO + Compliance Officer + Legal

#### 3.2 Inspeção da Autoridade Tributária

**Preparação:**
- Organização de toda a documentação fiscal (faturas, recibos, declarações)
- Verificação de conciliações bancárias
- Preparação de explicações para itens não standard
- Consulta prévia ao contador/advogado fiscal

**Durante inspeção:**
- Presença do contador/advogado fiscal
- Fornecimento de documentos solicitados
- Respostas claras e concisas
- Notas detalhadas

**Após inspeção:**
- Relatório interno
- Resposta a questões pendentes
- Pagamento de quaisquer taxas/penalidades devidas

**Responsável:** Financeiro + Contador + Legal

#### 3.3 Investigação Criminal (se aplicável)

**Cenários:**
- Mandado de busca e apreensão
- Solicitação de acesso a dados por autoridades judiciais
- Investigação por possível crime (ex: branqueamento, fraude)

**Processo:**
```
1. Receção de mandado/solicitação judicial
2. Verificação de validade legal (advogado obrigatório)
3. Avaliação de escopo do pedido
4. Cooperação limitada ao estritamente necessário
5. Proteção de dados de terceiros não relevantes
6. Registo detalhado no audit trail
7. Notificação às partes afetadas se legalmente permitido
8. Consulta a advogado sobre notificação a subscritores
```

**Responsável:** Legal + Advogado Externo + Compliance Officer

---

## Proteção de Dados em Comunicações com Autoridades

### Princípios

1. **Minimização**: Fornecer apenas o estritamente necessário
2. **Proporcionalidade**: Avaliar se o pedido é proporcional ao objetivo
3. **Legalidade**: Verificar base legal para a solicitação
4. **Confidencialidade**: Proteger dados de subscritores não relevantes
5. **Registo**: Documentar todas as comunicações

### Processo de Revisão Legal

Antes de enviar qualquer informação a uma autoridade:

1. **Verificar competência**: A autoridade tem competência para solicitar?
2. **Verificar base legal**: Existe mandato legal para a solicitação?
3. **Avaliar proporcionalidade**: O pedido é proporcional?
4. **Minimizar dados**: Podemos fornecer menos informação?
5. **Proteger terceiros**: Dados de outros subscritores estão protegidos?
6. **Consultar advogado**: Se houver dúvida, consulta obrigatória

### Direitos dos Subscritores

Quando dados pessoais são partilhados com autoridades:

1. **Notificação**: Subscritor deve ser notificado se legalmente permitido
2. **Direito de informação**: Subscritor pode pedir que informações foram partilhadas
3. **Direito de recurso**: Subscritor pode contestar a partilha se ilegal
4. **Confidencialidade**: A partilha não deve ser divulgada publicamente

---

## Gestão de Reclamações de Subscritores às Autoridades

### Cenário: Subscritor reclama à CNPD

**Processo:**
```
1. CNPD notifica empresa da reclamação
2. Registo no sistema de gestão de reclamações
3. Análise da reclamação
4. Recolha de evidências (audit trail, emails, documentos)
5. Preparação de resposta detalhada
6. Revisão legal
7. Envio de resposta à CNPD
8. Se reclamação procedente: plano de ação corretiva
9. Comunicação ao subscritor (se apropriado)
10. Follow-up até encerramento
```

**Responsável:** DPO + Compliance Officer + Legal

### Cenário: Subscritor reclama ao SRIJ

**Processo similar ao acima**, adaptado à competência do SRIJ

**Responsável:** Compliance Officer + Legal

---

## Template de Documentação para Autoridades

### Template de Relatório de Atividade (SRIJ)

```
RELATÓRIO DE ATIVIDADE - [PERÍODO]
[Nome Empresa]
[NIPC]

1. RESUMO EXECUTIVO
- Total de subscritores portugueses: [número]
- Total de sinais enviados: [número]
- Total de reclamações: [número]
- Intervenções de jogo responsável: [número]

2. DADOS DE SUBSCRITORES PORTUGUESES
- Novos subscritores: [número]
- Subscritores ativos: [número]
- Cancelamentos: [número]
- Distribuição por plano: [tabela]

3. JOGO RESPONSÁVEL
- Intervenções por nível: [tabela]
- Autoexclusões: [número]
- Bloqueios por comportamento de risco: [número]

4. RECLAMAÇÕES
- Total: [número]
- Por tipo: [tabela]
- Resolvidas: [número]
- Pendentes: [número]

5. ALTERAÇÕES AO SERVIÇO
- [Descrição de alterações]

6. DOCUMENTAÇÃO ANEXA
- [Lista de documentos anexos]

Data: [data]
Responsável: [nome/cargo]
```

### Template de Resposta a Pedido da CNPD

```
REFERÊNCIA: [Número de referência da CNPD]
ASSUNTO: Resposta a pedido de informações

Exmos. Senhores,

Em resposta ao pedido de informações referenciado acima, enviaremos os seguintes documentos:

1. Registo de Atividades de Tratamento (RAT)
2. Política de Privacidade (versão atual)
3. Contratos com Processadores de Dados
4. Registo de Consentimentos
5. [Outros documentos solicitados]

Informamos que [qualquer informação adicional relevante]

Colocamo-nos à disposição para esclarecimentos adicionais.

Com os melhores cumprimentos,

[Nome do DPO]
Data Protection Officer
[Email]
[Telefone]
Data: [data]
```

---

## Registo de Comunicações

### Sistema de Registo

Todas as comunicações com autoridades devem ser registadas no sistema com:

- Data e hora
- Autoridade contactada
- Tipo de comunicação (notificação, solicitação, resposta)
- Resumo do conteúdo
- Documentos anexados
- Responsável pela comunicação
- Prazo de resposta (se aplicável)
- Status (pendente, concluída, em follow-up)
- Referência externa (número de processo)

### Retenção de Registos

- **Comunicações com CNPD**: 10 anos
- **Comunicações com AT**: 10 anos
- **Comunicações com SRIJ**: 10 anos
- **Outras autoridades**: 5 anos

---

## Formação da Equipa

### Competências Necessárias

A equipa que lida com autoridades deve ter formação em:

1. **GDPR/LGPD**: Direitos dos titulares, obrigações do controlador
2. **Direito do jogo**: Regime jurídico português e europeu
3. **AML**: Obrigações de reporte (se aplicável)
4. **Comunicação escrita formal**: Redação de documentos oficiais
5. **Gestão de crise**: Resposta a inspeções/investigações

### Formação Anual

- **Módulo 1**: Atualizações regulamentares (4 horas)
- **Módulo 2**: Simulação de inspeção CNPD (2 horas)
- **Módulo 3**: Redação de documentos oficiais (2 horas)
- **Módulo 4**: Gestão de reclamações (2 horas)

**Total:** 10 horas/ano por membro da equipa

---

## Links Cruzados

- [[16_Compliance/REGULAMENTACAO_PT]] - Obrigações legais específicas Portugal
- [[16_Compliance/REGULAMENTACAO_EU]] - Obrigações legais europeias
- [[16_Compliance/AUDIT_TRAIL_COMPLIANCE]] - Registo de comunicações
- [[17_Legal/PRIVACY_POLICY]] - Proteção de dados em comunicações
- [[17_Legal/JURISDICAO_ESTRUTURA]] - Jurisdição aplicável
- [[34_Security/INCIDENT_RESPONSE]] - Resposta a incidentes de segurança