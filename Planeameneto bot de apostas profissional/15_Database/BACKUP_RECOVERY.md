# Backup and Recovery Strategy

**ID:** `DBR-001` | **Fase:** #phase/1 | **Owner:** DevOps Lead + DBA | **Status:** #status/active

---

## 1. OVERVIEW

This document defines the comprehensive backup and recovery strategy for the VBQ-UNIFIED system. Given the financial nature of the data (betting records, PnL, model predictions) and the criticality of ML models, a robust backup strategy is essential.

### Scope
- PostgreSQL database (all schemas)
- Redis cache (optional - can be rebuilt)
- MLflow artifacts (model versions, experiment data)
- Trained ML models (XGBoost models, meta-models)
- Configuration files (.env, docker-compose.yml)
- Application logs

### Recovery Objectives
- **RPO (Recovery Point Objective):** 1 hour (max data loss acceptable)
- **RTO (Recovery Time Objective):** 4 hours (max downtime acceptable)

---

## 2. BACKUP STRATEGY

### 2.1 PostgreSQL Database

#### Backup Types
1. **Full Daily Backup**
   - Schedule: 02:00 UTC daily
   - Method: `pg_dump` with custom format
   - Retention: 30 days
   - Compression: gzip (level 9)

2. **WAL Archiving (Continuous)**
   - Method: Continuous WAL archiving to S3/remote storage
   - Retention: 7 days
   - Enables point-in-time recovery (PITR)

3. **Weekly Schema Backup**
   - Schedule: Sunday 03:00 UTC
   - Method: `pg_dumpall --schema-only`
   - Retention: 90 days
   - Purpose: Schema evolution tracking

#### Backup Script
```bash
#!/bin/bash
# scripts/backup_postgres.sh

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Full backup
pg_dump -h postgres -U vb_admin -d valuebetting \
  -F c -f "$BACKUP_DIR/valuebetting_$DATE.dump" \
  --compress=9

# Compress and encrypt
gzip "$BACKUP_DIR/valuebetting_$DATE.dump"
gpg --encrypt --recipient your-email@example.com \
  "$BACKUP_DIR/valuebetting_$DATE.dump.gz"

# Upload to remote storage
aws s3 cp "$BACKUPDIR/valuebetting_$DATE.dump.gz.gpg" \
  s3://vbq-backups/postgres/

# Cleanup old backups
find "$BACKUP_DIR" -name "*.dump.gz.gpg" -mtime +$RETENTION_DAYS -delete
```

### 2.2 MLflow Artifacts

#### Backup Strategy
- **Frequency:** Daily after model training
- **Method:** rsync to remote storage
- **Retention:** 90 days
- **Location:** `/mlflow/artifacts`

#### Backup Script
```bash
#!/bin/bash
# scripts/backup_mlflow.sh

BACKUP_DIR="/backups/mlflow"
MLFLOW_DIR="/mlflow/artifacts"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=90

# Create backup
rsync -avz --delete "$MLFLOW_DIR/" "$BACKUP_DIR/mlflow_$DATE/"

# Compress
tar -czf "$BACKUP_DIR/mlflow_$DATE.tar.gz" \
  -C "$BACKUP_DIR" "mlflow_$date/"

# Upload to remote storage
aws s3 cp "$BACKUP_DIR/mlflow_$DATE.tar.gz" \
  s3://vbq-backups/mlflow/

# Cleanup
find "$BACKUP_DIR" -name "mlflow_*.tar.gz" -mtime +$RETENTION_DAYS -delete
```

### 2.3 Trained ML Models

#### Backup Strategy
- **Frequency:** After each model promotion to production
- **Method:** Copy to S3 with versioning
- **Retention:** Indefinite (all production models)
- **Location:** `/models/production`

#### Backup Script
```bash
#!/bin/bash
# scripts/backup_models.sh

MODELS_DIR="/models/production"
BACKUP_BUCKET="s3://vbq-backups/models/"

# Copy all production models with versioning
aws s3 sync "$MODELS_DIR/" "$BACKUP_BUCKET" \
  --storage-class STANDARD_IA \
  --metadata "backup-date=$(date +%Y-%m-%d)"
```

### 2.4 Configuration Files

#### Backup Strategy
- **Frequency:** After any configuration change
- **Method:** Git commit + encrypted backup
- **Retention:** Indefinite (Git history)

#### Files to Backup
- `.env` (encrypted)
- `docker-compose.yml`
- `docker/Dockerfile`
- `config/*.yaml`

#### Backup Script
```bash
#!/bin/bash
# scripts/backup_config.sh

CONFIG_DIR="/opt/valuebetting"
BACKUP_DIR="/backups/config"
DATE=$(date +%Y%m%d_%H%M%S)

# Encrypt .env
gpg --encrypt --recipient your-email@example.com \
  "$CONFIG_DIR/.env"

# Copy config files
cp "$CONFIG_DIR/docker-compose.yml" "$BACKUP_DIR/"
cp "$CONFIG_DIR/.env.gpg" "$BACKUP_DIR/"

# Upload to S3
aws s3 sync "$BACKUP_DIR/" s3://vbq-backups/config/
```

---

## 3. RETENTION POLICY

| Data Type | Daily Retention | Weekly Retention | Monthly Retention | Archive |
|-----------|----------------|------------------|------------------|---------|
| PostgreSQL Full | 7 days | 4 weeks | 12 months | 7 years |
| PostgreSQL WAL | 7 days | - | - | - |
| MLflow Artifacts | 7 days | 4 weeks | 12 months | 3 years |
| ML Models | Indefinite | - | - | Indefinite |
| Config Files | Indefinite | - | - | Indefinite |
| Logs | 7 days | 4 weeks | 12 months | 1 year |

---

## 4. OFF-SITE BACKUP

### 4.1 Primary Off-Site Location
- **Provider:** AWS S3 (eu-central-1)
- **Bucket:** `vbq-backups`
- **Storage Class:** STANDARD_IA (Infrequent Access)
- **Encryption:** Server-side encryption (AES-256)
- **Versioning:** Enabled
- **Lifecycle Rules:**
  - Move to GLACIER after 90 days
  - Delete after 7 years

### 4.2 Secondary Off-Site Location
- **Provider:** Hetzner Storage Box
- **Location:** Frankfurt
- **Purpose:** Geographic redundancy
- **Sync:** Daily via rsync

### 4.3 Backup Verification
- **Weekly:** Verify backup integrity (checksums)
- **Monthly:** Test restore of random backup
- **Quarterly:** Full disaster recovery drill

---

## 5. RECOVERY PROCEDURES

### 5.1 PostgreSQL Recovery

#### Scenario 1: Full Database Restore
```bash
#!/bin/bash
# scripts/restore_postgres.sh

BACKUP_FILE=$1  # Path to backup file
TARGET_HOST="localhost"

# Download backup from S3
aws s3 cp "s3://vbq-backups/postgres/$BACKUP_FILE" /tmp/

# Decrypt
gpg --decrypt /tmp/$BACKUP_FILE > /tmp/backup.dump.gz
gunzip /tmp/backup.dump.gz

# Restore
pg_restore -h $TARGET_HOST -U vb_admin -d valuebetting \
  -c -F c /tmp/backup.dump

# Cleanup
rm /tmp/backup.dump
```

#### Scenario 2: Point-in-Time Recovery (PITR)
```bash
#!/bin/bash
# scripts/restore_pitr.sh

TARGET_TIME="2026-05-17 14:00:00 UTC"

# Restore base backup
pg_restore -h localhost -U vb_admin -d valuebetting \
  -c -F c /backups/postgres/base_backup.dump

# Replay WAL logs up to target time
pg_rewind -D /var/lib/postgresql/data \
  --target-timeline=$(ls /backups/wal/ | tail -1) \
  --target-time="$TARGET_TIME"
```

### 5.2 MLflow Recovery

```bash
#!/bin/bash
# scripts/restore_mlflow.sh

BACKUP_FILE=$1

# Download and extract
aws s3 cp "s3://vbq-backups/mlflow/$BACKUP_FILE" /tmp/
tar -xzf /tmp/$BACKUP_FILE -C /mlflow/artifacts/

# Restart MLflow service
docker-compose restart mlflow
```

### 5.3 Model Recovery

```bash
#!/bin/bash
# scripts/restore_models.sh

MODEL_VERSION=$1

# Download specific model version
aws s3 sync "s3://vbq-backups/models/$MODEL_VERSION/" \
  "/models/production/$MODEL_VERSION/"

# Update model registry
curl -X POST http://localhost:5000/api/2.0/mlflow/model-versions/transition-stage \
  -d '{"name":"valuebetting_model","version":'$MODEL_VERSION',"stage":"Production"}'
```

---

## 6. DISASTER RECOVERY PLAN

### 6.1 Disaster Scenarios

| Scenario | Impact | Recovery Time | Procedure |
|----------|--------|---------------|-----------|
| VPS failure | Complete outage | 4-8 hours | Restore from backup to new VPS |
| Database corruption | Data loss | 2-4 hours | PITR to last consistent state |
| Ransomware attack | Complete compromise | 24-48 hours | Restore from immutable backups |
| Region outage | Geographic outage | 8-12 hours | Failover to secondary region |

### 6.2 Disaster Recovery Checklist

**Immediate Response (0-1 hour):**
- [ ] Declare disaster incident
- [ ] Notify stakeholders
- [ ] Assess scope and impact
- [ ] Activate DR team

**Recovery Phase (1-4 hours):**
- [ ] Provision new infrastructure
- [ ] Restore PostgreSQL from latest backup
- [ ] Restore MLflow artifacts
- [ ] Restore ML models
- [ ] Restore configuration files
- [ ] Update DNS if needed

**Validation Phase (4-8 hours):**
- [ ] Verify database integrity
- [ ] Run smoke tests
- [ ] Verify model predictions
- [ ] Test alerting systems
- [ ] Load test critical paths

**Post-Recovery (8-24 hours):**
- [ ] Monitor for anomalies
- [ ] Update documentation
- [ ] Conduct postmortem
- [ ] Implement improvements

### 6.3 Failover Procedure

```bash
#!/bin/bash
# scripts/failover.sh

# 1. Stop all services on primary
ssh primary-vps "docker-compose down"

# 2. Promote secondary to primary
ssh secondary-vps "
  docker-compose up -d
  ./scripts/restore_postgres.sh latest_backup.dump
  ./scripts/restore_mlflow.sh latest_mlflow.tar.gz
  ./scripts/restore_models.sh latest
"

# 3. Update DNS (manual or automated)
# Update A record to point to secondary-vps IP

# 4. Verify
curl https://api.valuebetting.com/health
```

---

## 7. BACKUP TESTING

### 7.1 Automated Tests
- **Daily:** Backup completion check (Nagios/Prometheus alert)
- **Weekly:** Backup integrity verification (checksums)
- **Monthly:** Automated restore test (staging environment)

### 7.2 Manual Tests
- **Quarterly:** Full disaster recovery drill
- **Annually:** Third-party backup audit

### 7.3 Test Script
```bash
#!/bin/bash
# scripts/test_backup.sh

# Test PostgreSQL restore
TEST_DB="valuebetting_test"
BACKUP_FILE=$(ls -t /backups/postgres/*.dump.gz.gpg | head -1)

# Decrypt and restore to test database
gpg --decrypt "$BACKUP_FILE" > /tmp/test_backup.dump.gz
gunzip /tmp/test_backup.dump.gz
pg_restore -h localhost -U vb_admin -d $TEST_DB \
  -c -F c /tmp/test_backup.dump

# Verify data
psql -h localhost -U vb_admin -d $TEST_DB -c "
  SELECT COUNT(*) FROM bronze.raw_games;
  SELECT COUNT(*) FROM silver.clean_odds;
"

# Cleanup
dropdb $TEST_DB
rm /tmp/test_backup.dump
```

---

## 8. MONITORING AND ALERTING

### 8.1 Metrics to Monitor
- Backup success/failure rate
- Backup size trends
- Backup duration
- Restore test success rate
- Storage utilization

### 8.2 Alerts
- **Critical:** Backup failed for 2+ consecutive days
- **Warning:** Backup size decreased by >20% (possible data loss)
- **Info:** Monthly backup summary

### 8.3 Grafana Dashboard
Create dashboard `Backup-Monitoring` with panels:
- Backup success rate (last 30 days)
- Backup duration trend
- Storage utilization by backup type
- Restore test results

---

## 9. SECURITY CONSIDERATIONS

### 9.1 Encryption
- All backups encrypted at rest (AES-256)
- All backups encrypted in transit (TLS)
- Encryption keys stored in AWS KMS or HashiCorp Vault

### 9.2 Access Control
- Backup access restricted to DevOps team
- MFA required for backup operations
- Audit logging for all backup/restore operations

### 9.3 Compliance
- GDPR: Personal data encrypted and retained per policy
- Financial regulations: PnL data retained for 7 years

---

## 10. DOCUMENTATION AND TRAINING

### 10.1 Documentation
- This document (updated quarterly)
- Runbooks for each recovery scenario
- Backup verification reports (monthly)

### 10.2 Training
- New DevOps engineers trained on backup procedures
- Annual DR drill for entire team
- Documentation review after each incident

---

## 11. CONTACTS AND RESPONSIBILITIES

| Role | Responsibility | Contact |
|------|----------------|---------|
| DevOps Lead | Backup execution and monitoring | devops@valuebetting.com |
| DBA | Database recovery procedures | dba@valuebetting.com |
| ML Engineer | Model backup verification | ml@valuebetting.com |
| CTO | Disaster recovery coordination | cto@valuebetting.com |

---

**Last Updated:** 2026-05-17
**Next Review:** 2026-08-17
