---
ID: OPS-005
tags: #status/active #operations #maintenance #scheduled #downtime
---

# Manutenção Programada

## Objetivo
Planificar, comunicar e executar todas as atividades de manutenção preventiva e corretiva no sistema de value betting NBA de forma controlada, minimizando o impacto nas operações de negócio, mantendo a transparência com os subscritores, e preservando a integridade dos dados e modelos. A manutenção programada inclui atualizações de sistema, patches de segurança, migrações de base de dados, retreinos de modelo, e atualizações de infraestrutura.

## O que faz
- Define janelas de manutenção standard: (1) Manutenção Leve (terças, 10:00-11:00 UTC, impacto mínimo), (2) Manutenção Média (quintas, 08:00-10:00 UTC, impacto moderado), (3) Manutenção Crítica (domingos, 06:00-09:00 UTC, impacto elevado, pré-agendada com 7 dias de antecedência).
- Estabelece processo de aprovação: pedido → avaliação de risco → aprovação gestor → comunicação subscritores → execução → validação → relatório.
- Implementa mecanismo de silenciamento de alertas durante a janela de manutenção, com reativação automática e verificação pós-manutenção.
- Garante rollback: toda a manutenção deve ter plano de rollback testado e documentado antes do início.

## Porque existe
- **Acumulação de Débito Técnico**: Sem manutenção programada, sistemas degradam: versões de bibliotecas ficam desatualizadas, acumulam vulnerabilidades, e a performance decresce.
- **Impacto no Negócio**: Manutenção não comunicada durante horário de jogo NBA (19:00-02:00 ET) pode interromper a entrega de sinais, gerando insatisfação massiva e pedidos de reembolso.
- **Segurança**: CVEs críticos (ex: em PostgreSQL, Redis, Python, ou framework web) precisam de patching dentro de prazos definidos (ex: 30 dias para CVE crítico).
- **Integridade de Dados**: Migrações de schema sem janela controlada e sem backup testado podem corromper a base de produção.

## Implementação / Pseudocódigo
```python
class ManutencaoProgramada:
    def __init__(self):
        self.janelas = {
            "LEVE": {"dia": "terca", "inicio_utc": "10:00", "duracao_max": "01:00", "impacto": "MINIMO", "pre_aviso_dias": 1},
            "MEDIA": {"dia": "quinta", "inicio_utc": "08:00", "duracao_max": "02:00", "impacto": "MODERADO", "pre_aviso_dias": 3},
            "CRITICA": {"dia": "domingo", "inicio_utc": "06:00", "duracao_max": "03:00", "impacto": "ELEVADO", "pre_aviso_dias": 7}
        }
        self.tipos_atividade = {
            "PATCH_SEGURANCA": {"risco": "ALTO", "requer_rollback": True, "requer_teste": True},
            "UPGRADE_VERSAO": {"risco": "MEDIO", "requer_rollback": True, "requer_teste": True},
            "MIGRACAO_BD": {"risco": "ALTO", "requer_rollback": True, "requer_teste": True},
            "RETREINO_MODELO": {"risco": "MEDIO", "requer_rollback": True, "requer_teste": True},
            "LIMPEZA_DADOS": {"risco": "BAIXO", "requer_rollback": False, "requer_teste": False},
            "OTIMIZACAO_INFRA": {"risco": "MEDIO", "requer_rollback": True, "requer_teste": True}
        }

    def solicitar_manutencao(self, solicitante, tipo, descricao, componentes, janela_preferida):
        risco = self.tipos_atividade[tipo]["risco"]
        pedido = {
            "id": f"MNT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "solicitante": solicitante,
            "tipo": tipo,
            "descricao": descricao,
            "componentes": componentes,
            "janela_preferida": janela_preferida,
            "risco": risco,
            "status": "PENDENTE_APROVACAO",
            "timestamp_pedido": datetime.utcnow().isoformat()
        }
        
        if risco == "ALTO":
            pedido["aprovadores"] = ["gestor_operacoes", "arquiteto_sistemas", "gestor_risco"]
        elif risco == "MEDIO":
            pedido["aprovadores"] = ["gestor_operacoes"]
        else:
            pedido["aprovadores"] = ["operador_dia"]
        
        self.db.inserir("pedidos_manutencao", pedido)
        self.notificar_aprovadores(pedido)
        return pedido

    def aprovar_manutencao(self, pedido_id, aprovador, rollback_plan):
        pedido = self.db.obter_pedido(pedido_id)
        if aprovador not in pedido["aprovadores"]:
            raise PermissionError("Aprovador não autorizado")
        
        pedido["rollback_plan"] = rollback_plan
        pedido["status"] = "APROVADA"
        pedido["timestamp_aprovacao"] = datetime.utcnow().isoformat()
        self.db.atualizar_pedido(pedido_id, pedido)
        
        # Comunicação aos subscritores
        self.comunicar_subscritores(
            assunto=f"Manutenção Programada - {pedido['janela_preferida']}",
            corpo=self.renderizar_template_comunicacao(pedido),
            antecedencia_dias=self.janelas[pedido["janela_preferida"]]["pre_aviso_dias"]
        )
        
        # Silenciar alertas na janela
        self.silenciar_alertas(pedido["janela_preferida"])
        return {"status": "APROVADA", "comunicacao_enviada": True}

    def executar_manutencao(self, pedido_id, executor):
        pedido = self.db.obter_pedido(pedido_id)
        if pedido["status"] != "APROVADA":
            raise ValueError("Manutenção não aprovada")
        
        log_execucao = {"inicio": datetime.utcnow().isoformat(), "passos": []}
        
        try:
            for passo in pedido["passos_execucao"]:
                resultado = self.executar_passo(passo)
                log_execucao["passos"].append({"passo": passo, "status": "OK", "timestamp": datetime.utcnow().isoformat()})
                if not resultado["sucesso"]:
                    raise ManutencaoException(f"Passo falhou: {passo}")
            
            log_execucao["status"] = "SUCESSO"
            log_execucao["fim"] = datetime.utcnow().isoformat()
            
        except ManutencaoException as e:
            log_execucao["status"] = "FALHA"
            log_execucao["erro"] = str(e)
            log_execucao["rollback_executado"] = self.executar_rollback(pedido["rollback_plan"])
            self.alertar_ops(f"Manutenção {pedido_id} falhou. Rollback: {log_execucao['rollback_executado']}")
        
        self.db.atualizar_pedido(pedido_id, {"status": log_execucao["status"], "log_execucao": log_execucao})
        self.reativar_alertas()
        self.validar_pos_manutencao(pedido["componentes"])
        return log_execucao

    def validar_pos_manutencao(self, componentes):
        for comp in componentes:
            health = self.verificar_saude_componente(comp)
            if health["status"] != "OK":
                self.alertar_ops(f"Componente {comp} não saudável após manutenção")
                return False
        return True
```

## Thresholds e Tabelas

| Tipo de Manutenção | Janela Padrão | Pre-Aviso | Risco | Aprovadores | Rollback Testado | Teste Pós-Manutenção |
|--------------------|--------------|-----------|-------|-------------|------------------|----------------------|
| Patch Segurança | Domingo 06:00 UTC | 7 dias | Alto | CO + Arquiteto + GR | Sim | Sim |
| Upgrade Versão | Quinta 08:00 UTC | 3 dias | Médio | CO | Sim | Sim |
| Migração BD | Domingo 06:00 UTC | 7 dias | Alto | CO + Arquiteto + GR | Sim | Sim |
| Retreino Modelo | Quinta 08:00 UTC | 3 dias | Médio | CO | Sim | Sim |
| Limpeza Dados | Terça 10:00 UTC | 1 dia | Baixo | Operador Dia | N/A | Não |
| Otimização Infra | Quinta 08:00 UTC | 3 dias | Médio | CO | Sim | Sim |

| Componente | Health Check Pós-Manutenção | Threshold Falha | Ação em Falha |
|-----------|---------------------------|-----------------|---------------|
| PostgreSQL | Latência < 50ms, conexões < 80% | Latência > 100ms | Rollback imediato |
| Redis | Latência < 10ms, memória < 80% | Latência > 50ms | Rollback imediato |
| Modelo API | Tempo resposta < 200ms, AUC > 0.55 | AUC < 0.52 | Rollback para versão anterior |
| Telegram Bot | Envio heartbeat < 5s | Falha 3x seguidas | Reinício + verificação |
| Feed Odds | Latência < 30s, taxa sucesso > 99% | Latência > 60s | Revert para feed backup |

## Riscos
- **Risco de Rollback Falhado**: Um rollback testado apenas em staging pode falhar em produção por diferenças de volume de dados ou configuração. Exigir rollback testado em ambiente de pré-produção idêntico à produção.
- **Risco de Comunicação Insuficiente**: Subscritores que não recebem aviso de manutenção e encontram o serviço indisponível geram churn e chargebacks.
- **Risco de Cascata**: Uma manutenção que demora mais do que o previsto pode sobrepor-se com o início dos jogos NBA, criando indisponibilidade crítica no horário de pico.
- **Risco de Débito Técnico Oculto**: Manutenções "leves" que são adiadas repetidamente acumulam-se e exigem uma manutenção crítica emergencial, muito mais arriscada.

## Checklist de Manutenção Programada
- [ ] Calendário de manutenção anual aprovado em Q4 do ano anterior; todas as janelas críticas agendadas.
- [ ] Template de pedido de manutenção preenchido com: descrição, componentes, risco, plano de rollback, teste pós-manutenção, aprovadores.
- [ ] Comunicação aos subscritores via e-mail e Telegram com antecedência mínima definida; registo no [[16_Compliance/AUDIT_TRAIL_COMPLIANCE]].
- [ ] Backup completo e testado antes de qualquer manutenção média ou crítica.
- [ ] Ambiente de staging/pre-produção idêntico à produção (infra as code) para testar rollback.
- [ ] Pós-manutenção: health checks executados em todos os componentes afetados; relatório de validação assinado pelo executor.
- [ ] Se rollback for executado, postmortem obrigatório em 48h — [[27_Postmortems/EXEMPLO_POSTMORTEM]].
- [ ] Métrica de "tempo médio de manutenção" vs. "tempo estimado" rastreada; desvios > 20% analisados.

## Links Cruzados
- [[18_Operations/ROTINA_DIARIA]] - Rotina que inclui verificação de manutenção agendada.
- [[25_SOPs/SOP-009_Backup_Restore_BD]] - Backup obrigatório pré-manutenção.
- [[26_Runbooks/RB-010_Erro_Deploy_Modelo]] - Rollback de modelo em manutenção.
- [[34_Security/VPS_HARDENING]] - Patches de segurança que motivam manutenção.
- [[30_Model_Registry/ROLLBACK_MODELO]] - Procedimento específico de rollback de modelo.
