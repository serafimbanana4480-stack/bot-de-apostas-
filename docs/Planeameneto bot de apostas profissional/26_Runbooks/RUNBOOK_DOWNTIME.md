# RUNBOOK_DOWNTIME — Recuperação de Incidentes

**ID:** `RB-001` | **Fase:** #phase/1-15 | **Owner:** DevOps Engineer | **Status:** #status/active
**Última Revisão:** 2024-05-13 | **Próxima Revisão:** 2024-08-13

---

## 1. OBJETIVO

Fornecer um guia passo-a-passo para recuperação de incidentes de downtime no sistema de value betting NBA, incluindo falhas de infraestrutura, serviços offline, e componentes indisponíveis. Este runbook deve ser seguido sistematicamente para minimizar o tempo de recuperação e prevenir perda de dados.

---

## 2. ESTRUTURA DO RUNBOOK

Cada secção segue o formato:
- **Sintoma:** Como detetar o problema
- **Impacto:** O que está em risco
- **Mitigação Imediata:** O que fazer em 5 minutos
- **Diagnóstico:** Como encontrar a causa
- **Resolução:** Como corrigir
- **Verificação:** Como confirmar que está resolvido
- **Escalada:** Quem contactar se não resolver

---

## 3. SINTOMA 1: VPS Offline (Sistema Indisponível)

### 3.1. Sintoma
- Dashboard Grafana inacessível
- SSH não conecta
- Ping ao VPS falha
- Alertas P1 de infraestrutura

### 3.2. Impacto
- Sistema completamente offline
- Perda de sinais durante downtime
- Perda de potencial PnL
- Insatisfação de subscritores

### 3.3. Mitigação Imediata (0-5 minutos)
1. Tentar ping: `ping <vps_ip>`
2. Tentar SSH: `ssh user@<vps_ip>`
3. Se falhar: contactar fornecedor de VPS imediatamente
4. Notificar equipa via Telegram ops_alertas: "VPS offline, a investigar"

### 3.4. Diagnóstico (5-15 minutos)
1. Verificar status no painel do fornecedor de VPS
2. Verificar se há incidentes reportados pelo fornecedor
3. Verificar se fatura foi paga
4. Verificar se há violação de termos de serviço
5. Verificar se houve ataque DDoS

### 3.5. Resolução (15-60 minutos)

**Caso: VPS desligado (shutdown)**
1. Aceder ao painel do fornecedor
2. Iniciar VPS: botão "Start" ou "Power On"
3. Aguardar inicialização (2-5 minutos)
4. Verificar conectividade: `ping <vps_ip>`

**Caso: VPS suspender (falta de pagamento)**
1. Pagar fatura pendente
2. Aguardar processamento (5-10 minutos)
3. Solicitar reativação ao suporte
4. Após reativação: verificar serviços

**Caso: VPS em manutenção pelo fornecedor**
1. Verificar ETA de conclusão
2. Notificar equipa com ETA
3. Se ETA > 1 hora: considerar failover para backup

**Caso: VPS comprometido (ataque)**
1. Contactar fornecedor imediatamente
2. Solicitar isolamento do VPS
3. Iniciar procedimento de recuperação de desastre
4. Verificar integridade dos dados

### 3.6. Verificação (5-10 minutos)
1. SSH para VPS: `ssh user@<vps_ip>`
2. Verificar status dos serviços: `systemctl status postgresql redis docker`
3. Verificar logs de erro: `journalctl -xe`
4. Verificar que dashboard Grafana está acessível
5. Verificar que motor de decisão está a correr

### 3.7. Escalada
- Se não resolvido em 15 minutos: Escalar para Operations Lead
- Se não resolvido em 30 minutos: Escalar para CTO
- Se não resolvido em 60 minutos: Considerar declarar incidente maior

---

## 4. SINTOMA 2: PostgreSQL Down

### 4.1. Sintoma
- Serviços que acedem à BD falham
- Alertas P1 de PostgreSQL
- Logs mostram erros de conexão à BD
- Dashboard mostra "Database Error"

### 4.2. Impacto
- Perda de acesso a todos os dados
- Motor de decisão não funciona
- Sistema de sinais inoperacional
- Perda de dados se não houver backup recente

### 4.3. Mitigação Imediata (0-5 minutos)
1. Verificar status: `systemctl status postgresql`
2. Se down: tentar reiniciar: `sudo systemctl restart postgresql`
3. Verificar logs: `journalctl -u postgresql -n 50`
4. Notificar equipa: "PostgreSQL down, a tentar reiniciar"

### 4.4. Diagnóstico (5-15 minutos)
1. Verificar logs de erro: `/var/log/postgresql/postgresql-*.log`
2. Verificar espaço em disco: `df -h`
3. Verificar memória disponível: `free -h`
4. Verificar se há processos zombie: `ps aux | grep postgres`
5. Verificar configuração: `/etc/postgresql/*/main/postgresql.conf`

### 4.5. Resolução (15-60 minutos)

**Caso: Serviço parado**
1. Reiniciar: `sudo systemctl restart postgresql`
2. Verificar status: `systemctl status postgresql`
3. Se falhar: verificar logs para causa

**Caso: Disco cheio**
1. Identificar ficheiros grandes: `du -sh /*`
2. Limpar logs antigos: `rm /var/log/postgresql/postgresql-*.log.old`
3. Limpar caches: `docker system prune -a`
4. Reiniciar PostgreSQL

**Caso: Memória insuficiente**
1. Identificar processos que consomem memória: `top`
2. Parar serviços não essenciais
3. Aumentar swap se necessário
4. Reiniciar PostgreSQL

**Caso: Corrupção de dados**
1. Tentar recuperação automática: `sudo -u postgres psql -c "REINDEX DATABASE nba_betting;"`
2. Se falhar: restaurar do backup mais recente (ver SOP-009)
3. Verificar integridade após restore

### 4.6. Verificação (5-10 minutos)
1. Conectar à BD: `sudo -u postgres psql`
2. Verificar bases de dados: `\l`
3. Verificar tabelas: `\dt`
4. Executar query de teste: `SELECT COUNT(*) FROM games;`
5. Verificar que serviços conectam

### 4.7. Escalada
- Se não resolvido em 15 minutos: Escalar para DBA
- Se não resolvido em 30 minutos: Escalar para Operations Lead
- Se dados corrompidos: Escalar para CTO imediatamente

---

## 5. SINTOMA 3: Redis Down

### 5.1. Sintoma
- Serviços que usam cache falham
- Alertas P1 de Redis
- Logs mostram erros de conexão ao Redis
- Performance degradada (cache miss rate alta)

### 5.2. Impacto
- Performance degradada
- Aumento de carga na BD
- Latência de predições aumentada
- Possível perda de dados em cache

### 5.3. Mitigação Imediata (0-5 minutos)
1. Verificar status: `systemctl status redis`
2. Se down: tentar reiniciar: `sudo systemctl restart redis`
3. Verificar logs: `journalctl -u redis -n 50`
4. Notificar equipa: "Redis down, a tentar reiniciar"

### 5.4. Diagnóstico (5-15 minutos)
1. Verificar logs: `/var/log/redis/redis-server.log`
2. Verificar espaço em disco: `df -h`
3. Verificar memória disponível: `free -h`
4. Verificar configuração: `/etc/redis/redis.conf`

### 5.5. Resolução (15-30 minutos)

**Caso: Serviço parado**
1. Reiniciar: `sudo systemctl restart redis`
2. Verificar status: `systemctl status redis`

**Caso: Disco cheio**
1. Limpar dados antigos: `redis-cli FLUSHDB` (cuidado!)
2. Configurar maxmemory no redis.conf
3. Reiniciar Redis

**Caso: Corrupção de dados**
1. Parar Redis: `sudo systemctl stop redis`
2. Remover dump corrompido: `rm /var/lib/redis/dump.rdb`
3. Reiniciar Redis (irá começar vazio)
4. Sistema irá repopular cache automaticamente

### 5.6. Verificação (5-10 minutos)
1. Conectar ao Redis: `redis-cli`
2. Verificar info: `INFO`
3. Verificar memória: `INFO memory`
4. Testar set/get: `SET test "hello"; GET test`

### 5.7. Escalada
- Se não resolvido em 15 minutos: Escalar para DevOps
- Se não resolvido em 30 minutos: Escalar para Operations Lead

---

## 6. SINTOMA 4: Docker Containers Down

### 6.1. Sintoma
- Serviços específicos não respondem
- `docker ps` mostra menos containers que esperado
- Alertas de containers down
- Logs mostram erros de containers

### 6.2. Impacto
- Serviços específicos indisponíveis
- Dependendo do container: impacto parcial ou total
- Perda de funcionalidade específica

### 6.3. Mitigação Imediata (0-5 minutos)
1. Verificar containers: `docker ps -a`
2. Identificar containers down
3. Tentar reiniciar: `docker restart <container_name>`
4. Verificar logs: `docker logs <container_name> --tail 50`

### 6.4. Diagnóstico (5-15 minutos)
1. Verificar logs do container: `docker logs <container_name>`
2. Verificar se há erros de configuração
3. Verificar se há dependências faltando
4. Verificar se há conflitos de portas

### 6.5. Resolução (15-30 minutos)

**Caso: Container crashou**
1. Verificar logs para causa
2. Se erro temporário: reiniciar container
3. Se erro de configuração: corrigir configuração
4. Se erro de código: corrigir código, rebuild image

**Caso: Imagem não existe**
1. Pull da imagem: `docker pull <image_name>`
2. Reiniciar container

**Caso: Conflito de portas**
1. Identificar porta em uso: `netstat -tulpn`
2. Parar serviço conflituoso ou mudar porta
3. Reiniciar container

### 6.6. Verificação (5-10 minutos)
1. Verificar containers a correr: `docker ps`
2. Verificar health check: `docker inspect <container_name> | grep Health`
3. Testar funcionalidade do serviço

### 6.7. Escalada
- Se não resolvido em 15 minutos: Escalar para DevOps
- Se não resolvido em 30 minutos: Escalar para Operations Lead

---

## 7. SINTOMA 5: Feed de Odds Offline

### 7.1. Sintoma
- Odds não atualizam
- Alertas de feed offline
- Logs mostram erros de Betfair API
- Circuit breaker Gamma ativado

### 7.2. Impacto
- Sem odds, sem sinais
- Perda de oportunidades
- Insatisfação de subscritores

### 7.3. Mitigação Imediata (0-5 minutos)
1. Verificar conexão: `curl -I https://api.betfair.com`
2. Verificar token de sessão
3. Se token expirado: renovar
4. Notificar: "Feed offline, apostas pausadas"

### 7.4. Diagnóstico (5-15 minutos)
1. Verificar logs do serviço de feed
2. Verificar status da Betfair API
3. Verificar rate limits
4. Verificar credenciais

### 7.5. Resolução (15-30 minutos)

**Caso: Token expirado**
1. Renovar token via API
2. Atualizar configuração
3. Reiniciar serviço

**Caso: Rate limits excedidos**
1. Aguardar janela de reset
2. Implementar backoff exponencial
3. Reduzir frequência de chamadas

**Caso: Betfair API down**
1. Verificar status page da Betfair
2. Aguardar resolução
3. Se downtime > 30 min: notificar subscritores

### 7.6. Verificação (5-10 minutos)
1. Testar chamada API
2. Verificar que odds são atualizadas
3. Verificar que dados são persistidos

### 7.7. Escalada
- Se não resolvido em 15 minutos: Escalar para DevOps
- Se Betfair API down: Aguardar, monitorizar

---

## 8. CHECKLIST FINAL

Antes de considerar incidente resolvido:

- [ ] Causa raiz identificada
- [ ] Serviço restaurado
- [ ] Funcionalidade verificada
- [ ] Logs analisados
- [ ] Equipa notificada
- [ ] Incidente documentado
- [ ] Postmortem agendado (se P1)

---

## 9. LINKS CRUZADOS

- [[26_Runbooks/INDEX]] ← Secção mãe
- [[18_Operations/GESTAO_ALERTAS]] → Gestão de alertas
- [[25_SOPs/SOP_BACKUP_RESTORE_BD]] → Backup e restore
- [[27_Postmortems/INDEX]] → Postmortems
