# DISASTER_RECOVERY — Plano de Recuperação (Custo Zero)

**ID:** `INF-007` | **Versão:** v1.0 | **Data:** 2026-05-17  
**Status:** #status/pending | **Owner:** DevOps Engineer + Operations Lead  
**RTO:** 4 horas | **RPO:** 24 horas

---

## 1. OVERVIEW

Plano de Disaster Recovery usando apenas recursos gratuitos, garantindo recuperação sem custos adicionais.

---

## 2. CENÁRIOS DE DESASTRE

| Cenário | Probabilidade | Impacto | RTO |
|---------|--------------|---------|-----|
| **VPS Down** | Média | Alto | 4h |
| **DB Corrompido** | Baixa | Crítico | 2h |
| **Data Loss** | Baixa | Crítico | 4h |
| **Região Indisponível** | Muito Baixa | Crítico | 8h |
| **Aplicação Quebrada** | Média | Médio | 1h |

---

## 3. CENÁRIO 1: VPS DOWN (Falha Completa)

### 3.1 Deteção
```bash
# Health check falha
ping <IP_PUBLICO>  # timeout
# ou
curl -f http://api:8000/health  # erro
```

### 3.2 Ações Imediatas (min 0-15)

1. **Verificar status na Oracle Cloud Console**
   - Compute → Instances → vbq-server
   - Se "Stopped": Iniciar instância
   - Se "Terminated": Proceder para recuperação

2. **Notificar equipa**
   - Telegram: @vbq-ops-channel
   - Mensagem: "🚨 VPS DOWN - Iniciando DR"

### 3.3 Recuperação (min 15-240)

**Se instância recuperável:**
```bash
# 1. Iniciar instância
# (via Oracle Cloud Console ou CLI)
oci compute instance action --action START --instance-id <ID>

# 2. Aguardar boot (~2 min)
sleep 120

# 3. Verificar serviços
ssh -i ~/.ssh/oracle_key ubuntu@<IP> "docker ps"

# 4. Se necessário, restart containers
docker compose restart
```

**Se instância irrecuperável:**
```bash
# 1. Criar nova instância (mesma configuração)
# Shape: VM.Standard.A1.Flex (4 OCPU, 24GB)
# Boot Volume: 200GB

# 2. Restaurar a partir de boot volume backup
oci bv boot-volume create \
    --source-boot-volume-backup-id <BACKUP_ID> \
    --display-name "vbq-server-recovery"

# 3. Anexar à nova instância

# 4. Configurar networking (security lists)

# 5. Verificar DNS (DuckDNS atualizará automaticamente)

# 6. Iniciar serviços
make up
```

---

## 4. CENÁRIO 2: DATABASE CORROMPIDO

### 4.1 Diagnóstico
```bash
# Verificar logs
docker logs vb-postgres | tail -100

# Tentar conexão
docker exec vb-postgres pg_isready
```

### 4.2 Recuperação

**Se database existe mas corrompida:**
```bash
# 1. Parar aplicação
docker compose stop api

# 2. Backup do estado atual (se possível)
docker exec vb-postgres pg_dump -U vb_admin valuebetting > /backups/corrupt_$(date +%Y%m%d).sql

# 3. Restaurar do backup
# Opção A: Último backup local
zcat /backups/postgres/valuebetting_latest.sql.gz | docker exec -i vb-postgres psql -U vb_admin valuebetting

# Opção B: Download do cloud e restore
oci os object get --bucket-name vbq-backups --name postgres/valuebetting_YYYYMMDD.sql.gz --file /tmp/restore.sql.gz
gunzip /tmp/restore.sql.gz
docker exec -i vb-postgres psql -U vb_admin valuebetting < /tmp/restore.sql

# 4. Verificar
docker exec vb-postgres psql -U vb_admin -c "SELECT COUNT(*) FROM bronze.raw_games;"

# 5. Restart aplicação
docker compose start api
```

---

## 5. CENÁRIO 3: DATA LOSS

### 5.1 Análise de Perda

```bash
# Identificar último backup válido
ls -lt /backups/postgres/ | head -5

# Verificar data do backup
date -r /backups/postgres/valuebetting_20240515.sql.gz
```

### 5.2 Recuperação para Ponto no Tempo

```bash
# Identificar backup mais próximo do ponto desejado
BACKUP_DATE="2024-05-15"
BACKUP_FILE="/backups/postgres/valuebetting_${BACKUP_DATE}_030000.sql.gz"

# Se não existe local, download do cloud
if [ ! -f $BACKUP_FILE ]; then
    oci os object get \
        --bucket-name vbq-backups \
        --name "postgres/valuebetting_${BACKUP_DATE}_030000.sql.gz" \
        --file $BACKUP_FILE
fi

# Restore
zcat $BACKUP_FILE | docker exec -i vb-postgres psql -U vb_admin valuebetting
```

---

## 6. CENÁRIO 4: APLICAÇÃO QUEBRADA (Deploy Mal Sucedido)

### 6.1 Rollback

```bash
# 1. Identificar versão anterior
git log --oneline -10

# 2. Reverter para versão estável anterior
git revert HEAD
git push origin main

# 3. Rebuild
docker compose down
docker compose up -d --build

# 4. Verificar
make health-check
```

### 6.2 Circuit Breaker (Auto)

O sistema tem circuit breakers automáticos:
- Se health check falha 3x consecutivas → rollback automático
- Se erro rate > 10% → pausa de deploy

---

## 7. COMUNICAÇÃO DURANTE DR

| Tempo | Ação | Responsável |
|-------|------|-------------|
| T+0 | Deteção e notificação | Sistema/On-call |
| T+5 | Post-mortem channel | DevOps |
| T+15 | Update #incidentes | Operations |
| T+30 | Update stakeholders | Product Owner |
| T+60 | Status a cada 30min | DevOps |
| T+240 | Resolução | DevOps |
| T+300 | Post-mortem meeting | Todos |

---

## 8. RECOVERY METRICS

| Métrica | Target | Último DR |
|---------|--------|-----------|
| **RTO (Recovery Time Objective)** | < 4 horas | N/A |
| **RPO (Recovery Point Objective)** | < 24 horas | N/A |
| **Backup Restore Time** | < 2 horas | N/A |
| **Failover Time** | < 30 min | N/A |

---

## 9. CUSTO DO DR

| Componente | Custo |
|------------|-------|
| Boot Volume Backup (10GB) | **0€** |
| Object Storage (backups) | **0€** |
| Nova instância (se necessário) | **0€** (Always-Free) |
| Transferência de dados | **0€** |
| **TOTAL** | **0€** |

---

## 10. CHECKLIST DE DR

- [ ] Teste de DR realizado (semestral)
- [ ] Boot volume backup verificado
- [ ] Cloud backups testados
- [ ] Scripts de restore validados
- [ ] Documentação atualizada
- [ ] Equipa treinada
- [ ] Comunicação testada
- [ ] RTO/RPO medidos e dentro do target

---

## 11. QUICK REFERENCE CARD

```
🚨 VPS DOWN
1. Oracle Console → Compute → Start Instance
2. SSH: ssh -i ~/.ssh/oracle_key ubuntu@<IP>
3. Docker: docker compose restart
4. Health: curl http://localhost:8000/health

🗄️ DB CORROMPIDO
1. Stop app: docker compose stop api
2. Restore: zcat /backups/latest.sql.gz | docker exec -i vb-postgres psql -U vb_admin valuebetting
3. Verify: docker exec vb-postgres pg_isready
4. Start app: docker compose start api

🔄 APP QUEBRADA
1. Revert: git revert HEAD && git push
2. Rebuild: docker compose up -d --build
3. Check: make health-check
```

---

## 12. IMPLEMENTAÇÃO COMPLETA

### 12.1 Script Robusto de Disaster Recovery
```python
"""
Script robusto de Disaster Recovery
Inclui deteção, diagnóstico, recuperação e verificação
"""

import os
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
import time
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DisasterRecoveryManager:
    """Gestor de Disaster Recovery"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.recovery_log = []
        
        logger.info("🚨 DisasterRecoveryManager inicializado")
    
    def check_vps_status(self, ip_address: str) -> bool:
        """
        Verifica se VPS está online
        """
        logger.info(f"🔍 Verificando status VPS: {ip_address}")
        
        try:
            # Ping
            result = subprocess.run(
                ['ping', '-c', '1', ip_address],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info("✅ VPS online")
                return True
            else:
                logger.error("❌ VPS offline")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ VPS timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao verificar VPS: {e}")
            return False
    
    def check_database_status(self, container_name: str) -> bool:
        """
        Verifica se database está saudável
        """
        logger.info(f"🔍 Verificando status database: {container_name}")
        
        try:
            # pg_isready
            result = subprocess.run(
                ['docker', 'exec', container_name, 'pg_isready'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if 'accepting connections' in result.stdout:
                logger.info("✅ Database saudável")
                return True
            else:
                logger.error("❌ Database não aceita conexões")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar database: {e}")
            return False
    
    def diagnose_database_corruption(self, container_name: str, db_name: str) -> Dict:
        """
        Diagnostica corrupção de database
        """
        logger.info(f"🔍 Diagnosticando corrupção: {db_name}")
        
        diagnosis = {
            'is_corrupted': False,
            'issues': [],
            'recommendation': None
        }
        
        try:
            # Verificar logs
            result = subprocess.run(
                ['docker', 'logs', '--tail', '100', container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if 'corruption' in result.stdout.lower() or 'corrupted' in result.stdout.lower():
                diagnosis['is_corrupted'] = True
                diagnosis['issues'].append('Corruption detected in logs')
            
            # Tentar conexão
            result = subprocess.run(
                ['docker', 'exec', container_name, 'psql', '-U', 'vb_admin', '-c', 'SELECT 1;'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                diagnosis['is_corrupted'] = True
                diagnosis['issues'].append(f"Query failed: {result.stderr}")
            
            if diagnosis['is_corrupted']:
                diagnosis['recommendation'] = 'restore_from_backup'
            else:
                diagnosis['recommendation'] = 'no_action'
            
            return diagnosis
            
        except Exception as e:
            logger.error(f"❌ Erro ao diagnosticar: {e}")
            diagnosis['is_corrupted'] = True
            diagnosis['issues'].append(f"Diagnostic error: {str(e)}")
            diagnosis['recommendation'] = 'manual_intervention'
            return diagnosis
    
    def restore_database_from_backup(self, backup_path: str, container_name: str, 
                                   db_name: str, db_user: str) -> bool:
        """
        Restaura database a partir de backup
        """
        logger.info(f"🔄 Restaurando database: {backup_path}")
        
        try:
            # Verificar integridade do backup
            if not self._verify_backup_integrity(backup_path):
                logger.error("Backup corrompido, abortando restore")
                return False
            
            # Parar aplicação
            logger.info("⏹️  Parando aplicação...")
            subprocess.run(
                ['docker', 'compose', 'stop', 'api'],
                capture_output=True,
                timeout=30
            )
            
            # Restore
            import gzip
            backup_file = Path(backup_path)
            
            with gzip.open(backup_file, 'rb') as f:
                sql_content = f.read()
            
            cmd = [
                'docker', 'exec', '-i', container_name,
                'psql', '-U', db_user, db_name
            ]
            
            subprocess.run(cmd, input=sql_content, check=True, timeout=300)
            
            logger.info("✅ Restore completado")
            
            # Verificar
            verify_cmd = [
                'docker', 'exec', container_name,
                'psql', '-U', db_user, '-c',
                f"SELECT COUNT(*) FROM bronze.raw_games;"
            ]
            result = subprocess.run(verify_cmd, capture_output=True, text=True)
            logger.info(f"   Registros verificados: {result.stdout}")
            
            # Reiniciar aplicação
            logger.info("▶️  Reiniciando aplicação...")
            subprocess.run(
                ['docker', 'compose', 'start', 'api'],
                capture_output=True,
                timeout=30
            )
            
            # Guardar no log
            self.recovery_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'database_restore',
                'backup_path': backup_path,
                'status': 'success'
            })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao restaurar: {e}")
            return False
    
    def rollback_application(self, repo_path: str, target_commit: str = None) -> bool:
        """
        Rollback da aplicação para commit anterior
        """
        logger.info("🔄 Rollback da aplicação...")
        
        try:
            os.chdir(repo_path)
            
            if target_commit:
                # Reverter para commit específico
                subprocess.run(['git', 'checkout', target_commit], check=True)
            else:
                # Reverter último commit
                subprocess.run(['git', 'revert', 'HEAD', '--no-edit'], check=True)
                subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            
            # Rebuild
            logger.info("🔨 Rebuildando containers...")
            subprocess.run(['docker', 'compose', 'down'], check=True, timeout=60)
            subprocess.run(['docker', 'compose', 'up', '-d', '--build'], check=True, timeout=300)
            
            # Health check
            time.sleep(10)
            if self._health_check():
                logger.info("✅ Rollback bem-sucedido")
                return True
            else:
                logger.error("❌ Health check falhou após rollback")
                return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer rollback: {e}")
            return False
    
    def _health_check(self, url: str = "http://localhost:8000/health") -> bool:
        """Verifica health check da aplicação"""
        try:
            result = subprocess.run(
                ['curl', '-f', url],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _verify_backup_integrity(self, backup_path: str) -> bool:
        """Verifica integridade do backup"""
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return False
            
            if backup_file.stat().st_size == 0:
                return False
            
            return True
            
        except:
            return False
    
    def download_cloud_backup(self, bucket_name: str, namespace: str, 
                           object_name: str, local_path: str) -> bool:
        """
        Download backup da cloud
        """
        logger.info(f"☁️  Download backup: {object_name}")
        
        try:
            cmd = [
                'oci', 'os', 'object', 'get',
                '--bucket-name', bucket_name,
                '--namespace-name', namespace,
                '--name', object_name,
                '--file', local_path
            ]
            
            subprocess.run(cmd, check=True, timeout=300)
            
            logger.info(f"✅ Download completado: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao download: {e}")
            return False
    
    def list_available_backups(self, backup_dir: str) -> List[str]:
        """Lista backups disponíveis"""
        try:
            backup_path = Path(backup_dir)
            backups = sorted(backup_path.glob('*.sql.gz'), key=lambda p: p.stat().st_mtime, reverse=True)
            return [str(b) for b in backups]
        except Exception as e:
            logger.error(f"❌ Erro ao listar backups: {e}")
            return []
    
    def generate_recovery_report(self) -> str:
        """Gera relatório de recuperação"""
        report = "# Relatório de Disaster Recovery\n\n"
        report += f"Gerado em: {datetime.now().isoformat()}\n\n"
        
        report += "## Histórico de Recuperações\n\n"
        for recovery in self.recovery_log:
            report += f"- {recovery['timestamp']}: {recovery['type']} ({recovery['status']})\n"
        
        return report

class RecoveryOrchestrator:
    """Orquestrador de recuperação automatizada"""
    
    def __init__(self, dr_manager: DisasterRecoveryManager):
        self.dr_manager = dr_manager
    
    def handle_vps_down(self, ip_address: str, container_name: str) -> bool:
        """
        Lida com cenário de VPS down
        """
        logger.info("🚨 Iniciando recuperação VPS DOWN...")
        
        # Verificar status
        is_online = self.dr_manager.check_vps_status(ip_address)
        
        if is_online:
            logger.info("✅ VPS já está online")
            return True
        
        # Tentar iniciar via OCI CLI (se disponível)
        logger.info("⚠️  VPS offline - requer intervenção manual ou OCI CLI")
        logger.info("   Ações manuais:")
        logger.info("   1. Oracle Cloud Console → Compute → Instances")
        logger.info("   2. Selecionar vbq-server → Start")
        logger.info("   3. Aguardar boot (~2 min)")
        logger.info("   4. SSH: docker compose restart")
        
        return False
    
    def handle_database_corruption(self, container_name: str, db_name: str, 
                                  db_user: str, backup_dir: str) -> bool:
        """
        Lida com cenário de database corrompido
        """
        logger.info("🚨 Iniciando recuperação DATABASE CORROMPIDO...")
        
        # Diagnosticar
        diagnosis = self.dr_manager.diagnose_database_corruption(container_name, db_name)
        
        if not diagnosis['is_corrupted']:
            logger.info("✅ Database não está corrompido")
            return True
        
        logger.warning(f"⚠️  Database corrompido: {diagnosis['issues']}")
        
        # Listar backups disponíveis
        backups = self.dr_manager.list_available_backups(backup_dir)
        
        if not backups:
            logger.error("❌ Nenhum backup disponível")
            return False
        
        # Usar backup mais recente
        latest_backup = backups[0]
        logger.info(f"📦 Usando backup: {latest_backup}")
        
        # Restaurar
        success = self.dr_manager.restore_database_from_backup(
            latest_backup, container_name, db_name, db_user
        )
        
        return success
    
    def handle_application_failure(self, repo_path: str) -> bool:
        """
        Lida com cenário de aplicação quebrada
        """
        logger.info("🚨 Iniciando recuperação APP QUEBRADA...")
        
        # Rollback para commit anterior
        success = self.dr_manager.rollback_application(repo_path)
        
        return success
    
    def run_full_recovery(self, ip_address: str, container_name: str, 
                         db_name: str, db_user: str, backup_dir: str, 
                         repo_path: str) -> Dict[str, bool]:
        """
        Executa recuperação completa verificando todos os cenários
        """
        logger.info("🚨 Iniciando recuperação completa...")
        
        results = {}
        
        # Cenário 1: VPS Down
        results['vps'] = self.handle_vps_down(ip_address, container_name)
        
        # Cenário 2: Database Corruption
        results['database'] = self.handle_database_corruption(
            container_name, db_name, db_user, backup_dir
        )
        
        # Cenário 3: Application Failure
        results['application'] = self.handle_application_failure(repo_path)
        
        # Resumo
        logger.info("\n📊 Resumo da Recuperação:")
        for scenario, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"  {scenario}: {status}")
        
        return results

# Uso
if __name__ == "__main__":
    # Configuração
    config = {
        'vps_ip': 'your.vps.ip',
        'postgres_container': 'vb-postgres',
        'db_name': 'valuebetting',
        'db_user': 'vb_admin',
        'backup_dir': '/backups/postgres',
        'repo_path': '/path/to/repo',
        'cloud_bucket': 'vbq-backups',
        'cloud_namespace': 'your-namespace'
    }
    
    # Criar gestor
    dr_manager = DisasterRecoveryManager(config)
    
    # Criar orquestrador
    orchestrator = RecoveryOrchestrator(dr_manager)
    
    # Executar recuperação completa
    results = orchestrator.run_full_recovery(
        ip_address=config['vps_ip'],
        container_name=config['postgres_container'],
        db_name=config['db_name'],
        db_user=config['db_user'],
        backup_dir=config['backup_dir'],
        repo_path=config['repo_path']
    )
    
    # Gerar relatório
    report = dr_manager.generate_recovery_report()
    print(report)
```

---

## 13. LINKS

- [[BACKUP_ESTRATEGY]] → Estratégia de backup
- [[VPS_CONFIGURACAO]] → Configuração de VPS
- [[10_Infrastructure/INDEX]] ← Secção mãe

---

**Disaster Recovery 100% Gratuito — Sempre Preparados**
