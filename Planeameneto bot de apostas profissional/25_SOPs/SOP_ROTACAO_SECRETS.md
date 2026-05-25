# SOP_ROTACAO_SECRETS — Procedimento Operacional Padrão

**ID:** `SOP-010` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/active
**Última Revisão:** 2024-05-13 | **Próxima Revisão:** 2024-08-13

---

## 1. OBJETIVO

Estabelecer um procedimento padronizado para rotação de secrets (chaves API, tokens, passwords, certificados), garantindo que as credenciais são atualizadas regularmente para minimizar o risco de comprometimento, e que a rotação é executada sem downtime ou interrupção do serviço.

---

## 2. APLICAÇÃO

**Quando executar:**
- Rotação programada (trimestral para secrets críticas, semestral para outras)
- Após suspeita de comprometimento
- Após saída de funcionário com acesso
- Após incidente de segurança

**Responsável:**
- DevOps Engineer (execução)
- Security Lead (aprovação)

**Duração estimada:**
- 30-60 minutos por secret

---

## 3. SECRETS DO SISTEMA

| Secret | Tipo | Frequência de Rotação | Crítico |
|--------|------|----------------------|---------|
| Betfair API Key | API Key | Trimestral | Sim |
| Betfair Session Token | Token | Diário (auto) | Sim |
| NBA API Key | API Key | Semestral | Sim |
| PostgreSQL Password | Password | Trimestral | Sim |
| Redis Password | Password | Trimestral | Sim |
| Telegram Bot Token | Token | Semestral | Não |
| JWT Secret | Secret | Trimestral | Sim |
| AWS Access Keys | Access Key | Trimestral | Sim |
| SSL Certificates | Certificate | Anual | Sim |

---

## 4. PROCEDIMENTO GERAL DE ROTAÇÃO

### 4.1. Preparação (15 minutos)

**Passos:**

1. **Agendar rotação:**
   - [ ] Notificar equipa com 7 dias de antecedência
   - [ ] Agendar janela de manutenção (se necessário)
   - [ ] Identificar serviços afetados

2. **Preparar novo secret:**
   - [ ] Gerar novo secret (usando gerador seguro)
   - [ ] Guardar secret em gestor de secrets (ex: AWS Secrets Manager, Vault)
   - [ ] Documentar novo secret temporariamente

3. **Testar novo secret (se possível):**
   - [ ] Testar em ambiente de staging
   - [ ] Verificar que serviços funcionam com novo secret

### 4.2. Execução da Rotação (30-45 minutos)

**Passos:**

1. **Atualizar configuração:**
   - [ ] Atualizar variáveis de ambiente
   - [ ] Atualizar ficheiros de configuração
   - [ ] Atualizar gestor de secrets

2. **Reiniciar serviços:**
   - [ ] Reiniciar serviços que usam o secret
   - [ ] Verificar que serviços iniciam corretamente
   - [ ] Verificar logs para erros

3. **Verificar funcionamento:**
   - [ ] Executar testes de smoke
   - [ ] Verificar que serviços comunicam corretamente
   - [ ] Verificar que não há erros de autenticação

4. **Invalidar secret antigo:**
   - [ ] Revogar secret antigo (se aplicável)
   - [ ] Remover secret antigo de configurações
   - [ ] Remover secret antigo de gestor de secrets

### 4.3. Verificação Pós-Rotação (15 minutos)

**Passos:**

1. **Monitorizar:**
   - [ ] Monitorizar logs por 30 minutos
   - [ ] Verificar que não há erros de autenticação
   - [ ] Verificar que performance não degradou

2. **Documentar:**
   - [ ] Registar data da rotação
   - [ ] Registar novo secret (hash, não plaintext)
   - [ ] Registar serviços afetados
   - [ ] Registar problemas (se houver)

3. **Notificar:**
   - [ ] Enviar confirmação para equipa
   - [ ] Atualizar documentação

---

## 5. PROCEDIMENTOS ESPECÍFICOS

### 5.1. Rotação de Betfair API Key

**Passos:**

1. **Gerar nova key no portal Betfair:**
   - [ ] Login no portal Betfair
   - [ ] Navegar para "My Account" -> "My API Settings"
   - [ ] Revogar key antiga
   - [ ] Gerar nova key

2. **Atualizar configuração:**
   ```bash
   # Atualizar variável de ambiente
   export BETFAIR_API_KEY="nova_key"
   
   # Atualizar ficheiro .env
   echo "BETFAIR_API_KEY=nova_key" >> .env
   ```

3. **Reiniciar serviço:**
   ```bash
   docker restart betfair_service
   ```

4. **Verificar:**
   - [ ] Testar conexão com Betfair API
   - [ ] Verificar que odds são recebidas

### 5.2. Rotação de PostgreSQL Password

**Passos:**

1. **Gerar nova password:**
   ```bash
   # Gerar password segura
   openssl rand -base64 32
   ```

2. **Atualizar password no PostgreSQL:**
   ```sql
   ALTER USER postgres WITH PASSWORD 'nova_password';
   ```

3. **Atualizar configuração:**
   - [ ] Atualizar pg_hba.conf
   - [ ] Atualizar variáveis de ambiente
   - [ ] Atualizar ficheiro .env

4. **Reiniciar PostgreSQL:**
   ```bash
   sudo systemctl restart postgresql
   ```

5. **Verificar:**
   - [ ] Testar conexão com nova password
   - [ ] Verificar que serviços conectam

### 5.3. Rotação de SSL Certificates

**Passos:**

1. **Gerar novo CSR:**
   ```bash
   openssl req -new -newkey rsa:2048 -nodes -keyout domain.key -out domain.csr
   ```

2. **Submeter para CA:**
   - [ ] Submeter CSR para autoridade certificadora
   - [ ] Aguardar emissão do certificado

3. **Instalar novo certificado:**
   ```bash
   # Copiar certificado e chave
   cp domain.crt /etc/ssl/certs/
   cp domain.key /etc/ssl/private/
   
   # Atualizar configuração do nginx/apache
   ```

4. **Reiniciar serviço web:**
   ```bash
   sudo systemctl restart nginx
   ```

5. **Verificar:**
   - [ ] Testar conexão HTTPS
   - [ ] Verificar validade do certificado
   - [ ] Verificar que não há warnings de segurança

---

## 6. CHECKLIST FINAL

- [ ] Rotação agendada
- [ ] Novo secret gerado
- [ ] Novo secret testado (se possível)
- [ ] Configuração atualizada
- [ ] Serviços reiniciados
- [ ] Funcionamento verificado
- [ ] Secret antigo invalidado
- [ ] Monitorização concluída
- [ ] Documentação atualizada
- [ ] Equipa notificada

---

## 7. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
- [[34_Security/INDEX]] → Segurança