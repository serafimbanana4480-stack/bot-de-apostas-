---
ID: CMP-007
tags: #status/active #compliance #kyc #processo #detalhado
---

# Processo KYC Detalhado - Procedimentos Operacionais

## Objetivo
Documentar de forma exaustiva o processo de Know Your Customer (KYC) aplicável ao serviço de informação quantitativa de apostas NBA, estabelecendo procedimentos operacionais padrão, responsabilidades, timelines e critérios de decisão para cada etapa do ciclo de vida do subscritor, desde o registo inicial até à verificação contínua e reavaliação periódica.

## Visão Geral do Processo

O processo KYC é estruturado em quatro fases principais:

1. **Fase 1 - Registo Inicial (SDD - Simplified Due Diligence)**
2. **Fase 2 - Verificação Identidade (CDD - Customer Due Diligence)**
3. **Fase 3 - Diligência Reforçada (EDD - Enhanced Due Diligence)**
4. **Fase 4 - Monitorização Contínua e Revisão Periódica**

---

## Fase 1: Registo Inicial (SDD)

### Objetivos
- Permitir onboarding rápido sem fricção desnecessária
- Recolher informação mínima para avaliação de risco inicial
- Estabelecer base para escalonamento posterior se necessário

### Informação Recolhida

| Campo | Tipo | Obrigatório | Finalidade | Retenção |
|-------|------|-------------|------------|----------|
| Nome completo | Texto | Sim | Identificação básica | 10 anos |
| Email | Texto | Sim | Comunicação, login | 10 anos |
| Telefone | Texto | Sim | Verificação 2FA, contacto | 10 anos |
| Data nascimento | Data | Sim | Verificação idade ≥18 | 10 anos |
| País residência | País | Sim | Determinação jurisdição | 10 anos |
| IP registo | IP | Automático | Detecção fraudes, geolocalização | 2 anos |
| User-agent | Texto | Automático | Detecção dispositivos suspeitos | 2 anos |

### Critérios de Aceitação Imediata (SDD)

O subscritor é aceito automaticamente em SDD se:

1. **Idade confirmada**: Data de nascimento indica ≥18 anos
2. **País permitido**: Residência em jurisdição não bloqueada (ver matriz em REGULAMENTACAO_EU.md)
3. **Email válido**: Email verificado via link de confirmação (não temporário/disponível)
4. **Telefone único**: Não associado a >2 contas existentes
5. **IP limpo**: Não em lista negra de fraudes, não associado a >1 registo recente
6. **Sem PEP match**: Screening inicial contra lista PEP não retorna match

### Restrições SDD

Subscritores em SDD têm limitações automáticas:

- **Limite acumulado subscrições**: €250
- **Acesso a sinais**: Limitado a 1 sinal/dia
- **Sem acesso a métricas avançadas**: CLV detalhado, backtest completo
- **Pagamentos**: Apenas cartão de crédito/débito (não transferência bancária)

### Procedimento de Verificação Email

```
1. Sistema envia email com link de validação (token único, expira em 24h)
2. Subscritor clica no link
3. Sistema marca email como "VERIFICADO"
4. Se não validado em 7 dias: conta marcada como "PENDENTE_VERIFICACAO"
5. Se não validado em 30 dias: conta automaticamente cancelada
```

### Procedimento de Verificação Telefone

```
1. Sistema envia SMS com código de 6 dígitos (expira em 5 minutos)
2. Subscritor introduz código na aplicação
3. Sistema valida código
4. Máximo 3 tentativas por código
5. Após 3 falhas: bloqueio temporário (30 minutos) + requerimento de novo código
6. Após 5 falhas consecutivas: conta suspensa, requer revisão manual
```

---

## Fase 2: Verificação Identidade (CDD)

### Gatilho para CDD

O subscritor é escalado para CDD quando qualquer dos seguintes critérios é atingido:

1. **Limite financeiro**: Total pago ≥€250
2. **Upgrade de plano**: Subscritor solicita plano PRO ou superior
3. **Comportamento suspeito**: Padrões de uso que justificam verificação adicional
4. **Mudança jurisdição**: Subscritor altera país de residência para jurisdição de risco
5. **Período de tempo**: 90 dias após registo (verificação periódica obrigatória)

### Documentação Exigida

| Documento | Formatos Aceites | Validez Máxima | Verificação |
|-----------|------------------|----------------|-------------|
| Bilhete Identidade / Passaporte | PDF, JPG, PNG (max 10MB) | 5 anos (BI) / 10 anos (passaporte) | OCR + verificação hologramas |
| Comprovativo morada | PDF, JPG, PNG | 3 meses | Cross-check com endereço registo |
| Selfie com liveness | JPG, PNG (captura webcam) | - | Comparação facial + deteção vivacidade |

### Procedimento de Submissão Documentos

```
1. Sistema notifica subscritor via email/Telegram: "Escalonamento para CDD requerido"
2. Subscritor acede dashboard → secção "Verificação"
3. Upload de documentos um a um com preview
4. Sistema valida formato, tamanho, legibilidade
5. Se documento ilegível: rejeição automática com motivo específico
6. Se todos documentos válidos: submissão para verificação
7. Sistema marca conta como "PENDENTE_CDD"
8. Subscritor continua a ter acesso limitado durante verificação (não bloqueio total)
```

### Processo de Verificação Automática

```
1. Documento enviado para API de verificação (Onfido/Jumio/Trulioo)
2. API executa:
   a) OCR para extração de dados
   b) Verificação de autenticidade (hologramas, microprint, fontes)
   c) Extração de MRZ (Machine Readable Zone)
   d) Verificação contra bases de dados de documentos perdidos/roubados
3. Selfie enviada para comparação facial
4. API executa:
   a) Detecção de vivacidade (anti-spoofing)
   b) Comparação facial com fotografia do documento
   c) Verificação de idade via data nascimento
5. Resultado retornado em 30-120 segundos
```

### Categorias de Resultado Verificação

| Resultado | Significado | Ação Imediata | Revisão Humana |
|-----------|-------------|---------------|----------------|
| CLEAR | Documento autêntico, selfie corresponde | Aprovar CDD | Não (amostragem 10%) |
| CONSIDER | Pequenas discrepâncias, mas provavelmente válido | Pendente revisão | Sim, obrigatória |
| REJECTED | Documento falso, alterado, ou selfie não corresponde | Rejeitar CDD | Sim, confirmar |
| UNABLE_TO_VERIFY | Qualidade imagem insuficiente, erro técnico | Pedir novo upload | Não (automático) |

### Critérios de Aprovação CDD

Aprovação automática se:

1. **Resultado API**: CLEAR
2. **Idade confirmada**: ≥18 anos
3. **Nacionalidade**: País não em lista de sanções
4. **PEP screening**: Sem match ou match de baixo risco (ex: funcionário público local)
5. **Endereço consistente**: Comprovativo morada corresponde ao registo inicial

Se algum critério falhar → revisão manual obrigatória por Compliance Officer.

### Revisão Manual CDD

O Compliance Officer deve:

1. Rever todos os documentos submetidos
2. Cross-check manual de discrepâncias
3. Verificar dados adicionais se necessário (ex: pesquisa LinkedIn para confirmação profissional)
4. Documentar decisão no audit trail com justificação detalhada
5. Se aprovar: marcar conta como "CDD_VERIFICADO"
6. Se rejeitar: notificar subscritor com motivo específico + direito de recurso

### Timeline CDD

| Etapa | SLA | Responsável |
|-------|-----|-------------|
| Notificação de escalonamento | Imediata (threshold atingido) | Sistema |
| Submissão documentos pelo subscritor | 7 dias | Subscritor |
| Verificação automática | 2 minutos | Sistema (API) |
| Revisão manual (se necessária) | 48 horas | Compliance Officer |
| Decisão final | 72 horas após submissão completa | Compliance Officer |
| Notificação ao subscritor | Imediata após decisão | Sistema |

### Benefícios CDD

Subscritores verificados CDD obtêm:

- **Limite acumulado**: €2.500
- **Acesso completo**: Todos os sinais, métricas avançadas
- **Métodos pagamento**: Cartão + transferência bancária
- **Suporte prioritário**: Resposta em 24h
- **Acesso a comunidade**: Canal Telegram exclusivo

---

## Fase 3: Diligência Reforçada (EDD)

### Gatilho para EDD

O subscritor é escalado para EDD quando:

1. **Limite financeiro**: Total pago ≥€2.500
2. **PEP de alto risco**: Screening retorna match de PEP nível nacional/internacional
3. **Jurisdição de risco**: Residência em país FATF grey/black list
4. **Volume transacional**: Padrões de pagamento anormais (ex: >€10.000/mês)
5. **Atividade suspeita**: Alertas AML múltiplos ou de alta severidade
6. **Mudança perfil**: Alteração drástica de comportamento após período estável

### Documentação Adicional Exigida

| Documento | Finalidade | Validez | Verificação |
|-----------|------------|---------|-------------|
| Fonte de fundos | Origem lícita de recursos | 6 meses | Revisão manual |
| Declaração de rendimentos | Comprovação capacidade financeira | 1 ano | Cross-check se necessário |
| Proveniência de riqueza | Acumulação de capital ao longo do tempo | Vários anos | Revisão manual |
| Extrato bancário | Movimentos recentes relevantes | 3 meses | Verificação padrões |

### Tipos de Fonte de Fundos Aceites

1. **Rendimento profissional**: Declaração IRS, recibos verdes, contrato de trabalho
2. **Investimentos**: Extratos conta investimento, dividendos, mais-valias
3. **Herança/Doação**: Documento notarial, declaração do doador
4. **Venda de ativos**: Contrato promessa compra/venda, escritura
5. **Empréstimo**: Contrato de crédito bancário com comprovativo de receção

### Procedimento de Análise Fonte de Fundos

```
1. Subscritor submete documentação fonte de fundos
2. Compliance Officer analisa:
   a) Consistência com perfil declarado (profissão, rendimento)
   b) Plausibilidade do montante acumulado
   c) Red flags (ex: depósitos em cash frequentes, transferências de paraísos fiscais)
3. Se inconsistência: solicitar documentação adicional
4. Se suspeita de branqueamento: relatar à UIF/BdP (se aplicável) + bloquear conta
5. Se tudo consistente: aprovar EDD
```

### PEP Screening Detalhado

Para EDD, o PEP screening é mais rigoroso:

1. **Verificação múltiplas fontes**: World-Check, Dow Jones, LexisNexis
2. **Análise de relacionamentos**: Família próximo, associados de negócio
3. **Monitorização contínua**: Alertas se PEP muda de status
4. **Avaliação de risco**: PEP nível local vs. nacional vs. internacional

Categorias de risco PEP:

| Categoria | Risco | Ação |
|-----------|-------|------|
| PEP doméstico nível local | Baixo | EDD standard |
| PEP doméstico nível nacional | Médio | EDD + aprovação diretor |
| PEP estrangeiro | Alto | EDD + aprovação diretor + monitorização mensal |
| Família PEP estrangeiro | Médio-Alto | EDD + monitorização trimestral |
| PEP sancionado | Crítico | Bloqueio imediato |

### Timeline EDD

| Etapa | SLA | Responsável |
|-------|-----|-------------|
| Notificação de escalonamento | Imediata | Sistema |
| Submissão documentação adicional | 14 dias | Subscritor |
| Análise inicial | 72 horas | Compliance Officer |
| Solicitação documentação extra (se necessário) | 7 dias | Compliance Officer |
| Decisão final | 10 dias após submissão completa | Diretor Compliance |
| Notificação ao subscritor | Imediata após decisão | Sistema |

### Limitações EDD

Mesmo após aprovação EDD, podem aplicar-se:

- **Limites transacionais**: Teto diário/semanal de pagamento
- **Monitorização reforçada**: Alertas mais sensíveis
- **Revisão periódica**: Semestral em vez de anual
- **Aprovação prévia**: Para grandes pagamentos (ex: >€5.000)

---

## Fase 4: Monitorização Contínua

### Objetivos
- Detetar alterações de perfil ao longo do tempo
- Identificar comportamento suspeito emergente
- Assegurar que subscritores permanecem dentro do seu nível de risco

### Eventos que Disparam Reavaliação

1. **Mudança de dados pessoais**: Nome, morada, telefone
2. **Alteração profissional**: Nova profissão declarada
3. **Mudança de país**: Residência fiscal alterada
4. **Aumento drástico de volume**: Pagamentos >3x média histórica
5. **Padrões de uso anormais**: Atividade 24/7, múltiplos dispositivos
6. **Chargebacks ou disputas**: Qualquer incidente de pagamento
7. **Reclamações repetidas**: >2 reclamações em 30 dias

### Procedimento de Reavaliação

```
1. Evento dispara alerta no sistema
2. Compliance Officer recebe notificação
3. Análise do contexto:
   a) Justificação aparente? (ex: bónus anual explicando aumento de volume)
   b) Red flags presentes?
4. Se justificação clara: registo no audit trail, sem alteração de nível
5. se red flags: escalonamento para nível superior ou revisão manual
6. Subscritor notificado se nível alterado
```

### Revisão Periódica Obrigatória

| Nível KYC | Frequência Revisão | Documentos Requeridos | Ação se Não Cumprido |
|-----------|-------------------|----------------------|---------------------|
| SDD | 90 dias | Email/telefone re-verificados | Downgrade ou suspensão |
| CDD | 12 meses | Comprovativo morada atualizado | Suspensão de sinais |
| EDD | 6 meses | Fonte de fundos atualizada | Bloqueio de pagamentos |

### Procedimento de Revisão Anual CDD

```
1. Sistema notifica subscritor 30 dias antes da data de revisão
2. Subscritor submete comprovativo morada atual (<3 meses)
3. Sistema valida automaticamente:
   a) Endereço consistente com registo
   b) Documento legível e válido
4. Se válido: Renovar verificação por 12 meses
5. Se inválido: Pedir novo documento
6. Se não submetido em 14 dias: Suspender sinais
7. Se não submetido em 30 dias: Cancelar subscrição
```

---

## Exceções e Casos Especiais

### Menores de Idade

Se detetado subscritor <18 anos:

1. **Imediato**: Bloqueio total da conta
2. **Reembolso**: Devolução integral de pagamentos (se aplicável)
3. **Notificação**: Informar pais/responsáveis (se dados disponíveis)
4. **Registo**: Marcar no audit trail para prevenir futuros registos
5. **Denúncia**: Se houver evidência de evasão sistemática, considerar denúncia

### Jogadores Autoexcluídos

Se NIF detectado em lista SRIJ de autoexclusão:

1. **Bloqueio imediato**: Suspender conta
2. **Notificação**: Informar subscritor do bloqueio
3. **Reembolso prorata**: Devolução de dias não utilizados
4. **Registo**: Documentar no audit trail
5. **Não reativação**: Permanecer bloqueado até remoção da lista

### Duplas Contas

Se detetado mesmo subscritor com múltiplas contas:

1. **Investigação**: Determinar intenção (fraude vs. erro genuíno)
2. Se erro genuíno: Fundir contas, manter histórico
3. Se fraude (abuso promoções, evasão limites):
   a) Suspender todas as contas
   b) Reembolso prorata
   c) Bloqueio futuro

### Subscritores de Alto Risco AML

Se PEP de alto risco ou país de risco:

1. **EDD obrigatório**: Mesmo abaixo de threshold financeiro
2. **Aprovação diretor**: Requer aprovação explícita do Diretor de Compliance
3. **Monitorização mensal**: Revisão manual mensal de atividade
4. **Limites transacionais**: Teto de pagamento aplicável
5. **Direito de recusa**: Reserva-se o direito de recusar serviço

---

## Direitos do Subscritor

### Direito de Recurso

Se a verificação KYC for rejeitada, o subscritor pode:

1. **Solicitar revisão**: Em 14 dias após notificação
2. **Submeter documentação adicional**: Para clarificar discrepâncias
3. **Apelar à direção**: Se discordar da decisão do Compliance Officer
4. **Obter justificação detalhada**: Motivo específico da rejeição

### Direito à Retificação

Se dados pessoais estiverem incorretos:

1. **Solicitar correção**: Via dashboard ou email
2. **Comprovação**: Documento que suporte a correção
3. **Atualização**: Sistema atualizado em 48 horas
4. **Notificação**: Confirmação da alteração

### Direito ao Apagamento (Direito ao Esquecimento)

Após cancelamento, o subscritor pode solicitar apagamento:

1. **Verificação de obrigações legais**: Dados fiscais retidos por 10 anos
2. **Pseudonimização**: Dados comportamentais apagados, identificadores retidos
3. **Confirmação**: Notificação em 30 dias
4. **Exceções**: Litígios pendentes, obrigações legais

---

## Responsabilidades da Equipa

### Compliance Officer

- Rever manualmente 10% das verificações CDD aprovadas automaticamente
- Revisar 100% das verificações EDD
- Aprovar/rejeitar casos CONSIDER da API
- Realizar revisões periódicas de subscritores de alto risco
- Manter documentação KYC atualizada
- Formar equipa de operações em deteção de fraude

### Equipa de Operações

- Processar pedidos de verificação no SLA definido
- Responder a dúvidas de subscritores sobre KYC
- Monitorizar alertas do sistema
- Escalar casos suspeitos para Compliance Officer

### Equipa Técnica

- Manter integrações com APIs de verificação (Onfido, Jumio)
- Garantir uptime dos sistemas KYC
- Implementar melhorias de UX para reduzir fricção
- Manter segurança de documentos submetidos (encriptação)

---

## Métricas e KPIs

### KPIs de Processo KYC

| KPI | Target | Frequência Medição |
|-----|--------|-------------------|
| Tempo médio verificação CDD | <24 horas | Diário |
| Taxa de aprovação automática CDD | >85% | Mensal |
| Taxa de conversão SDD→CDD | >70% | Mensal |
| Tempo médio verificação EDD | <5 dias úteis | Semanal |
| Taxa de falsos positivos PEP | <5% | Mensal |
| SLA cumprimento (72h decisão) | >95% | Mensal |
| Satisfação subscritor (KYC) | >4/5 | Trimestral |

### Alertas Operacionais

- Se taxa aprovação automática <70%: Revisar critérios API
- Se SLA cumprimento <90%: Alocar recursos adicionais
- Se taxa conversão SDD→CDD <50%: Simplificar processo
- Se falsos positivos PEP >10%: Ajustar thresholds

---

## Links Cruzados

- [[16_Compliance/KYC_AML]] - Visão geral técnica do sistema KYC/AML
- [[16_Compliance/AUDIT_TRAIL_COMPLIANCE]] - Registo de todas as decisões KYC
- [[16_Compliance/REGULAMENTACAO_PT]] - Obrigações legais específicas Portugal
- [[16_Compliance/REGULAMENTACAO_EU]] - Matriz de jurisdições europeias
- [[17_Legal/PRIVACY_POLICY]] - Tratamento de dados biométricos
- [[34_Security/SECRETS_MANAGEMENT]] - Proteção de documentos sensíveis