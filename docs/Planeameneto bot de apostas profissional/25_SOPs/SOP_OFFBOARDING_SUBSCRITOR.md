# SOP_OFFBOARDING_SUBSCRITOR — Procedimento Operacional Padrão

**ID:** `SOP-008` | **Fase:** #phase/5 | **Owner:** Customer Success | **Status:** #status/active
**Última Revisão:** 2024-05-13 | **Próxima Revisão:** 2024-08-13

---

## 1. OBJETIVO

Estabelecer um processo padronizado para offboarding de subscritores que cancelam a subscrição, garantindo que o acesso é revogado de forma segura, que os dados são retidos conforme a política de retenção, e que a experiência é profissional para minimizar churn negativo.

---

## 2. APLICAÇÃO

**Quando executar:**
- Quando subscritor solicita cancelamento
- Quando subscritor não renova subscrição
- Quando subscritor viola termos de serviço
- Quando subscritor é inativo por > 90 dias

**Responsável:**
- Customer Success Manager
- Operations Lead (revogação de acesso)

**Duração estimada:**
- 30-60 minutos

---

## 3. PRÉ-REQUISITOS

- [ ] Solicitação de cancelamento recebida
- [ ] Motivo de cancelamento documentado
- [ ] Data de término de subscrição confirmada

---

## 4. PROCEDIMENTO DETALHADO

### 4.1. Verificação e Confirmação (15 minutos)

**Passos:**

1. **Verificar solicitação:**
   - [ ] Confirmar que solicitação veio do subscritor
   - [ ] Confirmar motivo de cancelamento
   - [ ] Confirmar data de término

2. **Oferecer retenção (opcional):**
   - [ ] Se cancelamento por preço: oferecer desconto
   - [ ] Se cancelamento por insatisfação: oferecer solução
   - [ ] Documentar resultado da oferta

### 4.2. Revogação de Acesso (15 minutos)

**Passos:**

1. **Revogar acesso ao Telegram:**
   - [ ] Remover subscritor do canal de sinais
   - [ ] Verificar que não tem acesso a canais privados

2. **Revogar acesso ao dashboard:**
   - [ ] Desativar conta de utilizador
   - [ ] Revogar tokens de API
   - [ ] Remover permissões

3. **Atualizar base de dados:**
   ```sql
   UPDATE subscribers
   SET status = 'CANCELLED',
       end_date = NOW(),
       cancellation_reason = '[motivo]'
   WHERE user_id = '[user_id]';
   ```

### 4.3. Processamento Financeiro (15 minutos)

**Passos:**

1. **Verificar pagamento:**
   - [ ] Confirmar se pagamento recorrente deve ser cancelado
   - [ ] Cancelar pagamento recorrente no gateway
   - [ ] Confirmar que não serão feitos cobranças futuras

2. **Processar reembolso (se aplicável):**
   - [ ] Se reembolso devido: processar
   - [ ] Documentar valor e data de reembolso
   - [ ] Notificar subscritor

### 4.4. Retenção de Dados (15 minutos)

**Passos:**

1. **Arquivar dados:**
   - [ ] Exportar dados do subscritor para arquivo
   - [ ] Guardar histórico de apostas
   - [ ] Guardar histórico de pagamentos

2. **Eliminar dados sensíveis:**
   - [ ] Eliminar dados de pagamento
   - [ ] Eliminar dados pessoais não essenciais
   - [ ] Manter dados conforme política de retenção (GDPR)

### 4.5. Comunicação (15 minutos)

**Passos:**

1. **Enviar confirmação:**
   - [ ] Enviar email confirmando cancelamento
   - [ ] Incluir data de término
   - [ ] Incluir informações sobre retenção de dados

2. **Solicitar feedback (opcional):**
   - [ ] Enviar survey de cancelamento
   - [ ] Pedir feedback sobre como melhorar

3. **Oferecer reativação (opcional):**
   - [ ] Informar que podem reativar a qualquer momento
   - [ ] Oferecer incentivo para reativação

---

## 5. CHECKLIST FINAL

- [ ] Solicitação verificada
- [ ] Acesso ao Telegram revogado
- [ ] Acesso ao dashboard revogado
- [ ] Base de dados atualizada
- [ ] Pagamento recorrente cancelado
- [ ] Dados arquivados
- [ ] Dados sensíveis eliminados
- [ ] Confirmação enviada
- [ ] Feedback solicitado

---

## 6. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
- [[16_Compliance/GDPR]] → Política de retenção de dados