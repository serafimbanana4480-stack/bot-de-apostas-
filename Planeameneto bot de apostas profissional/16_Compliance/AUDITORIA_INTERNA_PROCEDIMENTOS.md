---
ID: CMP-008
tags: #status/active #compliance #auditoria #interna #procedimentos
---

# Procedimentos de Auditoria Interna de Compliance

## Objetivo
Estabelecer um framework estruturado de auditoria interna que garanta a conformidade contínua do sistema de value betting NBA com todas as obrigações legais, regulamentares e de melhores práticas. Este documento define o ciclo de auditoria, as áreas de escopo, as metodologias de teste, os responsáveis e os planos de ação corretiva para as não conformidades detetadas.

## Visão Geral do Programa de Auditoria

O programa de auditoria interna opera em três níveis:

1. **Auditorias Diárias** - Automatizadas, contínuas, focadas em controles de sistema
2. **Auditorias Mensais** - Focadas em processos operacionais e métricas
3. **Auditorias Anuais** - Abrangentes, conduzidas por auditor interno ou externo, cobrindo todos os domínios

---

## Auditorias Diárias (Automatizadas)

### Objetivo
Deteção imediata de desvios de compliance através de verificações automáticas executadas diariamente via scripts/cron jobs.

### Áreas de Escopo Diário

#### 1. Verificação de Idade e Autoexclusão

**O que é verificado:**
- Todos os novos registos do dia anterior têm idade ≥18 anos
- Nenhum subscritor ativo tem NIF na lista de autoexcluídos SRIJ
- Nenhum subscritor em jurisdição PROIBIDO (ver matriz REGULAMENTACAO_EU.md)

**Método de teste:**
```sql
SELECT COUNT(*) FROM subscritores 
WHERE data_criacao = CURRENT_DATE - 1 
AND data_nascimento > CURRENT_DATE - INTERVAL '18 years';
```

**Ação corretiva se falha:**
- Bloqueio imediato das contas afetadas
- Notificação ao Compliance Officer
- Reembolso prorata se aplicável
- Investigação de como a falha ocorreu (bug de sistema?)

**Responsável:** Sistema (automático) + Compliance Officer (notificação)

#### 2. Verificação de Consentimentos GDPR

**O que é verificado:**
- Todos os novos subscritores têm registo de consentimento de privacidade
- Versão do consentimento corresponde à versão ativa da política
- Hash do consentimento corresponde ao hash da política no momento

**Método de teste:**
```sql
SELECT s.id FROM subscritores s
LEFT JOIN consentimentos_privacidade cp ON s.id = cp.subscritor_id
WHERE s.data_criacao = CURRENT_DATE - 1
AND (cp.id IS NULL OR cp.versao_politica != (SELECT versao_atual FROM politica_privacidade));
```

**Ação corretiva se falha:**
- Suspender sinais para subscritores sem consentimento válido
- Enviar notificação para aceitar política atualizada
- Bloquear após 7 dias se não aceitar

**Responsável:** Sistema (automático)

#### 3. Verificação de Disclaimers em Sinais

**O que é verificado:**
- Todas as mensagens de sinal enviadas no dia anterior contêm disclaimer
- Disclaimer corresponde à versão ativa
- Hash do disclaimer no mensagem corresponde ao hash do template

**Método de teste:**
```sql
SELECT COUNT(*) FROM mensagens_sinal
WHERE data_envio = CURRENT_DATE - 1
AND disclaimer_hash != (SELECT hash_atual FROM disclaimer_template);
```

**Ação corretiva se falha:**
- Alerta imediato à equipa técnica
- Revisão manual das mensagens sem disclaimer
- Correção do bug que causou a omissão

**Responsável:** Sistema (automático) + Equipa Técnica

#### 4. Verificação de Limites KYC

**O que é verificado:**
- Subscritores em SDD não excederam €250 acumulados
- Subscritores em CDD não excederam €2.500 acumulados
- Subscritores não escalados automaticamente quando threshold atingido

**Método de teste:**
```sql
SELECT s.id, s.kyc_nivel, SUM(p.valor) as total_pago
FROM subscritores s
JOIN pagamentos p ON s.id = p.subscritor_id
WHERE p.data = CURRENT_DATE - 1
GROUP BY s.id, s.kyc_nivel
HAVING (s.kyc_nivel = 'SDD' AND SUM(p.valor) > 250)
   OR (s.kyc_nivel = 'CDD' AND SUM(p.valor) > 2500);
```

**Ação corretiva se falha:**
- Escalonamento imediato para nível superior
- Notificação ao subscritor para submeter documentação
- Suspensão de pagamentos até documentação recebida

**Responsável:** Sistema (automático)

#### 5. Verificação de Integridade Audit Trail

**O que é verificado:**
- Cadeia de hashes do audit trail está intacta (nenhuma adulteração)
- Todos os eventos críticos do dia anterior foram registados
- Timestamps estão em ordem cronológica

**Método de teste:**
```python
def verificar_integridade_audit_trail(data):
    registos = db.obter_registos_audit(data)
    hashes_falhados = 0
    for i, reg in enumerate(registos):
        hash_calculado = sha256(reg)
        if hash_calculado != reg.hash_proprio:
            hashes_falhados += 1
    return hashes_falhados == 0
```

**Ação corretiva se falha:**
- Alerta crítico à equipa técnica e segurança
- Investigação imediata de possível intrusão
- Restauração de backup do audit trail se necessário
- Notificação às autoridades se violação confirmada

**Responsável:** Sistema (automático) + CISO/CTO

#### 6. Verificação de Responsável Gambling

**O que é verificado:**
- Subscritores que atingiram thresholds de risco foram notificados
- Subscritores em nível VERMELHO têm sinais bloqueados
- Intervenções documentadas no audit trail

**Método de teste:**
```sql
SELECT s.id FROM subscritores s
JOIN avaliacoes_risco rg ON s.id = rg.subscritor_id
WHERE rg.nivel = 'VERMELHO'
AND rg.data = CURRENT_DATE - 1
AND s.sinais_bloqueados = false;
```

**Ação corretiva se falha:**
- Bloqueio imediato de sinais
- Envio de mensagem de intervenção
- Notificação ao Responsible Gambling Officer

**Responsável:** Sistema (automático) + RG Officer

---

## Auditorias Mensais

### Objetivo
Revisão sistemática de processos operacionais, métricas de desempenho de compliance e tendências de risco. Conduzida pelo Compliance Officer com suporte das equipas relevantes.

### Áreas de Escopo Mensal

#### 1. Revisão de Métricas de Compliance

**Métricas a analisar:**
- Taxa de conversão KYC (SDD→CDD→EDD)
- Tempo médio de verificação KYC
- Taxa de falsos positivos PEP
- Número de intervenções de Responsible Gambling
- Taxa de chargebacks
- Número de reclamações

**Método de análise:**
- Dashboard de métricas atualizado diariamente
- Comparação com targets mensais
- Análise de tendências (melhoria ou deterioração)
- Identificação de outliers

**Ação corretiva se métrica fora de target:**
- Investigação de causa raiz
- Plano de ação corretiva com timeline
- Acompanhamento mensal até normalização

**Responsável:** Compliance Officer

#### 2. Revisão de Amostra de Verificações KYC

**O que é revisto:**
- Amostra aleatória de 10% das verificações CDD aprovadas automaticamente
- 100% das verificações EDD
- 100% das verificações rejeitadas

**Método de revisão:**
- Acesso aos documentos submetidos
- Verificação manual contra critérios de aprovação
- Cross-check com resultados da API
- Documentação de discordâncias

**Ação corretiva se erro detetado:**
- Reversão da aprovação se erro grave
- Ajuste de thresholds da API se erro sistemático
- Formação adicional à equipa se erro humano

**Responsável:** Compliance Officer

#### 3. Revisão de Reclamações

**O que é revisto:**
- Todas as reclamações recebidas no mês
- Classificação por tipo (faturação, serviço, técnico, legal)
- Tempo de resposta
- Resolução alcançada

**Método de revisão:**
- Análise de padrões nas reclamações
- Identificação de reclamações recorrentes
- Avaliação da qualidade das respostas
- Verificação de follow-up necessário

**Ação corretiva se padrão problemático:**
- Alteração de processo se causa sistémica
- Formação à equipa se causa de competência
- Comunicação preventiva se causa de expectativa

**Responsável:** Compliance Officer + Customer Success

#### 4. Revisão de Alterações a Termos e Políticas

**O que é revisto:**
- Todas as alterações a ToS, Privacy Policy, Cookie Policy no mês
- Notificações enviadas aos subscritores
- Taxa de aceitação das alterações
- Subscritores que não aceitaram e foram suspensos

**Método de revisão:**
- Verificação de que alterações foram comunicadas adequadamente
- Confirmação de que suspensões foram executadas corretamente
- Análise de feedback dos subscritores

**Ação corretiva se problema detetado:**
- Reativação de subscritores se suspensão indevida
- Melhoria do processo de comunicação
- Revisão das alterações se rejeição massiva

**Responsável:** Compliance Officer + Legal

#### 5. Revisão de Acesso Administrativo

**O que é revisto:**
- Logs de acesso a dados sensíveis (dados pessoais, documentos KYC)
- Contas com privilégios administrativos
- Alterações a configurações de sistema

**Método de revisão:**
- Análise de logs de acesso do mês
- Verificação de justificação para acessos sensíveis
- Identificação de acessos anormais (horas, localização, volume)

**Ação corretiva se acesso suspeito:**
- Investigação imediata
- Revogação de privilégios se necessário
- Formação em segurança de dados se erro de processo

**Responsável:** Compliance Officer + CISO

#### 6. Revisão de Pagamentos e Chargebacks

**O que é revisto:**
- Todos os chargebacks do mês
- Razões alegadas pelos subscritores
- Resposta do prestador
- Taxa de chargeback vs. threshold (1%)

**Método de revisão:**
- Análise de padrões nas razões de chargeback
- Verificação de que respostas foram adequadas
- Identificação de subscritores com chargebacks recorrentes

**Ação corretiva se taxa >1%:**
- Análise profunda de causas
- Melhoria de processos de cobrança/communicação
- Contacto com gateway se taxa crítica

**Responsável:** Compliance Officer + Financeiro

---

## Auditorias Anuais

### Objetivo
Avaliação abrangente e independente de todo o programa de compliance, conduzida por auditor interno (se organização grande) ou auditor externo (recomendado para startups). A auditoria anual serve como validação terceira da conformidade e como input para melhoria contínua.

### Áreas de Escopo Anual

#### 1. Avaliação do Programa de Compliance

**O que é avaliado:**
- Adequação das políticas e procedimentos
- Eficácia dos controles implementados
- Cultura de compliance na organização
- Recursos alocados (pessoal, tecnologia, orçamento)

**Método de avaliação:**
- Entrevistas com key stakeholders
- Revisão documental (políticas, procedimentos, relatórios)
- Testes de controle (amostragem)
- Benchmarking com melhores práticas da indústria

**Output:**
- Relatório de auditoria com:
  - Avaliação de maturidade (1-5)
  - Não conformidades identificadas
  - Recomendações de melhoria
  - Plano de ação corretiva com prazos

**Responsável:** Auditor Interno/Externo + Compliance Officer

#### 2. Avaliação de Conformidade GDPR

**O que é avaliado:**
- Registo de atividades de tratamento (RAT)
- Bases jurídicas para cada categoria de dados
- Medidas de segurança implementadas
- Direitos dos titulares (processamento de pedidos)
- Transferências internacionais de dados
- Contratos com processadores (DPA)
- Designação e funcionamento do DPO

**Método de avaliação:**
- Revisão do RAT atualizado
- Teste de resposta a pedido de titular (simulação)
- Verificação de medidas técnicas e organizacionais
- Revisão de DPAs com todos os processadores
- Entrevista com DPO

**Output:**
- Relatório de conformidade GDPR
- Plano de ação para não conformidades
- Recomendações de melhoria

**Responsável:** Auditor (com especialização GDPR) + DPO

#### 3. Avaliação de Conformidade AML

**O que é avaliado:**
- Programa KYC/AML implementado
- Eficácia da deteção de atividade suspeita
- Processos de reporte à UIF/BdP (se aplicável)
- Formação da equipa em AML
- Integração com serviços de verificação

**Método de avaliação:**
- Revisão da política KYC/AML
- Teste de deteção de cenários de risco
- Revisão de relatórios de atividade suspeita
- Entrevistas com equipa operacional
- Verificação de contratos com fornecedores de verificação

**Output:**
- Relatório de conformidade AML
- Avaliação de eficácia do programa
- Recomendações de melhoria

**Responsável:** Auditor (com especialização AML) + Compliance Officer

#### 4. Avaliação de Responsible Gambling

**O que é avaliado:**
- Eficácia do sistema de deteção de risco
- Qualidade das intervenções realizadas
- Parcerias com entidades de apoio
- Formação da equipa em jogo responsável
- Feedback dos subscritores sobre intervenções

**Método de avaliação:**
- Análise de métricas de RG (intervenções, reativações)
- Revisão de casos de alto risco
- Entrevistas com subscritores que sofreram intervenções
- Verificação de parcerias com entidades de apoio
- Teste do sistema de deteção

**Output:**
- Relatório de Responsible Gambling
- Avaliação do impacto das intervenções
- Recomendações de melhoria

**Responsável:** Auditor + Responsible Gambling Officer

#### 5. Avaliação de Segurança da Informação

**O que é avaliado:**
- Medidas de segurança técnicas (encriptação, autenticação, firewalls)
- Medidas de segurança organizacionais (políticas, formação, controlo de acesso)
- Plano de resposta a incidentes
- Testes de penetração realizados
- Gestão de vulnerabilidades
- Backup e disaster recovery

**Método de avaliação:**
- Revisão de políticas de segurança
- Análise de relatórios de testes de penetração
- Verificação de implementação de recomendações anteriores
- Simulação de incidente de segurança
- Revisão de planos de backup/recovery

**Output:**
- Relatório de segurança da informação
- Avaliação de postura de segurança
- Recomendações de melhoria

**Responsável:** Auditor + CISO

---

## Processo de Gestão de Não Conformidades

### Classificação de Não Conformidades

| Severidade | Definição | Prazo Correção | Notificação |
|------------|-----------|----------------|-------------|
| Crítica | Violação legal grave, risco imediato de sanção | 24 horas | Diretoria, Conselho (se aplicável) |
| Alta | Violação legal/moderate, risco de sanção se não corrigido | 7 dias | Diretoria |
| Média | Desvio de processo sem risco legal imediato | 30 dias | Compliance Officer |
| Baixa | Oportunidade de melhoria, sem impacto significativo | 90 dias | Compliance Officer |

### Processo de Tratamento

1. **Identificação**: Não conformidade detetada em auditoria
2. **Registo**: Entrada no sistema de gestão de não conformidades
3. **Classificação**: Atribuição de severidade pelo Compliance Officer
4. **Investigação**: Análise de causa raiz
5. **Plano de Ação**: Definição de ações corretivas com responsáveis e prazos
6. **Implementação**: Execução das ações corretivas
7. **Verificação**: Confirmação de eficácia das ações
8. **Encerramento**: Arquivamento da não conformidade
9. **Lições Aprendidas**: Documentação para prevenir recorrência

### Exemplos de Não Conformidades

#### Exemplo 1: Falha na Verificação de Idade

- **Descrição**: Sistema permitiu registo de menor de 18 anos devido a bug
- **Severidade**: Crítica
- **Causa raiz**: Bug no cálculo de data de nascimento
- **Ação corretiva**: Correção do bug + teste automatizado + revisão de todos os registos do período afetado
- **Prazo**: 24 horas
- **Responsável**: CTO

#### Exemplo 2: Omissão de Disclaimer em Sinais

- **Descrição**: 15% das mensagens de sinal não incluíram disclaimer devido a falha de template
- **Severidade**: Alta
- **Causa raiz**: Template atualizado mas deploy incompleto
- **Ação corretiva**: Deploy completo + verificação de todas as mensagens enviadas + comunicação aos subscritores afetados
- **Prazo**: 7 dias
- **Responsável**: Lead Developer

#### Exemplo 3: Atraso em Resposta a Pedido de Titular GDPR

- **Descrição**: Pedido de acesso aos dados não respondido em 30 dias (prazo legal)
- **Severidade**: Média
- **Causa raiz**: Processo manual sem alertas de SLA
- **Ação corretiva**: Implementação de sistema de alertas SLA + formação à equipa
- **Prazo**: 30 dias
- **Responsável**: Compliance Officer

---

## Relatórios de Auditoria

### Relatório Diário (Automático)

**Conteúdo:**
- Resumo de verificações diárias (passou/falhou)
- Não conformidades críticas (se houver)
- Métricas operacionais básicas

**Distribuição:**
- Compliance Officer (diário)
- CTO (se falha técnica)
- Diretoria (se não conformidade crítica)

### Relatório Mensal

**Conteúdo:**
- Resumo executivo de compliance no mês
- Métricas principais com comparação vs. target
- Não conformidades identificadas e status
- Plano de ação para o mês seguinte
- Tendências e alertas

**Distribuição:**
- Diretoria (mensal)
- Conselho (trimestral - resumo)
- Compliance Officer (mensal)

### Relatório Anual

**Conteúdo:**
- Avaliação completa do programa de compliance
- Maturidade de compliance por domínio
- Não conformidades do ano e resolução
- Recomendações estratégicas
- Plano de melhoria para o ano seguinte

**Distribuição:**
- Diretoria (anual)
- Conselho (anual)
- Investidores (se aplicável)
- Reguladores (se solicitado)

---

## Independência da Auditoria

### Princípios de Independência

Para garantir a credibilidade das auditorias, o auditor deve:

1. **Não ter conflito de interesses**: Não auditar áreas onde tem responsabilidade operacional
2. **Reportar diretamente à direção**: Linha de reporte independente das áreas auditadas
3. **Ter recursos adequados**: Orçamento, pessoal e ferramentas para conduzir auditorias eficazes
4. **Ser competente**: Formação e experiência em compliance e auditoria

### Auditor Externo vs. Interno

| Aspecto | Auditor Interno | Auditor Externo |
|---------|-----------------|-----------------|
| Custo | Menor (salário) | Maior (honorários) |
| Independência | Limitada (parte da organização) | Alta (terceiro independente) |
| Conhecimento do negócio | Alto | Requer learning curve |
| Credibilidade externa | Média | Alta |
| Frequência | Contínua | Pontual (anual) |

**Recomendação**: Para fase inicial (startup), auditor interno (Compliance Officer) com revisão externa anual. Para fase mais madura, equipa de auditoria interna com auditor externo periódico.

---

## Links Cruzados

- [[16_Compliance/AUDIT_TRAIL_COMPLIANCE]] - Sistema de registo para auditorias
- [[16_Compliance/KYC_AML]] - Programa KYC/AML sujeito a auditoria
- [[16_Compliance/RESPONSIBLE_GAMBLING]] - Programa de jogo responsável
- [[16_Compliance/REGULAMENTACAO_PT]] - Obrigações legais Portugal
- [[16_Compliance/REGULAMENTACAO_EU]] - Obrigações legais UE
- [[17_Legal/PRIVACY_POLICY]] - Conformidade GDPR
- [[34_Security/INCIDENT_RESPONSE]] - Resposta a incidentes de segurança