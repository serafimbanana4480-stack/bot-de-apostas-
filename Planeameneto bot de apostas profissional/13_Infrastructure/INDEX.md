# 13_Infrastructure — INDEX

**ID:** `SEC-13` | **Fase:** #phase/1-15 | **Owner:** DevOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Gerir a infraestrutura de hardware e serviços que suportam o sistema. Manter custos controlados, performance aceitável, e capacidade de escalar quando o edge justificar.

---

## 2. NOTAS FUNDAMENTAIS

- [[VPS_CONFIGURACAO]] — Especificação do servidor, OS, tuning
- [[REDIS_CONFIG]] — Cache, filas, rate limiting
- [[POSTGRES_CONFIG]] — Tuning, backups, replicação (futuro)
- [[CUSTOS_INFRA]] — Tracking de custos mensais, projeções
- [[ESCALABILIDADE]] — Quando e como escalar vertical/horizontal
- [[DISASTER_RECOVERY]] — Backups, restore points, RTO/RPO

---

## 3. STACK INFRASTRUTURAL MVP

| Componente | Especificação MVP | Custo Mensal | Quando Escalar |
|------------|-------------------|--------------|----------------|
| VPS | 4 vCPU AMD, 8 GB RAM, 160 GB SSD (Hetzner CPX31) | ~12€ | Quando CPU > 70% sustained → upgrade para CPX51 (8vCPU, 16GB) ~28€ |
| PostgreSQL | Instância local no VPS | Incluído | Separar para RDS/managed quando > 500GB |
| Redis | Instância local no VPS | Incluído | Separar para Elasticache quando cluster |
| Storage | SSD local + backups S3 (futuro) | ~5€ | Quando dados > 200GB |
| Monitoring | Prometheus + Grafana local | Incluído | SaaS quando equipa > 3 pessoas |

**Total MVP:** ~17€/mês (incluindo storage)

---

## 4. BACKLOG TÉCNICO

- [ ] Aprovisionar VPS e configurar OS (Ubuntu 22.04 LTS)
- [ ] Instalar e configurar PostgreSQL 15
- [ ] Instalar e configurar Redis
- [ ] Configurar firewall (UFW) e SSH hardening
- [ ] Criar scripts de backup automatizado
- [ ] Documentar procedimentos de disaster recovery

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[12_DevOps/INDEX]] → Deploy e automação
- [[15_Database/INDEX]] → Schema e tuning de BD
