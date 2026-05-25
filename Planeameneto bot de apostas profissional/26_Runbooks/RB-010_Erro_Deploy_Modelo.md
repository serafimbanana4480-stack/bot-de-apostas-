# RB-010 — Erro no Deploy de Modelo

**ID:** `RB-010` | **Severidade:** High | **Status:** #status/active

---

## 1. SINTOMAS

- Deploy falha
- Modelo não carrega
- Erro ao carregar artefatos do modelo

---

## 2. DIAGNÓSTICO

```bash
# Verificar logs de deploy
tail -f /var/log/betting-bot/deploy.log

# Verificar se ficheiros existem
ls -lh /opt/betting-bot/models/

# Verificar permissões
ls -la /opt/betting-bot/models/
```

---

## 3. RESOLUÇÃO

1. Identificar erro específico no log
2. Se ficheiro corrompido, restaurar do backup
3. Se permissão issue, corrigir permissões
4. Se versão incompatível, rollback para versão anterior
5. Se dependência missing, instalar dependências
6. Re-executar deploy

---

## 4. VERIFICAÇÃO

- Modelo carrega com sucesso
- Predições funcionando
- Sem erros nos logs

---

## 5. LINKS CRUZADOS

- [[26_Runbooks/INDEX]] ← Secção mãe
- [[30_Model_Registry/INDEX]] → Registry de modelos
