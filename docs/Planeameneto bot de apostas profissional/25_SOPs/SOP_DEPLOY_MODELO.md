# SOP_DEPLOY_MODELO — Procedimento Operacional Padrão

**ID:** `SOP-006` | **Fase:** #phase/6 | **Owner:** ML Engineer + DevOps | **Status:** #status/active
**Última Revisão:** 2024-05-13 | **Próxima Revisão:** 2024-08-13

---

## 1. OBJETIVO

Estabelecer um procedimento padronizado para o deploy de novos modelos de ML em produção, garantindo que a transição é suave, sem downtime, e que o novo modelo é monitorizado após o deploy para detetar problemas precocemente.

---

## 2. APLICAÇÃO

**Quando executar:**
- Após retreino bem-sucedido e validação aprovada
- Após correção de bug em modelo existente
- Após teste de A/B showing resultados positivos

**Responsável:**
- ML Engineer (preparação do modelo)
- DevOps Engineer (execução do deploy)
- Risk Manager (aprovação final)

**Duração estimada:**
- Preparação: 30 minutos
- Deploy: 15-30 minutos
- Verificação: 30-60 minutos
- Total: 1.5-2 horas

---

## 3. PRÉ-REQUISITOS

- [ ] Modelo aprovado e registado no Model Registry
- [ ] Plano de rollback testado
- [ ] Janela de manutenção agendada (se necessário)
- [ ] Backup do modelo atual
- [ ] Sistema de monitorização configurado
- [ ] Acesso aos ambientes de staging e produção

---

## 4. PROCEDIMENTO DETALHADO

### 4.1. Preparação (30 minutos)

**Passos:**

1. **Verificar aprovação:**
   - [ ] Confirmar que modelo foi aprovado pelo Risk Manager
   - [ ] Confirmar que relatório de validação está completo
   - [ ] Confirmar que critérios de aprovação foram cumpridos

2. **Preparar artefactos:**
   - [ ] Exportar modelo do Model Registry
   - [ ] Empacotar modelo com dependências
   - [ ] Criar tag de versão (ex: v2.1.0)
   - [ ] Upload para repositório de artefactos

3. **Preparar ambiente de staging:**
   - [ ] Deploy do novo modelo em staging
   - [ ] Executar testes de smoke
   - [ ] Verificar que predições são geradas corretamente
   - [ ] Comparar predições com modelo atual

4. **Preparar plano de rollback:**
   - [ ] Documentar passos para rollback
   - [ ] Testar rollback em staging
   - [ ] Confirmar que rollback pode ser executado em < 5 minutos

### 4.2. Deploy em Produção (15-30 minutos)

**Estratégia:** Blue-Green Deploy (sem downtime)

**Passos:**

1. **Notificar equipa:**
   - [ ] Enviar mensagem: "Iniciando deploy do modelo v[X] em [hora]"
   - [ ] Indicar duração estimada
   - [ ] Indificar canal de comunicação durante deploy

2. **Deploy da nova versão (Green):**
   ```bash
   # 1. Pull da nova imagem
   docker pull registry.seusistema.com/model:v2.1.0
   
   # 2. Iniciar novo container (green)
   docker run -d --name model_green \
     -p 8002:8000 \
     registry.seusistema.com/model:v2.1.0
   
   # 3. Verificar health check
   curl http://localhost:8002/health
   ```

3. **Verificar nova versão:**
   - [ ] Executar predições de teste
   - [ ] Verificar latência de resposta
   - [ ] Verificar que não há erros nos logs
   - [ ] Comparar predições com esperado

4. **Switch de tráfego:**
   ```bash
   # 1. Atualizar load balancer ou proxy
   # Alterar rota de /predict para apontar para :8002
   
   # 2. Verificar que tráfego está a fluir para nova versão
   curl http://localhost/predict -d '{"features": [...]}'
   
   # 3. Parar versão antiga (blue)
   docker stop model_blue
   docker rm model_blue
   
   # 4. Renomear green para blue (para próximo deploy)
   docker rename model_green model_blue
   ```

5. **Confirmar deploy:**
   - [ ] Verificar logs da nova versão
   - [ ] Verificar métricas de performance (latência, taxa de erro)
   - [ ] Verificar que predições estão a ser geradas
   - [ ] Confirmar que não há erros

### 4.3. Verificação Pós-Deploy (30-60 minutos)

**Passos:**

1. **Monitorização imediata:**
   - [ ] Monitorizar latência de predições (deve ser < 200ms)
   - [ ] Monitorizar taxa de erro (deve ser < 1%)
   - [ ] Monitorizar distribuição de predições
   - [ ] Comparar com modelo anterior

2. **Validação em produção:**
   - [ ] Executar predições para jogos reais
   - [ ] Verificar que CLV está dentro do esperado
   - [ ] Verificar que edge está dentro do esperado
   - [ ] Verificar que não há predições extremas (fora de [0.05, 0.95])

3. **Shadow mode (opcional):**
   - [ ] Se deploy em shadow mode: novo modelo gera predições mas não são usadas
   - [ ] Comparar predições novo vs atual
   - [ ] Se diferença significativa: investigar
   - [ ] Se diferença aceitável: promover para produção

4. **Documentar deploy:**
   - [ ] Registar versão deployada
   - [ ] Registar timestamp
   - [ ] Registar responsável
   - [ ] Guardar logs do deploy

### 4.4. Rollback (se necessário)

**Critérios para rollback:**
- Latência > 500ms
- Taxa de erro > 5%
- Predições fora de [0.05, 0.95] > 10%
- CLV negativo significativo
- Erros críticos nos logs

**Procedimento:**
```bash
# 1. Parar nova versão
docker stop model_blue

# 2. Iniciar versão anterior
docker run -d --name model_blue \
  -p 8000:8000 \
  registry.seusistema.com/model:v2.0.0

# 3. Verificar health check
curl http://localhost:8000/health

# 4. Notificar equipa
```

---

## 5. CHECKLIST FINAL

- [ ] Modelo aprovado
- [ ] Artefactos preparados
- [ ] Staging testado
- [ ] Plano de rollback testado
- [ ] Deploy executado
- [ ] Verificação concluída
- [ ] Métricas dentro de thresholds
- [ ] Deploy documentado
- [ ] Equipa notificada

---

## 6. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
- [[25_SOPs/SOP_RETREINO_MODELO]] → Retreino de modelo
- [[26_Runbooks/RB-010_Erro_Deploy_Modelo]] → Runbook de erro de deploy
- [[30_Model_Registry/INDEX]] → Model Registry