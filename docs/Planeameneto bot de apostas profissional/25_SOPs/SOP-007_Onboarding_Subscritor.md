# SOP-007 — Onboarding de Subscritor

**ID:** `SOP-007` | **Fase:** #phase/10+ | **Owner:** Product Manager | **Status:** #status/pending

---

## 1. OBJETIVO

Procedimento para onboarding de novos subscritores.

---

## 2. CHECKLIST

- [ ] Receber pedido de subscrição
- [ ] Verificar KYC/AML
- [ ] Assinar acordo de subscrição
- [ ] Configurar conta no sistema
- [ ] Definir limites de stake
- [ ] Configurar alertas personalizados
- [ ] Fornecer acesso ao dashboard
- [ ] Treinar subscritor

---

## 3. PROCEDIMENTO DETALHADO

### 3.1 Receber Pedido de Subscrição

- Subscritor envia pedido via formulário ou email
- Verificar disponibilidade: máximo 100 subscritores ativos (ver `02_Business_Model/INDEX`)
- Se quota atingida: adicionar à lista de espera

### 3.2 Verificar KYC/AML (Fase 10+ — simplificado no início)

- Pedir: nome completo, morada, identificação (CC/passaporte)
- Verificar se não está em listas de sanções (OFAC, UE)
- Guardar documentação encriptada em `16_Compliance/KYC/`
- **Nota:** Em Fase 5-9, KYC é manual. Automatização planeada para Fase 10+.

### 3.3 Assinar Acordo de Subscrição

- Enviar `SUBSCRICAO_AGREEMENT.md` (disclaimer de risco incluído)
- Subscritor assina digitalmente (DocuSign ou similar)
- Guardar cópia assinada em `16_Compliance/Contratos/`

### 3.4 Configurar Conta no Sistema

```bash
# Criar registo na base de dados
python scripts/create_subscriber.py \
  --name "Nome Subscritor" \
  --email "subscritor@email.com" \
  --phone "+3519XXXXXXXX" \
  --start_date $(date +%Y-%m-%d) \
  --tier "unico"

# Gerar ID único de subscritor
# Formato: SUB-XXX (ex: SUB-001)
```

### 3.5 Definir Limites de Stake

- Stake máxima por aposta: 2% do bankroll do subscritor
- Exposição máxima diária: 12% do bankroll
- Limites definidos no `meta.subscriber_limits`

```bash
python scripts/set_subscriber_limits.py --subscriber-id SUB-001 --max-stake-pct 2.0 --max-daily-pct 12.0
```

### 3.6 Configurar Alertas Personalizados

- Adicionar ao canal Telegram de sinais
- Configurar alertas de circuit breaker (se subscritor quiser)
- Definir preferência de notificações: todas / apenas high-edge / digest diário

```bash
python scripts/add_telegram_subscriber.py --chat-id CHAT_ID --subscriber-id SUB-001
```

### 3.7 Treinar Subscritor

- Enviar guia de boas-vindas (baseado em `GETTING_STARTED.md` adaptado para subscritores)
- Explicar: Kelly fracionado, gestão de bankroll, importância do edge
- Estabelecer expectativas realistas: CLV médio > 2%, drawdown máximo 15%
- Fornecer acesso ao dashboard de performance (Grafana read-only)

---

## 4. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
