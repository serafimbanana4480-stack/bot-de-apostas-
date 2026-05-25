# ACCESS_CONTROL — Controlo de Acesso

**ID:** `SEC-003` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. VISÃO GERAL

O sistema de controlo de acesso implementa **RBAC** (Role-Based Access Control) para garantir que cada utilizador/serviço tem apenas as permissões necessárias para a sua função (princípio de least privilege).

---

## 2. ROLES E PERMISSÕES

### 2.1 Hierarquia de Roles

```
ADMIN (Full Access)
├── OPERATIONS (Read/Write Operations)
│   ├── VIEWER (Read-only)
│   └── BETTOR (Execute bets only)
└── DEVELOPER (Deploy/Debug, no production data)
```

### 2.2 Matriz de Permissões

| Role | Read Data | Write Data | Execute Bets | Deploy Code | View Logs | Configure System |
|------|-----------|------------|--------------|-------------|-----------|------------------|
| **ADMIN** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **OPERATIONS** | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **VIEWER** | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **BETTOR** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **DEVELOPER** | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |

---

## 3. AUTENTICAÇÃO

### 3.1 Autenticação de Utilizadores

**Método:** JWT (JSON Web Tokens) com refresh tokens

**Flow:**
1. Utilizador faz login com username/password
2. Servidor valida credenciais contra PostgreSQL
3. Servidor emite access token (15 min) + refresh token (7 dias)
4. Cliente envia access token em cada requisição (Authorization header)
5. Quando access token expira, usar refresh token para obter novo

**Implementação:**
```python
from datetime import datetime, timedelta
import jwt

SECRET_KEY = os.getenv('JWT_SECRET_KEY')

def generate_tokens(user_id: str, role: str):
    access_payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(minutes=15),
        'type': 'access'
    }
    refresh_payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7),
        'type': 'refresh'
    }

    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm='HS256')

    return access_token, refresh_token

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
```

### 3.2 Autenticação de Serviços

**Método:** API Keys com IP whitelisting

**Flow:**
1. Cada serviço tem uma API key única
2. API key é passada em header (X-API-Key)
3. Servidor valida key + IP de origem
4. Permissões são baseadas na key

**Implementação:**
```python
API_KEYS = {
    'betting_service': {
        'key': os.getenv('BETTING_SERVICE_KEY'),
        'allowed_ips': ['127.0.0.1', '10.0.0.5'],
        'permissions': ['execute_bets', 'read_odds']
    },
    'monitoring_service': {
        'key': os.getenv('MONITORING_SERVICE_KEY'),
        'allowed_ips': ['127.0.0.1'],
        'permissions': ['read_metrics']
    }
}

def verify_service_key(api_key: str, client_ip: str):
    for service_name, config in API_KEYS.items():
        if config['key'] == api_key:
            if client_ip in config['allowed_ips']:
                return service_name, config['permissions']
            raise Exception("IP not whitelisted")
    raise Exception("Invalid API key")
```

---

## 4. AUTORIZAÇÃO

### 4.1 Decorator de Permissões

```python
from functools import wraps

def require_permission(permission: str):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'No token provided'}), 401

            try:
                payload = verify_token(token.replace('Bearer ', ''))
                user_role = payload['role']

                if not has_permission(user_role, permission):
                    return jsonify({'error': 'Insufficient permissions'}), 403

                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': str(e)}), 401

        return decorated_function
    return decorator

def has_permission(role: str, permission: str) -> bool:
    ROLE_PERMISSIONS = {
        'ADMIN': ['*'],
        'OPERATIONS': ['read_data', 'write_data', 'execute_bets', 'view_logs'],
        'VIEWER': ['read_data', 'view_logs'],
        'BETTOR': ['execute_bets'],
        'DEVELOPER': ['deploy_code', 'view_logs']
    }

    if role not in ROLE_PERMISSIONS:
        return False

    return '*' in ROLE_PERMISSIONS[role] or permission in ROLE_PERMISSIONS[role]
```

### 4.2 Exemplo de Uso

```python
@app.route('/api/bets', methods=['POST'])
@require_permission('execute_bets')
def place_bet():
    # Lógica de aposta
    pass

@app.route('/api/config', methods=['PUT'])
@require_permission('configure_system')
def update_config():
    # Lógica de configuração
    pass
```

---

## 5. CONTROLO DE ACESSO A BASE DE DADOS

### 5.1 Utilizadores PostgreSQL Dedicados

```sql
-- Utilizador para aplicação principal
CREATE USER vb_app WITH PASSWORD '<strong_password>';
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO vb_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO vb_app;

-- Utilizador apenas para leitura (dashboards)
CREATE USER vb_readonly WITH PASSWORD '<strong_password>';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO vb_readonly;

-- Utilizador para backups
CREATE USER vb_backup WITH PASSWORD '<strong_password>';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO vb_backup;
```

### 5.2 Row-Level Security (RLS)

```sql
-- Exemplo: Apenas operadores podem ver apostas do seu turno
ALTER TABLE bets ENABLE ROW LEVEL SECURITY;

CREATE POLICY operator_turn_policy ON bets
    FOR SELECT
    TO vb_app
    USING (operator_id = current_user_id());
```

---

## 6. AUDITORIA DE ACESSO

Todos os acessos são logados com:
- Timestamp
- User/Service ID
- IP address
- Ação executada
- Recurso acedido
- Resultado (sucesso/falha)

**Ver:** [[34_Security/AUDIT_LOGGING]] para detalhes

---

## 7. REVOGAÇÃO DE ACESSO

### 7.1 Revogação Imediata

**Cenários:**
- Demissão de funcionário
- Comprometimento de credenciais
- Mudança de role

**Processo:**
1. Revogar refresh tokens (blacklist em Redis)
2. Remover/desativar utilizador em PostgreSQL
3. Rotacionar API keys do serviço
4. Revogar SSH keys
5. Documentar no audit log

**Implementação:**
```python
def revoke_user_access(user_id: str):
    # Adicionar refresh token à blacklist
    redis_client.set(f"blacklist:{user_id}", "1", ex=7*24*3600)

    # Desativar utilizador na BD
    db.execute("UPDATE users SET active = false WHERE id = %s", (user_id,))

    # Log
    audit_log.info(f"Access revoked for user {user_id}", extra={'action': 'revoke_access'})
```

---

## 8. BACKLOG

- [ ] Implementar MFA (Multi-Factor Authentication) para ADMIN
- [ ] Configurar Row-Level Security em todas as tabelas sensíveis
- [ ] Implementar sessão única (single session) por utilizador
- [ ] Criar UI para gestão de roles e permissões
- [ ] Implementar IP whitelisting para acessos remotos

---

## 9. LINKS CRUZADOS

- [[34_Security/INDEX]] ← Secão mãe
- [[34_Security/SECURITY_ARCHITECTURE]] → Arquitetura geral
- [[34_Security/SECRETS_MANAGEMENT]] → Gestão de credenciais
- [[34_Security/AUDIT_LOGGING]] → Auditoria de acessos