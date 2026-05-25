# 99_Templates — INDEX

**ID:** `SEC-99` | **Fase:** Todas | **Owner:** Chief Systems Architect | **Status:** #status/active

---

## 1. OBJETIVO

Fornecer templates padronizados para todas as notas do sistema. **Nunca criar uma nota sem template correspondente.** A consistência estrutural é essencial para que outra IA possa parsear e executar o conteúdo.

---

## 2. TEMPLATES DISPONÍVEIS

| ID      | Template                 | Uso                                  | Secção                       |
| ------- | ------------------------ | ------------------------------------ | ---------------------------- |
| TPL-001 | [[TEMPLATE_MODELO]]      | Documentação de cada modelo treinado | [[30_Model_Registry]]        |
| TPL-002 | [[TEMPLATE_EXPERIMENTO]] | Tracking de experimentos ML          | [[29_Experiment_Tracking]]   |
| TPL-003 | [[TEMPLATE_DAILY]]       | Daily notes de operações             | [[18_Operations]]            |
| TPL-004 | [[TEMPLATE_POSTMORTEM]]  | Análise pós-incidente                | [[27_Postmortems]]           |
| TPL-005 | [[TEMPLATE_SOP]]         | Standard Operating Procedure         | [[25_SOPs]]                  |
| TPL-006 | [[TEMPLATE_RUNBOOK]]     | Runbook de resposta                  | [[26_Runbooks]]              |
| TPL-007 | [[TEMPLATE_DECISAO]]     | Decisões arquiteturais (ADRs)        | [[01_Vision_And_Strategy]]   |
| TPL-008 | [[TEMPLATE_FEATURE]]     | Documentação de features             | [[32_Feature_Store]]         |
| TPL-009 | [[TEMPLATE_BET]]         | Registo individual de aposta         | [[22_Real_Money_Operations]] |
| TPL-010 | [[TEMPLATE_RISCO]]       | Identificação e mitigação de risco   | [[28_Failure_Scenarios]]     | ✅ Criado |
| TPL-011 | [[TEMPLATE_DASHBOARD]]   | Especificação de dashboards          | [[20_Dashboarding]]          | ✅ Criado |
| TPL-012 | [[TEMPLATE_INCIDENTE]]   | Report de incidente em tempo real    | [[27_Postmortems]]           | ✅ Criado |

---

## 3. REGRAS DE USO

1. Copiar o template antes de editar.
2. Preencher TODOS os campos obrigatórios (marcados com *).
3. Usar tags padronizadas no cabeçalho.
4. Adicionar backlinks para notas relacionadas.
5. Atualizar o campo "Status" sempre que o estado mudar.

---

## 4. BACKLOG (Concluído ✓)

- [x] Criar template de risco (TPL-010) → [[TEMPLATE_RISCO]]
- [x] Criar template de dashboard (TPL-011) → [[TEMPLATE_DASHBOARD]]
- [x] Criar template de incidente (TPL-012) → [[TEMPLATE_INCIDENTE]]
- [ ] Criar template de sprint review (futuro)
- [ ] Criar template de reunião de estratégia (futuro)
- [ ] Criar template de análise de competidor (futuro)
- [ ] Criar template de onboarding de subscritor (futuro)
