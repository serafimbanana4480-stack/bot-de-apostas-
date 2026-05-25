---
ID: CMP-005
tags: #status/active #compliance #audit #trail #immutability #evidence
---

# Audit Trail de Compliance

## Objetivo
Construir e manter um registo completo, imutável e criptograficamente verificável de todas as ações, decisões, alterações de configuração e eventos de negócio relevantes para compliance. Este audit trail serve como prova pericial em litígios, auditorias regulamentares, investigações internas e análises de forense digital, garantindo a integridade, disponibilidade e confidencialidade dos registos segundo os princípios ALCOA+ (Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, Enduring, Available).

## O que faz
- Regista automaticamente todas as alterações em dados de subscritores, configurações de modelo, thresholds de risco, execuções de apostas (mesmo em paper trading), decisões de circuit breakers, alterações de preços e modificações de termos de serviço.
- Calcula e armazena hashes criptográficos (SHA-256) de cada registo, ligando-o ao hash anterior (blockchain simplificada interna) para deteção de adulteração.
- Replica os registos para três destinos: base de dados PostgreSQL (tabela audit_auditlog), arquivo WORM (Write Once Read Many) em storage object (AWS S3 Glacier / Azure Blob Immutable), e log externo imutável (LogDNA / Datadog / Splunk).
- Implementa retenção escalonada: 2 anos online, 7 anos em arquivo frio, 10 anos em arquivo perene (conforme prescrição civil portuguesa e obrigações fiscais).

## Porque existe
- **Requisito Legal**: Art. 5º, nº1, alínea f) do GDPR exige que os dados sejam mantidos de forma que permitam a identificação do titular apenas pelo período necessário. Para dados de controlo, o período é estendido.
- **Prova Pericial**: Em litígio com subscritor ou autoridade, a carga da prova está no operador. Sem audit trail, é impossível demonstrar que uma configuração não foi alterada retroativamente ou que um circuit breaker atuou corretamente.
- **Deteção de Fraude Interna**: Análise de padrões no audit trail permite identificar funcionários ou contas comprometidas que alteraram dados para benefício próprio.
- **Recuperação de Desastres**: Em caso de ransomware ou corrupção de base de dados, o audit trail externo permite reconstruir o estado do sistema.

## Implementação / Pseudocódigo
```python
class AuditTrailCompliance:
    def __init__(self):
        self.db = PostgreSQLConnection()
        self.storage_worm = S3ImmutableStorage(bucket="audit-trail-worm", retention_days=2555)  # ~7 anos
        self.log_immutable = LogDNAClient()
        self.hash_chain = []
        
    def registrar_evento(self, categoria, entidade, entidade_id, acao, payload_anterior, payload_novo, agente):
        timestamp = datetime.utcnow().isoformat()
        payload_diff = self.calcular_diff_json(payload_anterior, payload_novo)
        
        registo = {
            "id": str(uuid.uuid4()),
            "timestamp_utc": timestamp,
            "categoria": categoria,       # EX: "SUBSCRITOR", "MODELO", "RISCO", "CONFIG", "APOSTA"
            "entidade": entidade,           # Nome da tabela/recurso
            "entidade_id": entidade_id,
            "acao": acao,                   # EX: "CREATE", "UPDATE", "DELETE", "EXECUTE", "ALERT"
            "diff": payload_diff,
            "agente": agente,               # "sistema", "user:123", "api:webhook", "cron:rotina"
            "hash_anterior": self.hash_chain[-1] if self.hash_chain else "0" * 64
        }
        
        registo["hash_proprio"] = self.calcular_hash_sha256(registo)
        self.hash_chain.append(registo["hash_proprio"])
        
        # Persistência tripla
        self.db.inserir("audit_log", registo)
        self.storage_worm.upload(
            key=f"{timestamp[:7]}/{registo['id']}.json",  # prefixo YYYY-MM
            data=json.dumps(registo, ensure_ascii=False),
            legal_hold=True
        )
        self.log_immutable.enviar(
            message=f"AUDIT {categoria}/{acao} {entidade}:{entidade_id}",
            metadata=registo,
            tags=["audit", "compliance", categoria.lower()]
        )
        
        return registo["id"]

    def verificar_integridade(self, data_inicio, data_fim):
        registos = self.db.consultar(
            "SELECT * FROM audit_log WHERE timestamp_utc BETWEEN %s AND %s ORDER BY timestamp_utc",
            (data_inicio, data_fim)
        )
        
        hashes_verificados = 0
        hashes_falhados = 0
        
        for i, reg in enumerate(registos):
            hash_calculado = self.calcular_hash_sha256(reg)
            if hash_calculado != reg["hash_proprio"]:
                hashes_falhados += 1
                self.alertar_integridade_violada(reg, hash_calculado)
            else:
                hashes_verificados += 1
        
        return {
            "total": len(registos),
            "verificados": hashes_verificados,
            "falhados": hashes_falhados,
            "integridade": hashes_falhados == 0
        }

    def calcular_diff_json(self, anterior, novo):
        if not anterior and not novo:
            return None
        return {
            "removido": {k: anterior[k] for k in set(anterior) - set(novo)},
            "adicionado": {k: novo[k] for k in set(novo) - set(anterior)},
            "alterado": {k: {"de": anterior[k], "para": novo[k]} for k in anterior if k in novo and anterior[k] != novo[k]}
        }

    def gerar_relatorio_auditoria(self, periodo):
        return {
            "periodo": periodo,
            "total_eventos": self.db.contar("audit_log", periodo),
            "categorias": self.db.agrupar_por("categoria", periodo),
            "agentes_mais_ativos": self.db.top_agentes(periodo, n=10),
            "integridade_verificada": self.verificar_integridade(periodo[0], periodo[1]),
            "retenção_worm": self.storage_worm.verificar_retencao(periodo)
        }
```

## Thresholds e Tabelas

| Categoria de Evento | Nível de Detalhe | Retenção Online | Retenção Arquivo Frio | Retenção Perene |
|--------------------|------------------|----------------|----------------------|-----------------|
| Dados Pessoais Subscritor (CRUD) | Diff completo JSON | 2 anos | 7 anos | 10 anos |
| Configuração de Modelo / Threshold | Diff + justificação | 2 anos | 7 anos | 10 anos |
| Execução de Aposta (paper + real) | Snapshot completo pre/post | 2 anos | 7 anos | 10 anos |
| Circuit Breaker / Alerta de Risco | Contexto completo | 2 anos | 7 anos | 10 anos |
| Alteração de Preço / Plano | Diff + consentimento | 2 anos | 7 anos | 10 anos |
| Acesso Administrativo / Root | Log de sessão + comandos | 2 anos | 7 anos | 10 anos |

| Propriedade ALCOA+ | Implementação no Sistema |
|--------------------|--------------------------|
| Attributable | Campo `agente` identifica utilizador, serviço ou processo |
| Legible | Formato JSON estruturado com schema versionado |
| Contemporaneous | Timestamp UTC com precisão de microssegundos; inserção síncrona com a operação |
| Original | Registo primário na BD; cópias em storage WORM são read-only |
| Accurate | Hash SHA-256 calculado sobre o conteúdo exato do registo |
| Complete | Campos obrigatórios validados em schema; rejeita registos incompletos |
| Consistent | Schema versionado; migrações mantêm compatibilidade retroativa |
| Enduring | Storage WORM com legal hold; eliminação física impossível até ao fim do período |
| Available | Replicação em 3 zonas de disponibilidade; RPO < 1 minuto |

## Riscos
- **Risco de Integridade Comprometida**: Se o sistema de hash for calculado após potencial adulteração na memória, o audit trail perde valor probatório. O hash deve ser calculado no momento da criação do evento.
- **Risco de Privacidade Inversa**: Um audit trail muito detalhado sobre comportamento de jogo pode constituir dado pessoal sensível; o acesso deve ser restrito ao DPO e ao compliance officer.
- **Risco de Custos de Armazenamento**: 10 anos de diff JSON completo com milhões de eventos pode atingir terabytes. A compressão (gzip) e a separação de blobs devem ser implementadas.
- **Risco de Indisponibilidade em Auditoria**: Se o fornecedor de storage WORM falhar, a prova pericial pode não ser recuperável. Necessário exportação física anual (tape ou disco offline).

## Checklist de Audit Trail
- [ ] Tabela `audit_log` criada em PostgreSQL com índices em `timestamp_utc`, `categoria`, `entidade_id`, `agente`.
- [ ] Coluna `hash_proprio` e `hash_anterior` implementadas; verificação de cadeia executada diariamente via cron.
- [ ] Bucket S3/Azure configurado com política WORM (object lock, retention-mode compliance, legal hold).
- [ ] Pipeline de replicação assíncrona da BD para storage WORM com retentativa em falha (DLQ - Dead Letter Queue).
- [ ] Rotação de chaves de acesso ao storage WORM a cada 90 dias; acesso apenas via IAM role (nunca access key em código).
- [ ] Relatório de integridade mensal enviado para compliance officer; qualquer falha de hash dispara alerta crítico.
- [ ] Teste semestral de recuperação: extrair registo de arquivo frio e verificar se hash corresponde ao original.
- [ ] Documentação do schema de audit log versionado (v1, v2, etc.) com changelog.

## Links Cruzados
- [[16_Compliance/KYC_AML]] - Registo de decisões de verificação de identidade.
- [[16_Compliance/RESPONSIBLE_GAMBLING]] - Registo de intervenções e autoexclusões.
- [[17_Legal/PRIVACY_POLICY]] - Base jurídica para retenção de dados pessoais em audit trail.
- [[34_Security/BACKUPS_ENCRIPTADOS]] - Política de backup que inclui audit trail.
- [[25_SOPs/SOP-009_Backup_Restore_BD]] - Procedimento de backup que preserva integridade do audit trail.
