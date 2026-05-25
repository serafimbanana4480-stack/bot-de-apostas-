# VPS_CONFIGURACAO — Configuração de VPS 100% Gratuito

**ID:** `INF-004` | **Versão:** v1.0 | **Data:** 2026-05-17  
**Status:** #status/pending | **Owner:** DevOps Engineer  
**Custo:** **0€/mês** (Oracle Cloud Free Tier Always-Free)

---

## 1. OVERVIEW

Configuração completa de VPS usando **apenas recursos gratuitos**, garantindo operação sem custo nas Fases 1-4.

### Opções de VPS Gratuito

| Provider | Recursos | Limitações | Duração | Verificação |
|----------|----------|------------|---------|-------------|
| **Oracle Cloud Free Tier** (RECOMENDADO) | 4 ARM CPUs, 24GB RAM, 200GB | Nenhuma (always-free) | Ilimitado | Email + telefone |
| AWS Free Tier | 1 vCPU (t2.micro), 1GB RAM, 30GB storage | 750h/mês | 12 meses | Cartão (sem cobrança) |
| Google Cloud Free | 1 f1-micro, 30GB storage | Região US apenas | 12 meses | Cartão (sem cobrança) |

**Recomendação:** Oracle Cloud Free Tier — não expira, não requer cartão de crédito, recursos mais generosos.

---

## 2. ORACLE CLOUD FREE TIER — SETUP

### 2.1 Criar Conta

1. Aceder a: https://www.oracle.com/cloud/free/
2. Clicar "Start for free"
3. Preencher:
   - Email (validar)
   - Password
   - Nome completo
   - Morada
   - Telefone (SMS)
4. **NÃO é necessário cartão de crédito** para tier básico

### 2.2 Criar Instância Always-Free

**Especificações:**
```
Nome: vbq-server
Shape: VM.Standard.A1.Flex (ARM Ampere A1)
OCPU: 4 (máximo always-free)
Memória: 24GB (máximo always-free)
Storage: 200GB (boot volume always-free)
SO: Ubuntu 22.04 LTS
```

**Passos:**
1. Dashboard → Compute → Instances
2. Create Instance
3. Name: `vbq-server`
4. Image: Ubuntu 22.04 LTS
5. Shape: VM.Standard.A1.Flex
   - OCPUs: 4
   - Memory: 24GB
6. Networking: Criar nova VCN
7. Add SSH Keys: Gerar novo par
8. Boot Volume: 200GB
9. Create

### 2.3 Configurar Networking

**Security List — Inbound:**
```
Porta 22 (SSH): Seu IP only
Porta 80 (HTTP): 0.0.0.0/0
Porta 443 (HTTPS): 0.0.0.0/0
Porta 8000 (API): Seus IPs only
Porta 3000 (Grafana): Seus IPs only
Porta 9090 (Prometheus): Seus IPs only
```

**Nota:** Oracle Cloud não cobra por tráfego de entrada. Tráfego de saída até 10TB/mês é gratuito.

---

## 3. CONFIGURAÇÃO DO SISTEMA

### 3.1 SSH Hardening

```bash
# Aceder ao servidor
ssh -i ~/.ssh/oracle_key ubuntu@<IP_PUBLICO>

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar fail2ban
sudo apt install fail2ban ufw -y

# Configurar UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Configurar fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3.2 Instalar Docker

```bash
# Instalar Docker CE (gratuito)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Adicionar user ao grupo docker
sudo usermod -aG docker ubuntu

# Instalar Docker Compose
sudo apt install docker-compose-plugin

# Verificar
docker --version
docker compose version
```

### 3.3 Configurar Swap

```bash
# Criar 4GB swap (recomendado para 24GB RAM)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Tornar permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 4. BACKUP DO SISTEMA BASE

### 4.1 Criar Imagem Boot Volume

```bash
# No Oracle Cloud Console:
# 1. Navegar para Block Storage → Boot Volumes
# 2. Selecionar boot volume do vbq-server
# 3. Create Boot Volume Backup
# 4. Nome: vbq-server-baseline
```

**Custo:** 0€ (10GB backup storage incluído no Free Tier)

---

## 5. CUSTO

| Componente | Custo Mensal |
|------------|--------------|
| VPS (4 CPU, 24GB, 200GB) | **0€** |
| Tráfego de entrada | **0€** |
| Tráfego de saída (10TB) | **0€** |
| Backup (10GB) | **0€** |
| **TOTAL** | **0€** |

---

## 6. CHECKLIST DE SETUP

- [ ] Conta Oracle Cloud criada
- [ ] Instância A1.Flex criada (4 CPU, 24GB, 200GB)
- [ ] SSH key configurada
- [ ] Security rules configuradas
- [ ] Sistema atualizado
- [ ] fail2ban instalado e ativo
- [ ] UFW configurado
- [ ] Docker CE instalado
- [ ] Swap configurado
- [ ] Backup boot volume criado

---

## 7. LINKS

- [[NETWORKING]] → Configuração de rede
- [[BACKUP_ESTRATEGY]] → Estratégia de backup
- [[GETTING_STARTED]] → Setup inicial

---

**Oracle Cloud Free Tier — Sempre Gratuito**
