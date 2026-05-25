# SOP-008 — Offboarding de Subscritor

**ID:** `SOP-008` | **Fase:** #phase/10+ | **Owner:** Product Manager | **Status:** #status/pending

---

## 1. OBJETIVO

Procedimento para offboarding de subscritores.

---

## 2. CHECKLIST

- [ ] Receber pedido de cancelamento
- [ ] Parar novas apostas para subscritor
- [ ] Liquidar posições abertas
- [ ] Calcular PnL final
- [ ] Processar reembolso
- [ ] Revogar acesso ao sistema
- [ ] Arquivar documentação
- [ ] Solicitar feedback

---

## 3. PROCEDIMENTO DETALHADO

### 3.1 Receber Pedido de Cancelamento

- Subscritor envia pedido de cancelamento (email ou Telegram)
- Confirmar receção em até 24h
- Verificar data de início para calcular reembolso proporcional (se aplicável)

### 3.2 Parar Novas Apostas para Subscritor

```bash
# Desativar subscritor no sistema
python scripts/deactivate_subscriber.py --subscriber-id SUB-XXX

# Verificar se sinais pendentes foram cancelados
python scripts/check_subscriber_signals.py --subscriber-id SUB-XXX
```

**Critério:** 0 sinais pendentes após desativação.

### 3.3 Calcular PnL Final

- Obter PnL acumulado desde o início da subscrição
- Calcular reembolso proporcional (se subscritor cancelar nos primeiros 14 dias)
- Gerar relatório final de performance

```bash
python scripts/generate_subscriber_final_report.py --subscriber-id SUB-XXX
```

### 3.4 Processar Reembolso (se aplicável)

- Se dentro do período de reembolso: processar via Stripe/PayPal
- Se fora do período: não há reembolso (cláusula no acordo)
- Documentar transação em `35_Financial_Tracking/`

### 3.5 Revogar Acesso ao Sistema

```bash
# Remover do canal Telegram de sinais
python scripts/remove_telegram_subscriber.py --subscriber-id SUB-XXX

# Desativar dashboard
python scripts/disable_dashboard_access.py --subscriber-id SUB-XXX

# Marcar como "inactive" na base de dados
python scripts/archive_subscriber.py --subscriber-id SUB-XXX
```

### 3.6 Arquivar Documentação

- Mover contrato assinado para `16_Compliance/Contratos/Arquivados/`
- Guardar relatório final de performance em `35_Financial_Tracking/Subscritores/`
- Manter registos por 5 anos (obrigatório legalmente em PT)

### 3.7 Solicitar Feedback

- Enviar questionário de saída (opcional, incentivado)
- Perguntar: razão de saída, satisfação, sugestões
- Utilizar feedback para melhorar produto

---

## 4. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
