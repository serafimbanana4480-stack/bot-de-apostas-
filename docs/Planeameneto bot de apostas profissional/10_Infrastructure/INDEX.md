# 10_Infrastructure — INDEX

**ID:** `SEC-10` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/complete

---

## 1. OBJETIVO

Documentar a infraestrutura técnica do sistema: servidores, redes, monitorização, e escalabilidade.

---

## 2. DOCUMENTAÇÃO

| ID | Documento | Descrição | Custo |
|----|-----------|-----------|-------|
| INF-001 | [[ARQUITETURA_MONITORIZACAO]] | Arquitetura de monitorização do sistema | 0€ |
| INF-002 | [[DASHBOARD_NEGOCIO]] | Dashboard de métricas de negócio | 0€ |
| INF-003 | [[METRICAS_DETALHADAS]] | Métricas técnicas detalhadas | 0€ |
| **INF-004** | [[VPS_CONFIGURACAO]] | **Configuração de VPS 100% gratuito (Oracle Cloud)** | **0€** |
| **INF-005** | [[NETWORKING]] | **Configuração de rede e firewall (UFW, fail2ban)** | **0€** |
| **INF-006** | [[BACKUP_ESTRATEGY]] | **Estratégia de backup (local + cloud gratuita)** | **0€** |
| **INF-007** | [[DISASTER_RECOVERY]] | **Plano de recuperação de disaster (RTO 4h)** | **0€** |
| **INF-008** | [[MONITORIZACAO_INFRA]] | **Monitorização de infraestrutura (Prometheus + Grafana)** | **0€** |

---

## 3. RESUMO DE CUSTOS

| Componente | Custo Mensal |
|-------------|--------------|
| VPS (Oracle Cloud Free Tier) | **0€** |
| Backup (OCI Object Storage 10GB) | **0€** |
| Monitorização (Prometheus + Grafana OSS) | **0€** |
| Rede (DuckDNS + Let's Encrypt) | **0€** |
| **TOTAL INFRAESTRUTURA** | **0€/mês** |

---

## 4. BACKLOG (Concluído ✓)

- [x] Documentar configuração VPS → [[VPS_CONFIGURACAO]]
- [x] Documentar setup de redes → [[NETWORKING]]
- [x] Documentar estratégias de backup → [[BACKUP_ESTRATEGY]]
- [x] Documentar procedimentos de disaster recovery → [[DISASTER_RECOVERY]]
- [x] Documentar monitorização de infraestrutura → [[MONITORIZACAO_INFRA]]

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[13_Infrastructure]] → Infraestrutura detalhada
- [[12_DevOps]] → DevOps e CI/CD
