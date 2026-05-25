# SABOTAGE_PREVENTION — Prevenção de Sabotagem

**ID:** `SEC-001` | **Fase:** #phase/1 | **Owner:** Security Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Prevenir sabotagem ou uso não autorizado do sistema.

---

## 2. CONTROLES DE ACESSO

| Controlo | Implementação |
|----------|---------------|
| Autenticação | 2FA obrigatório |
| Autorização | RBAC por papel |
| Auditoria | Log de todas as ações |
| Segregação de funções | Aprovação para ações críticas |

---

## 3. MONITORIZAÇÃO

```python
def detect_suspicious_activity():
    """
    Deteta atividade suspeita.
    
    Sinais:
    - Múltiplas falhas de login
    - Acesso de IP desconhecido
    - Alterações não autorizadas
    """
    # 1. Verificar falhas de login
    failed_logins = get_failed_logins(last_hour=1)
    if len(failed_logins) > 5:
        send_alert("🚨 Múltiplas falhas de login detetadas")
    
    # 2. Verificar IPs desconhecidos
    unknown_ips = get_unknown_ips(last_hour=1)
    if len(unknown_ips) > 0:
        send_alert(f"⚠️ Acesso de IPs desconhecidos: {unknown_ips}")
    
    # 3. Verificar alterações
    unauthorized_changes = get_unauthorized_changes(last_hour=1)
    if len(unauthorized_changes) > 0:
        send_alert("🚨 Alterações não autorizadas detetadas")
```

---

## 4. BACKUP DE SEGURANÇA

```python
def create_security_backup():
    """Cria backup de segurança em localização isolada."""
    # 1. Backup da base de dados
    backup_db_to_offsite()
    
    # 2. Backup do código
    backup_code_to_offsite()
    
    # 3. Backup de configurações
    backup_config_to_offsite()
    
    logger.info("Backup de segurança criado")
```

---

## 5. CRITÉRIOS

- **2FA obrigatório** para todos os utilizadores
- **Logs auditáveis** por 90 dias
- **Backup offsite** diário

---

## 6. LINKS CRUZADOS

- [[01_Vision_And_Strategy/INDEX]]
- [[TEAM_ROLES]]
