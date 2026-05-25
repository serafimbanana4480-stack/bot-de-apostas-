# TPL-005 — Standard Operating Procedure (SOP)

**ID:** `SOP-XXX`  
**Título:** *Título descritivo do procedimento*  
**Versão:** `v1.0`  
**Área:** #area/ops / #area/ml / #area/data / #area/exec / #area/infra  
**Owner:** *Nome do responsável*  
**Aprovado por:** *Nome do aprovador*  
**Data de Aprovação:** *YYYY-MM-DD*  
**Próxima Revisão:** *YYYY-MM-DD*

---

## 1. RESUMO EXECUTIVO

| Campo | Descrição |
|-------|-----------|
| **O que é?** | *Breve descrição do procedimento* |
| **Quando usar?** | *Condições que acionam este SOP* |
| **Quem executa?** | *Papel/role necessário* |
| **Tempo estimado** | *X minutos/horas* |
| **Risco se não seguido** | *Consequências de omissão* |

---

## 2. OBJETIVO E ÂMBITO

### 2.1 Objetivo
*Descrição detalhada do que este SOP pretende alcançar*

### 2.2 Âmbito
**Inclui:**
- *Situação A*
- *Situação B*

**Exclui:**
- *Situação C (ver SOP-YYY)*
- *Situação D (ver SOP-ZZZ)*

### 2.3 Referências Normativas
- [[SOP-YYY]] — *Procedimento relacionado*
- [[RB-XXX]] — *Runbook de emergência*
- [[DOC-POLICY]] — *Política aplicável*

---

## 3. RESPONSABILIDADES

| Papel | Responsabilidade | Requisitos |
|-------|------------------|------------|
| **Executor** | *Executar o procedimento conforme documentado* | *Treino SOP-XXX* |
| **Reviewer** | *Verificar execução correta* | *Senior na área* |
| **Owner do SOP** | *Manter SOP atualizado* | *Conhecimento profundo* |

---

## 4. PRÉ-REQUISITOS

### 4.1 Acessos Necessários
- [ ] *Sistema A: permissão de read/write*
- [ ] *Sistema B: permissão de admin*
- [ ] *Ferramenta C: conta ativa*

### 4.2 Ferramentas e Recursos
| Ferramenta | Versão | Onde Obter |
|------------|--------|------------|
| *Ex: psql* | *15.x* | *Instalado no servidor* |
| *Ex: Docker* | *24.x* | *Pre-instalado* |

### 4.3 Conhecimento Prévio
- [ ] *Conhecimento A (ex: SQL básico)*
- [ ] *Conhecimento B (ex: Docker compose)*
- [ ] *Treino prévio: [link para material de treino]*

### 4.4 Preparação do Ambiente
```bash
# Verificar ambiente
./scripts/verify-env.sh

# Output esperado:
# ✅ PostgreSQL: OK
# ✅ Redis: OK
# ✅ API: OK
```

---

## 5. PROCEDIMENTO DETALHADO

### 5.1 Preparação (Pre-Flight)

#### Checklist de Segurança
- [ ] Backup realizado (se aplicável)
- [ ] Janela de manutenção comunicada (se aplicável)
- [ ] Rollback plan identificado

#### Validação Inicial
```bash
# Comando de validação
make health-check

# Esperado: Todos os serviços OK
```

### 5.2 Execução Principal

#### Passo 1: [Nome do Passo]
**Duração estimada:** *X minutos*

**Instruções:**
1. *Ação detalhada 1*
   ```bash
   # Comando exemplo com placeholders
   comando --parametro [VALOR]
   ```

2. *Ação detalhada 2*
   ```sql
   -- Query exemplo
   SELECT * FROM tabela WHERE condicao = 'valor';
   ```

3. *Ação detalhada 3*

**Checkpoint:**
- [ ] *Critério de sucesso verificado*
- [ ] *Output esperado confirmado*

#### Passo 2: [Nome do Passo]
**Duração estimada:** *X minutos*

**Instruções:**
1. 
2. 
3. 

**Checkpoint:**
- [ ] 
- [ ] 

#### Passo 3: [Nome do Passo]
**Duração estimada:** *X minutos*

**Instruções:**
1. 
2. 
3. 

**Checkpoint:**
- [ ] 
- [ ] 

### 5.3 Verificação Pós-Execução (Post-Flight)

#### Checklist de Validação
- [ ] *Critério A verificado (como: comando/output)*
- [ ] *Critério B verificado*
- [ ] *Critério C verificado*

#### Testes de Sanidade
```bash
# Teste 1: Verificar X
curl http://api/health
# Esperado: {"status": "healthy"}

# Teste 2: Verificar Y
docker compose ps
# Esperado: Todos os serviços UP

# Teste 3: Verificar Z
psql -c "SELECT COUNT(*) FROM tabela;"
# Esperado: N > 0
```

---

## 6. VERIFICAÇÃO E EVIDÊNCIAS

### 6.1 Critérios de Aceitação
| Critério | Como Verificar | Evidence Required |
|----------|----------------|-------------------|
| *Critério A* | *Comando/teste* | *Screenshot/log* |
| *Critério B* | *Query/métrica* | *Output guardado* |

### 6.2 Registo de Execução

**Template para preencher:**
```
Data: YYYY-MM-DD
Executor: [Nome]
Reviewer: [Nome]
Ambiente: [dev/staging/prod]
Resultado: [Sucesso/Falha]
Desvios: [N/A ou descrição]
Tempo Total: X minutos
```

---

## 7. EXCEÇÕES, PROBLEMAS E ESCALADA

### 7.1 Problemas Conhecidos

| Problema | Sintoma | Causa Provável | Solução |
|----------|---------|----------------|---------|
| *Erro X* | *Mensagem Y* | *Condição Z* | *Ver RB-XXX* |

### 7.2 Quando Escalar

| Situação | Contactar | Meio | Urgência |
|----------|-----------|------|----------|
| *Erro não documentado* | *Tech Lead* | *Slack* | *High* |
| *Timeout > 10min* | *Senior On-call* | *Telegram* | *Critical* |

### 7.3 Rollback
**Se a execução falhar no Passo X:**
1. *Ação de rollback 1*
2. *Ação de rollback 2*
3. *Verificar estado do sistema*
4. *Contactar Owner do SOP*

---

## 8. ANEXOS

### Anexo A: Comandos de Referência
```bash
# Comando útil 1
docker compose logs --tail=100 [serviço]

# Comando útil 2
psql -U vb_admin -d valuebetting -c "[QUERY]"

# Comando útil 3
make status
```

### Anexo B: Contactos de Suporte
| Papel | Nome | Contacto |
|-------|------|----------|
| *Owner SOP* | *Nome* | *Email/Slack* |
| *Backup* | *Nome* | *Email/Slack* |

---

## 9. TREINO E CERTIFICAÇÃO

### 9.1 Requisitos de Treino
- [ ] *Leitura deste SOP (100%)*
- [ ] *Shadow de execução com experiente (3x)*
- [ ] *Execução supervisionada (2x)*
- [ ] *Execução independente (1x)*
- [ ] *Aprovação em quiz (80%+)*

### 9.2 Recertificação
- **Frequência:** *Anual*
- **Quando:** *Se houver alteração de versão major*

---

## 10. HISTÓRICO DE REVISÕES

| Data | Versão | Alteração | Autor | Aprovador |
|------|--------|-----------|-------|-----------|
| *YYYY-MM-DD* | *v1.0* | *Criação inicial* | *Nome* | *Nome* |
| *YYYY-MM-DD* | *v1.1* | *Adicionado Passo 4* | *Nome* | *Nome* |
| *YYYY-MM-DD* | *v2.0* | *Major revisão* | *Nome* | *Nome* |

---

## 11. APROVAÇÕES

| Papel | Nome | Assinatura | Data |
|-------|------|------------|------|
| **Owner** | | | |
| **QA/Reviewer** | | | |
| **Manager** | | | |

---

## 12. REFERÊNCIAS

- [[25_SOPs/INDEX]] ← Todos os SOPs
- [[RB-XXX]] → Runbook de emergência relacionado
- [[TEMPLATE_RUNBOOK]] → Template para criar runbooks

---

**⚠️ ATENÇÃO:**
- Não executar sem treino prévio validado
- Sempre executar checklist de segurança
- Documentar desvios deste SOP
- Manter evidências de execução por 1 ano
