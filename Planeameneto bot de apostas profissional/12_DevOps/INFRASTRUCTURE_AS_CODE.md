# INFRASTRUCTURE_AS_CODE — Terraform, Ansible e Versionamento de Infraestrutura

**ID:** `DEV-004` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar Infraestrutura como Código (IaC) para provisionar, configurar e gerir a infraestrutura de forma automatizada, reprodutível e versionada. IaC elimina configurações manuais, reduz erros e garante consistência entre ambientes.

---

## 2. CONCEITOS

### 2.1 O que é Infrastructure as Code?

**Definição:** Gestão de infraestrutura (servidores, redes, bancos de dados) através de código em vez de processos manuais ou configurações interativas.

**Princípios:**
- **Declarativo:** Descrever o estado desejado, não como chegar lá
- **Idempotente:** Executar múltiplas vezes sem efeitos colaterais
- **Versionado:** Infraestrutura em Git como qualquer outro código
- **Testável:** Validar infraestrutura antes de aplicar
- **Documentação automática:** O código é a documentação

**Benefícios:**
- Consistência entre ambientes
- Rastreabilidade de mudanças
- Rollback rápido
- Redução de erros humanos
- Automação de provisionamento
- Auditoria e compliance

### 2.2 Ferramentas Escolhidas

| Ferramenta | Uso | Justificação |
|------------|-----|--------------|
| **Terraform** | Provisionamento de recursos cloud | Declarativo, multi-cloud, maduro |
| **Ansible** | Configuração de servidores | Agentless, simples, YAML |
| **Docker** | Containerização | Padronização de ambientes |
| **Docker Compose** | Orquestração local | Simples para desenvolvimento |

**Alternativas consideradas:**
- **AWS CloudFormation:** Proprietário AWS, lock-in
- **Pulumi:** Imperativo, menos popular
- **Chef/Puppet:** Mais complexos que Ansible
- **Kubernetes:** Overkill para escala atual

---

## 3. TERRAFORM

### 3.1 Estrutura de Diretórios

```
terraform/
├── environments/
│   ├── dev/
│   │   ├── backend.tf
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── staging/
│   │   ├── backend.tf
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── production/
│       ├── backend.tf
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── modules/
│   ├── vps/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── database/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── security/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── scripts/
    ├── init.sh
    └── apply.sh
```

### 3.2 Provider Configuration

```hcl
# terraform/environments/production/provider.tf
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
  
  backend "s3" {
    bucket = "valuebetting-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
    encrypt = true
  }
}

provider "digitalocean" {
  token = var.do_token
}
```

### 3.3 VPS Module

```hcl
# terraform/modules/vps/main.tf
resource "digitalocean_droplet" "app" {
  image  = var.image
  name   = var.name
  region = var.region
  size   = var.size
  ssh_keys = var.ssh_key_ids
  
  tags = var.tags
  
  monitoring = true
  
  user_data = file("${path.module}/cloud-init.yml")
}

resource "digitalocean_floating_ip" "app_ip" {
  droplet_id = digitalocean_droplet.app.id
  region     = var.region
}

output "droplet_id" {
  value = digitalocean_droplet.app.id
}

output "floating_ip" {
  value = digitalocean_floating_ip.app_ip.ip_address
}

output "ipv4_address" {
  value = digitalocean_droplet.app.ipv4_address
}
```

```hcl
# terraform/modules/vps/variables.tf
variable "name" {
  description = "Nome do droplet"
  type        = string
}

variable "region" {
  description = "Região do droplet"
  type        = string
  default     = "ams3"
}

variable "size" {
  description = "Tamanho do droplet"
  type        = string
  default     = "s-4vcpu-8gb"
}

variable "image" {
  description = "Imagem do droplet"
  type        = string
  default     = "ubuntu-22-04-x64"
}

variable "ssh_key_ids" {
  description = "IDs das chaves SSH"
  type        = list(string)
}

variable "tags" {
  description = "Tags do droplet"
  type        = list(string)
  default     = ["valuebetting", "production"]
}
```

### 3.4 Database Module

```hcl
# terraform/modules/database/main.tf
resource "digitalocean_database_cluster" "postgres" {
  name       = var.name
  engine     = "pg"
  version    = var.postgres_version
  size       = var.size
  region     = var.region
  node_count = var.node_count
  
  tags = var.tags
}

resource "digitalocean_database_db" "app_db" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = var.db_name
}

resource "digitalocean_database_user" "app_user" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = var.db_user
}

output "connection_uri" {
  value     = digitalocean_database_cluster.postgres.uri
  sensitive = true
}

output "host" {
  value = digitalocean_database_cluster.postgres.host
}

output "port" {
  value = digitalocean_database_cluster.postgres.port
}
```

### 3.5 Environment Configuration

```hcl
# terraform/environments/production/main.tf
module "app_server" {
  source = "../../modules/vps"
  
  name        = "valuebetting-app-prod"
  region      = "ams3"
  size        = "s-4vcpu-8gb"
  ssh_key_ids = [digitalocean_ssh_key.default.fingerprint]
  tags        = ["valuebetting", "production", "app"]
}

module "database" {
  source = "../../modules/database"
  
  name            = "valuebetting-db-prod"
  region          = "ams3"
  size            = "db-s-2vcpu-4gb"
  postgres_version = "15"
  node_count      = 1
  db_name         = "valuebetting"
  db_user         = "app_user"
  tags            = ["valuebetting", "production", "database"]
}

resource "digitalocean_ssh_key" "default" {
  name       = "valuebetting-key"
  public_key = file(var.ssh_public_key_path)
}

output "app_ip" {
  value = module.app_server.floating_ip
}

output "db_host" {
  value = module.database.host
}
```

### 3.6 Cloud-init Script

```yaml
# terraform/modules/vps/cloud-init.yml
#cloud-config
package_update: true
package_upgrade: true

packages:
  - docker.io
  - docker-compose
  - nginx
  - ufw
  - fail2ban

runcmd:
  - systemctl enable docker
  - systemctl start docker
  - ufw allow 22/tcp
  - ufw allow 80/tcp
  - ufw allow 443/tcp
  - ufw --force enable
  - systemctl enable fail2ban
  - systemctl start fail2ban
  
  # Criar diretórios
  - mkdir -p /app/valuebetting
  - mkdir -p /app/valuebetting/logs
  - mkdir -p /app/valuebetting/ssl
  
  # Configurar nginx
  - cp /tmp/nginx.conf /etc/nginx/nginx.conf
  - systemctl restart nginx
```

### 3.7 Comandos Terraform

```bash
# Inicializar Terraform
terraform init

# Validar configuração
terraform validate

# Formatar código
terraform fmt -recursive

# Ver plano de mudanças
terraform plan

# Aplicar mudanças
terraform apply

# Aplicar com auto-approve (cuidado!)
terraform apply -auto-approve

# Destruir infraestrutura
terraform destroy

# Importar recursos existentes
terraform import digitalocean_droplet.app 12345678

# Output de variáveis
terraform output app_ip

# State management
terraform state list
terraform state show digitalocean_droplet.app
terraform state mv digitalocean_droplet.app digitalocean_droplet.new_app
```

---

## 4. ANSIBLE

### 4.1 Estrutura de Diretórios

```
ansible/
├── inventory/
│   ├── dev.ini
│   ├── staging.ini
│   └── production.ini
├── roles/
│   ├── common/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   └── templates/
│   ├── docker/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── handlers/
│   │       └── main.yml
│   ├── application/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   ├── templates/
│   │   │   └── docker-compose.yml.j2
│   │   └── files/
│   └── monitoring/
│       ├── tasks/
│       │   └── main.yml
│       └── templates/
├── playbooks/
│   ├── setup-server.yml
│   ├── deploy-app.yml
│   └── backup.yml
├── group_vars/
│   ├── all.yml
│   ├── production.yml
│   └── staging.yml
└── host_vars/
    └── production.yml
```

### 4.2 Inventory

```ini
# ansible/inventory/production.ini
[production]
app-server ansible_host=APP_IP ansible_user=root

[production:vars]
ansible_python_interpreter=/usr/bin/python3
env=production
```

### 4.3 Common Role

```yaml
# ansible/roles/common/tasks/main.yml
---
- name: Update apt cache
  apt:
    update_cache: yes
    cache_valid_time: 3600

- name: Install common packages
  apt:
    name:
      - curl
      - wget
      - git
      - vim
      - htop
      - tmux
      - ufw
      - fail2ban
    state: present

- name: Configure UFW
  ufw:
    rule: allow
    port: "{{ item }}"
    proto: tcp
  loop:
    - 22
    - 80
    - 443

- name: Enable UFW
  ufw:
    state: enabled
    policy: deny

- name: Configure fail2ban
  template:
    src: jail.local.j2
    dest: /etc/fail2ban/jail.local
  notify: restart fail2ban

- name: Start fail2ban
  service:
    name: fail2ban
    state: started
    enabled: yes
```

```yaml
# ansible/roles/common/handlers/main.yml
---
- name: restart fail2ban
  service:
    name: fail2ban
    state: restarted
```

### 4.4 Docker Role

```yaml
# ansible/roles/docker/tasks/main.yml
---
- name: Install Docker dependencies
  apt:
    name:
      - apt-transport-https
      - ca-certificates
      - curl
      - gnupg
      - lsb-release
    state: present

- name: Add Docker GPG key
  apt_key:
    url: https://download.docker.com/linux/ubuntu/gpg
    state: present

- name: Add Docker repository
  apt_repository:
    repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_lsb.codename }} stable"
    state: present

- name: Install Docker
  apt:
    name:
      - docker-ce
      - docker-ce-cli
      - containerd.io
      - docker-compose-plugin
    state: present
    update_cache: yes

- name: Add user to docker group
  user:
    name: "{{ ansible_user }}"
    groups: docker
    append: yes

- name: Start Docker service
  service:
    name: docker
    state: started
    enabled: yes

- name: Install Docker Compose
  get_url:
    url: "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-linux-x86_64"
    dest: /usr/local/bin/docker-compose
    mode: '0755'
```

### 4.5 Application Role

```yaml
# ansible/roles/application/tasks/main.yml
---
- name: Create application directory
  file:
    path: "{{ app_dir }}"
    state: directory
    owner: "{{ ansible_user }}"
    group: "{{ ansible_user }}"
    mode: '0755'

- name: Create logs directory
  file:
    path: "{{ app_dir }}/logs"
    state: directory
    owner: "{{ ansible_user }}"
    group: "{{ ansible_user }}"
    mode: '0755'

- name: Create SSL directory
  file:
    path: "{{ app_dir }}/ssl"
    state: directory
    owner: "{{ ansible_user }}"
    group: "{{ ansible_user }}"
    mode: '0700'

- name: Copy docker-compose file
  template:
    src: docker-compose.yml.j2
    dest: "{{ app_dir }}/docker-compose.yml"
    owner: "{{ ansible_user }}"
    group: "{{ ansible_user }}"
    mode: '0644'
  notify: restart application

- name: Copy environment file
  template:
    src: .env.j2
    dest: "{{ app_dir }}/.env"
    owner: "{{ ansible_user }}"
    group: "{{ ansible_user }}"
    mode: '0600'
  notify: restart application

- name: Pull Docker images
  docker_compose:
    project_src: "{{ app_dir }}"
    pull: yes
  register: pull_result

- name: Start application
  docker_compose:
    project_src: "{{ app_dir }}"
    state: present
  register: start_result
```

```yaml
# ansible/roles/application/handlers/main.yml
---
- name: restart application
  docker_compose:
    project_src: "{{ app_dir }}"
    state: restarted
```

```yaml
# ansible/roles/application/templates/docker-compose.yml.j2
version: '3.8'

services:
  app:
    image: ghcr.io/{{ github_repository }}:{{ app_version }}
    container_name: valuebetting-app
    restart: unless-stopped
    environment:
      - ENV={{ env }}
      - DATABASE_URL={{ database_url }}
      - MLFLOW_TRACKING_URI={{ mlflow_tracking_uri }}
      - LOG_LEVEL={{ log_level }}
    ports:
      - "8000:8000"
    volumes:
      - {{ app_dir }}/logs:/app/logs
    networks:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: valuebetting-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - {{ app_dir }}/nginx.conf:/etc/nginx/nginx.conf
      - {{ app_dir }}/ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - backend

networks:
  backend:
    driver: bridge
```

### 4.6 Playbooks

```yaml
# ansible/playbooks/setup-server.yml
---
- name: Setup production server
  hosts: production
  become: yes
  
  roles:
    - common
    - docker
    - application
```

```yaml
# ansible/playbooks/deploy-app.yml
---
- name: Deploy application
  hosts: production
  become: yes
  
  vars:
    app_version: "{{ lookup('env', 'APP_VERSION') | default('latest', true) }}"
  
  tasks:
    - name: Update docker-compose with new version
      template:
        src: docker-compose.yml.j2
        dest: "{{ app_dir }}/docker-compose.yml"
      notify: restart application
    
    - name: Pull new image
      docker_compose:
        project_src: "{{ app_dir }}"
        pull: yes
    
    - name: Restart application
      docker_compose:
        project_src: "{{ app_dir }}"
        state: restarted
    
    - name: Wait for health check
      uri:
        url: http://localhost:8000/health
        status_code: 200
      register: result
      until: result.status == 200
      retries: 10
      delay: 10
```

### 4.7 Comandos Ansible

```bash
# Verificar conectividade
ansible production -m ping

# Executar playbook
ansible-playbook -i inventory/production.ini playbooks/setup-server.yml

# Executar com variáveis
ansible-playbook -i inventory/production.ini playbooks/deploy-app.yml \
  -e "app_version=v1.2.3"

# Ver syntax
ansible-playbook --syntax-check playbooks/setup-server.yml

# Dry run (check mode)
ansible-playbook -i inventory/production.ini playbooks/setup-server.yml --check

# Listar hosts
ansible all -i inventory/production.ini --list-hosts

# Executar comando em hosts
ansible production -i inventory/production.ini -m shell -a "docker ps"

# Copiar arquivo
ansible production -i inventory/production.ini -m copy \
  -a "src=./local-file dest=/remote-file"
```

---

## 5. INTEGRAÇÃO CI/CD

### 5.1 Terraform no GitHub Actions

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  push:
    branches:
      - main
    paths:
      - 'terraform/**'
  workflow_dispatch:

jobs:
  terraform:
    name: Terraform Apply
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.0
      
      - name: Terraform Init
        run: |
          cd terraform/environments/production
          terraform init
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      
      - name: Terraform Format Check
        run: terraform fmt -check -recursive
        working-directory: terraform
      
      - name: Terraform Validate
        run: terraform validate
        working-directory: terraform/environments/production
      
      - name: Terraform Plan
        run: terraform plan -out=tfplan
        working-directory: terraform/environments/production
        env:
          DO_TOKEN: ${{ secrets.DO_TOKEN }}
      
      - name: Terraform Apply
        run: terraform apply tfplan
        working-directory: terraform/environments/production
        env:
          DO_TOKEN: ${{ secrets.DO_TOKEN }}
        if: github.ref == 'refs/heads/main'
```

### 5.2 Ansible no GitHub Actions

```yaml
# .github/workflows/ansible.yml
name: Ansible

on:
  push:
    branches:
      - main
    paths:
      - 'ansible/**'
  workflow_dispatch:

jobs:
  ansible:
    name: Run Ansible Playbook
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Ansible
        run: |
          pip install ansible ansible-lint
      
      - name: Ansible Lint
        run: ansible-lint ansible/playbooks/
      
      - name: Run Ansible Playbook
        run: |
          ansible-playbook -i ansible/inventory/production.ini \
            ansible/playbooks/deploy-app.yml \
            -e "app_version=${{ github.sha }}"
        env:
          ANSIBLE_HOST_KEY_CHECKING: False
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
```

---

## 6. BOAS PRÁTICAS

### 6.1 Terraform

- Usar módulos reutilizáveis
- Separar estado por ambiente
- Versionar estado em backend remoto
- Usar variáveis para valores sensíveis
- Documentar código com comentários
- Usar locks para evitar conflitos
- Executar `terraform plan` antes de `apply`
- Nunca commitar secrets ou state files

### 6.2 Ansible

- Usar roles para organização
- Separar inventory por ambiente
- Usar templates para configurações
- Documentar variáveis
- Testar playbooks em modo check
- Usar handlers para restarts
- Nunca hardcode passwords
- Usar vault para secrets

### 6.3 Geral

- Infraestrutura em Git
- Code review para mudanças
- Testar mudanças em staging primeiro
- Ter plano de rollback
- Documentar procedimentos
- Automatizar tudo possível
- Monitorizar infraestrutura

---

## 7. BACKLOG TÉCNICO

- [ ] Implementar Terraform modules para todos os recursos
- [ ] Adicionar Ansible vault para secrets
- [ ] Implementar testes de infraestrutura (Terratest)
- [ ] Adicionar monitorização com Prometheus
- [ ] Implementar auto-scaling
- [ ] Configurar backup automatizado
- [ ] Implementar disaster recovery

---

## 8. LINKS CRUZADOS

- [[12_DevOps/INDEX]] ← Secção mãe
- [[12_DevOps/GIT_WORKFLOW]] → Estratégia Git
- [[12_DevOps/CI_CD_SETUP]] → Configuração de CI/CD
- [[12_DevOps/DEPLOYMENT_STRATEGY]] → Estratégias de deploy
- [[13_Infrastructure/INDEX]] → Detalhes de infraestrutura