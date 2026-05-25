# BACKUP_ESTRATEGY — Estratégia de Backup 100% Gratuita

**ID:** `INF-006` | **Versão:** v1.0 | **Data:** 2026-05-17  
**Status:** #status/pending | **Owner:** DevOps Engineer  
**Custo:** **0€** (Oracle Object Storage 10GB free + local backup)

---

## 1. OVERVIEW

Estratégia de backup 3-2-1 usando apenas recursos gratuitos:
- **3** cópias dos dados
- **2** tipos de mídia diferentes
- **1** cópia off-site (cloud gratuita)

---

## 2. ESTRATÉGIA 3-2-1

```
┌─────────────────────────────────────────────────────────────┐
│                    BACKUP STRATEGY 3-2-1                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. CÓPIA PRIMÁRIA (Produção)                                 │
│     └── PostgreSQL no VPS (200GB SSD)                       │
│                                                              │
│  2. CÓPIA LOCAL (Backup diário)                               │
│     └── /backups/ no mesmo VPS (dump SQL)                   │
│                                                              │
│  3. CÓPIA OFF-SITE (Cloud gratuita)                           │
│     └── Oracle Object Storage (10GB Always-Free)            │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  MÍDIA 1: SSD (produção + backup local)                      │
│  MÍDIA 2: Object Storage (cloud)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. BACKUP DO BANCO DE DADOS

### 3.1 Backup Diário (Local)

```bash
#!/bin/bash
# /backups/scripts/backup-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
CONTAINER="vb-postgres"
DB_NAME="valuebetting"
DB_USER="vb_admin"

# Criar backup
mkdir -p $BACKUP_DIR
docker exec $CONTAINER pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/${DB_NAME}_${DATE}.sql.gz

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "${DB_NAME}_*.sql.gz" -mtime +7 -delete

# Log
logger "Backup DB: ${DB_NAME}_${DATE}.sql.gz criado"
```

### 3.2 Backup Semanal (Cloud)

```bash
#!/bin/bash
# Upload para Oracle Object Storage

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/backups/postgres/valuebetting_${DATE}.sql.gz"
BUCKET="vbq-backups"
NAMESPACE=$(oci os ns get --query data --raw-output)

# Upload
oci os object put --bucket-name $BUCKET --namespace-name $NAMESPACE --file $BACKUP_FILE --name "postgres/valuebetting_${DATE}.sql.gz"

# Verificar
oci os object list --bucket-name $BUCKET --prefix "postgres/" | head -20
```

---

## 4. ORACLE OBJECT STORAGE (10GB Free)

### 4.1 Configuração

1. Oracle Cloud Console → Storage → Buckets
2. Create Bucket
   - Name: `vbq-backups`
   - Storage Tier: Standard
   - Visibility: Private
3. Criar API Key para acesso programático

### 4.2 Instalar OCI CLI

```bash
# Instalar OCI CLI
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Configurar
oci setup config
# Seguir wizard: upload public key, enter region, etc.
```

---

## 5. AGENDAMENTO (crontab)

```bash
# Editar crontab
crontab -e

# Backup diário às 3h da manhã
0 3 * * * /backups/scripts/backup-db.sh

# Backup semanal aos domingos às 2h
0 2 * * 0 /backups/scripts/upload-cloud.sh

# Verificação mensal (dia 1 às 1h)
0 1 1 * * /backups/scripts/test-restore.sh
```

---

## 6. TESTE DE RESTAURAÇÃO

### 6.1 Procedimento Mensal

```bash
#!/bin/bash
# /backups/scripts/test-restore.sh

# 1. Listar backups disponíveis
ls -la /backups/postgres/

# 2. Restaurar em database de teste
docker exec vb-postgres psql -U vb_admin -c "CREATE DATABASE test_restore;"
docker exec -i vb-postgres psql -U vb_admin test_restore < /backups/postgres/valuebetting_latest.sql

# 3. Verificar integridade
docker exec vb-postgres psql -U vb_admin test_restore -c "SELECT COUNT(*) FROM bronze.raw_games;"

# 4. Limpar
docker exec vb-postgres psql -U vb_admin -c "DROP DATABASE test_restore;"

logger "Teste de restore mensal concluído"
```

---

## 7. RETENÇÃO

| Tipo | Retenção | Localização |
|------|----------|-------------|
| Backup diário local | 7 dias | /backups/postgres/ |
| Backup semanal cloud | 4 semanas | Oracle Object Storage |
| Backup mensal arquivado | 12 meses | Oracle Object Storage |

---

## 8. CUSTO

| Componente | Custo |
|------------|-------|
| Backup local (no VPS) | 0€ (incluído no 200GB) |
| Oracle Object Storage (10GB) | **0€** (Always-Free) |
| Transferência de dados | **0€** (10TB/mês incluso) |
| **TOTAL** | **0€** |

---

## 9. CHECKLIST

- [ ] Script de backup diário criado
- [ ] Script de upload semanal criado
- [ ] Bucket Oracle Object Storage criado
- [ ] OCI CLI configurado
- [ ] Crontab configurado
- [ ] Teste de restore mensal agendado
- [ ] Retenção configurada (7 dias local, 4 semanas cloud)

---

## 10. RECOVERY PROCEDURES

### Recovery Point Objective (RPO)
- **Máxima perda de dados:** 24 horas

### Recovery Time Objective (RTO)
- **Tempo máximo de recuperação:** 2 horas

---

## 10. IMPLEMENTAÇÃO COMPLETA

### 10.1 Script Robusto de Backup Automatizado
```python
"""
Script robusto de backup automatizado
Inclui backup local, upload para cloud, verificação de integridade e alertas
"""

import os
import logging
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
import hashlib
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackupManager:
    """Gestor de backup completo"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.backup_history = []
        
        # Criar diretórios
        self.local_backup_dir = Path(config['local_backup_dir'])
        self.local_backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("🗄️  BackupManager inicializado")
    
    def backup_postgres(self, container_name: str, db_name: str, db_user: str) -> Optional[str]:
        """
        Realiza backup do PostgreSQL
        Retorna caminho do arquivo de backup ou None em caso de erro
        """
        logger.info(f"📦 Iniciando backup PostgreSQL: {db_name}")
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{db_name}_{timestamp}.sql.gz"
            backup_path = self.local_backup_dir / backup_filename
            
            # Comando pg_dump via Docker
            cmd = [
                'docker', 'exec', container_name,
                'pg_dump', '-U', db_user, db_name
            ]
            
            # Executar backup e comprimir
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Comprimir com gzip
            with gzip.open(backup_path, 'wb') as f:
                f.write(result.stdout.encode())
            
            # Calcular checksum
            checksum = self._calculate_checksum(backup_path)
            file_size = backup_path.stat().st_size
            
            logger.info(f"✅ Backup criado: {backup_filename} ({file_size / 1024 / 1024:.2f} MB)")
            logger.info(f"   Checksum: {checksum}")
            
            # Guardar no histórico
            self.backup_history.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'postgres',
                'database': db_name,
                'filename': backup_filename,
                'path': str(backup_path),
                'size_bytes': file_size,
                'checksum': checksum,
                'status': 'success'
            })
            
            return str(backup_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro ao executar pg_dump: {e}")
            logger.error(f"   Stderr: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            return None
    
    def backup_docker_volumes(self, volumes: List[str]) -> bool:
        """
        Realiza backup de volumes Docker
        """
        logger.info(f"📦 Iniciando backup de volumes Docker: {volumes}")
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for volume in volumes:
                backup_filename = f"volume_{volume}_{timestamp}.tar.gz"
                backup_path = self.local_backup_dir / backup_filename
                
                # Comando docker run para backup de volume
                cmd = [
                    'docker', 'run', '--rm',
                    '-v', f'{volume}:/data:ro',
                    '-v', str(self.local_backup_dir):'/backup',
                    'alpine',
                    'tar', 'czf', f'/backup/{backup_filename}', '-C', '/data', '.'
                ]
                
                subprocess.run(cmd, check=True)
                
                file_size = backup_path.stat().st_size
                logger.info(f"✅ Volume {volume} backup: {file_size / 1024 / 1024:.2f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao backup volumes: {e}")
            return False
    
    def cleanup_old_backups(self, retention_days: int = 7):
        """
        Remove backups antigos baseado em retenção
        """
        logger.info(f"🧹 Limpando backups com mais de {retention_days} dias...")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            deleted_count = 0
            
            for backup_file in self.local_backup_dir.glob('*.sql.gz'):
                file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                if file_mtime < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"   Removido: {backup_file.name}")
            
            logger.info(f"✅ {deleted_count} backups removidos")
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar backups: {e}")
    
    def verify_backup_integrity(self, backup_path: str) -> bool:
        """
        Verifica integridade do backup
        """
        logger.info(f"🔍 Verificando integridade: {backup_path}")
        
        try:
            backup_file = Path(backup_path)
            
            # Verificar se arquivo existe
            if not backup_file.exists():
                logger.error("   Arquivo não existe")
                return False
            
            # Verificar tamanho
            file_size = backup_file.stat().st_size
            if file_size == 0:
                logger.error("   Arquivo vazio")
                return False
            
            # Verificar checksum se disponível
            backup_record = next(
                (b for b in self.backup_history if b['path'] == backup_path),
                None
            )
            
            if backup_record:
                current_checksum = self._calculate_checksum(backup_file)
                if current_checksum != backup_record['checksum']:
                    logger.error("   Checksum mismatch!")
                    return False
            
            logger.info("✅ Integridade verificada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar integridade: {e}")
            return False
    
    def upload_to_cloud(self, backup_path: str, bucket_name: str, namespace: str) -> bool:
        """
        Upload backup para Oracle Object Storage
        """
        logger.info(f"☁️  Upload para cloud: {backup_path}")
        
        try:
            backup_file = Path(backup_path)
            object_name = f"postgres/{backup_file.name}"
            
            # Comando OCI CLI
            cmd = [
                'oci', 'os', 'object', 'put',
                '--bucket-name', bucket_name,
                '--namespace-name', namespace,
                '--file', str(backup_file),
                '--name', object_name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"✅ Upload completado: {object_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro ao upload: {e}")
            logger.error(f"   Stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao upload: {e}")
            return False
    
    def list_cloud_backups(self, bucket_name: str, namespace: str) -> List[str]:
        """
        Lista backups na cloud
        """
        logger.info("📋 Listando backups na cloud...")
        
        try:
            cmd = [
                'oci', 'os', 'object', 'list',
                '--bucket-name', bucket_name,
                '--namespace-name', namespace
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse JSON output
            objects = json.loads(result.stdout)
            backup_names = [obj['name'] for obj in objects]
            
            logger.info(f"✅ {len(backup_names)} backups encontrados")
            return backup_names
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar backups: {e}")
            return []
    
    def restore_postgres(self, backup_path: str, container_name: str, 
                        db_name: str, db_user: str, test_mode: bool = False) -> bool:
        """
        Restaura backup do PostgreSQL
        """
        logger.info(f"🔄 Restaurando backup: {backup_path}")
        
        try:
            backup_file = Path(backup_path)
            
            # Verificar integridade antes de restaurar
            if not self.verify_backup_integrity(backup_path):
                logger.error("Backup corrompido, abortando restore")
                return False
            
            # Nome do database de teste se test_mode
            target_db = f"{db_name}_test_restore" if test_mode else db_name
            
            # Descomprimir
            with gzip.open(backup_file, 'rb') as f:
                sql_content = f.read()
            
            # Restaurar via Docker
            cmd = [
                'docker', 'exec', '-i', container_name,
                'psql', '-U', db_user, target_db
            ]
            
            subprocess.run(cmd, input=sql_content, check=True)
            
            logger.info(f"✅ Restore completado: {target_db}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao restaurar: {e}")
            return False
    
    def test_restore(self, container_name: str, db_name: str, db_user: str) -> bool:
        """
        Testa restore em database temporário
        """
        logger.info("🧪 Testando restore...")
        
        try:
            # Criar database de teste
            create_cmd = [
                'docker', 'exec', container_name,
                'psql', '-U', db_user, '-c',
                f"CREATE DATABASE {db_name}_test_restore;"
            ]
            subprocess.run(create_cmd, check=True)
            
            # Pegar backup mais recente
            latest_backup = max(self.local_backup_dir.glob('*.sql.gz'), 
                              key=lambda p: p.stat().st_mtime)
            
            # Restaurar
            success = self.restore_postgres(
                str(latest_backup), container_name, db_name, db_user, test_mode=True
            )
            
            if success:
                # Verificar integridade
                verify_cmd = [
                    'docker', 'exec', container_name,
                    'psql', '-U', db_user, f'{db_name}_test_restore',
                    '-c', "SELECT COUNT(*) FROM bronze.raw_games;"
                ]
                result = subprocess.run(verify_cmd, capture_output=True, text=True)
                logger.info(f"   Registros verificados: {result.stdout}")
            
            # Limpar database de teste
            drop_cmd = [
                'docker', 'exec', container_name,
                'psql', '-U', db_user, '-c',
                f"DROP DATABASE {db_name}_test_restore;"
            ]
            subprocess.run(drop_cmd, check=True)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar restore: {e}")
            return False
    
    def generate_backup_report(self) -> str:
        """Gera relatório de backup"""
        report = "# Relatório de Backup\n\n"
        report += f"Gerado em: {datetime.now().isoformat()}\n\n"
        
        report += "## Histórico de Backups\n\n"
        for backup in self.backup_history[-10:]:  # Últimos 10
            report += f"- {backup['timestamp']}: {backup['filename']} ({backup['size_bytes'] / 1024 / 1024:.2f} MB)\n"
        
        report += "\n## Estatísticas\n\n"
        report += f"Total de backups: {len(self.backup_history)}\n"
        
        if self.backup_history:
            total_size = sum(b['size_bytes'] for b in self.backup_history)
            report += f"Tamanho total: {total_size / 1024 / 1024 / 1024:.2f} GB\n"
        
        return report
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calcula checksum SHA256 do arquivo"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()

class BackupScheduler:
    """Agendador de backups"""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
    
    def run_daily_backup(self, container_name: str, db_name: str, db_user: str):
        """Executa backup diário"""
        logger.info("📅 Executando backup diário...")
        
        # Backup PostgreSQL
        backup_path = self.backup_manager.backup_postgres(
            container_name, db_name, db_user
        )
        
        if backup_path:
            # Verificar integridade
            self.backup_manager.verify_backup_integrity(backup_path)
            
            # Limpar backups antigos
            self.backup_manager.cleanup_old_backups(retention_days=7)
        
        return backup_path is not None
    
    def run_weekly_backup(self, container_name: str, db_name: str, db_user: str,
                         bucket_name: str, namespace: str):
        """Executa backup semanal com upload para cloud"""
        logger.info("📅 Executando backup semanal...")
        
        # Backup PostgreSQL
        backup_path = self.backup_manager.backup_postgres(
            container_name, db_name, db_user
        )
        
        if backup_path:
            # Upload para cloud
            self.backup_manager.upload_to_cloud(backup_path, bucket_name, namespace)
        
        return backup_path is not None
    
    def run_monthly_test(self, container_name: str, db_name: str, db_user: str):
        """Executa teste mensal de restore"""
        logger.info("📅 Executando teste mensal de restore...")
        
        success = self.backup_manager.test_restore(
            container_name, db_name, db_user
        )
        
        if success:
            logger.info("✅ Teste de restore bem-sucedido")
        else:
            logger.error("❌ Teste de restore falhou")
        
        return success

# Uso
if __name__ == "__main__":
    import gzip
    
    # Configuração
    config = {
        'local_backup_dir': '/backups/postgres',
        'cloud_bucket': 'vbq-backups',
        'cloud_namespace': 'your-namespace'
    }
    
    # Criar gestor
    manager = BackupManager(config)
    
    # Criar agendador
    scheduler = BackupScheduler(manager)
    
    # Executar backup diário
    success = scheduler.run_daily_backup(
        container_name='vb-postgres',
        db_name='valuebetting',
        db_user='vb_admin'
    )
    
    # Gerar relatório
    report = manager.generate_backup_report()
    print(report)
```

---

## 11. LINKS

- [[DISASTER_RECOVERY]] → Plano completo de DR
- [[VPS_CONFIGURACAO]] → Configuração de VPS
- [[10_Infrastructure/INDEX]] ← Secção mãe

---

**Backup 100% Gratuito — Proteção Total do Sistema**
