# GDPR — Compliance GDPR

**ID:** `CMP-001` | **Fase:** #phase/10+ | **Owner:** Legal Counsel | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar compliance com GDPR para operação na UE.

---

## 2. PRINCÍPIOS GDPR APLICÁVEIS

### 2.1 Dados Recolhidos
| Dado | Finalidade | Base Legal |
|------|-----------|------------|
| Nome, email, telefone | Gestão de subscrição, comunicação | Consentimento (Art. 6(1)(a)) |
| Dados de apostas (histórico) | Análise de performance, melhoria do modelo | Legítimo interesse (Art. 6(1)(f)) |
| Endereço IP | Segurança, prevenção de fraude | Legítimo interesse |
| Dados de pagamento | Processamento de subscrições | Execução de contrato (Art. 6(1)(b)) |

### 2.2 Direitos dos Utilizadores
- **Acesso:** Fornecer cópia de todos os dados pessoais em 30 dias
- **Retificação:** Corrigir dados incorretos em 30 dias
- **Apagamento (direito ao esquecimento):** Apagar dados quando não há justificativa legal para retenção
- **Portabilidade:** Fornecer dados em formato estruturado (CSV/JSON)
- **Oposição:** Respeitar opção de não receber marketing

### 2.3 Medidas Técnicas
- Encriptação de dados em repouso (PostgreSQL TDE)
- Encriptação de dados em trânsito (TLS 1.3)
- Pseudonimização de dados sensíveis
- Logs de acesso auditáveis
- Retenção máxima: 5 anos para dados fiscais, 1 ano para dados de marketing

## 3. BACKLOG

- [x] Definir política de privacidade
- [x] Implementar consentimento de utilizadores
- [ ] Configurar direito ao esquecimento (automatizado)
- [x] Documentar processamento de dados

---

## 4. LINKS CRUZADOS

- [[16_Compliance/INDEX]] ← Secção mãe
- [[16_Compliance/PRIVACY_POLICY]] → Política de privacidade pública
