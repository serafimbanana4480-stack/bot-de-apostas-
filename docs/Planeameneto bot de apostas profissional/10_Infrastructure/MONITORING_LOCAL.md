# Monitoring Local - Setup Zero Euros

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  

---

## 🎯 OBJETIVO

Sistema de monitoring básico local para stack VBQ-UNIFIED zero euros, sem Grafana/Prometheus, usando logging e health checks simples.

---

## 📊 ARQUITETURA DE MONITORING

### **Componentes de Monitoring**
```python
# 1. Logging Estruturado (JSON)
# 2. Health Checks Automáticos
# 3. Métricas do Sistema (psutil)
# 4. Alertas Simples (Telegram)
# 5. Dashboard Básico (Streamlit)
```

### **Stack vs Original**
```
ORIGINAL (Grafana + Prometheus):
- Dashboards avançados
- Metrics collection automática
- Alerting complexo
- Alto overhead

LOCAL (Logging + Health Checks):
- Logging estruturado
- Health checks manuais
- Alertas simples
- Baixo overhead
```

---

## 📝 LOGGING ESTRUTURADO

### **Configuração de Logging**
```python
import logging
import json
from datetime import datetime
from pathlib import Path

class StructuredLogger:
    """Logger estruturado em JSON"""
    
    def __init__(self, name, log_dir='logs'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Criar diretório de logs
        Path(log_dir).mkdir(exist_ok=True)
        
        # Handler para arquivo JSON
        file_handler = logging.FileHandler(f'{log_dir}/{name}.json')
        file_handler.setLevel(logging.INFO)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter JSON
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log(self, level, message, **kwargs):
        """Registra log estruturado"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            **kwargs
        }
        self.logger.info(json.dumps(log_entry))
    
    def info(self, message, **kwargs):
        self.log('INFO', message, **kwargs)
    
    def warning(self, message, **kwargs):
        self.log('WARNING', message, **kwargs)
    
    def error(self, message, **kwargs):
        self.log('ERROR', message, **kwargs)
    
    def critical(self, message, **kwargs):
        self.log('CRITICAL', message, **kwargs)

# Uso
logger = StructuredLogger('vbq_api')

logger.info('API iniciada', port=8000, environment='development')
logger.warning('Conexão lenta', latency=2.5, endpoint='/api/predict')
logger.error('Erro de database', error='connection refused', retry=3)
```

---

## 🏥 HEALTH CHECKS

### **Sistema de Health Checks**
```python
import requests
import psycopg2
import redis
from datetime import datetime

class HealthChecker:
    """Sistema de health checks"""
    
    def __init__(self):
        self.checks = {
            'api': self.check_api,
            'database': self.check_database,
            'redis': self.check_redis,
            'models': self.check_models,
            'disk_space': self.check_disk_space
        }
    
    def check_api(self):
        """Health check da API"""
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def check_database(self):
        """Health check do database"""
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='valuebetting',
                user='vb_admin',
                password='your_password'
            )
            conn.close()
            return {'status': 'healthy'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def check_redis(self):
        """Health check do Redis"""
        try:
            r = redis.Redis(host='localhost', port=6379, 
                           password='your_password', decode_responses=True)
            r.ping()
            return {'status': 'healthy'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def check_models(self):
        """Health check dos modelos"""
        try:
            from pathlib import Path
            model_dir = Path('models')
            
            if model_dir.exists() and len(list(model_dir.glob('*.pkl'))) > 0:
                return {'status': 'healthy', 'models': len(list(model_dir.glob('*.pkl')))}
            else:
                return {'status': 'warning', 'message': 'No models found'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def check_disk_space(self):
        """Health check do espaço em disco"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            
            free_percent = (free / total) * 100
            
            if free_percent < 10:
                return {'status': 'critical', 'free_percent': free_percent}
            elif free_percent < 20:
                return {'status': 'warning', 'free_percent': free_percent}
            else:
                return {'status': 'healthy', 'free_percent': free_percent}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    def run_all_checks(self):
        """Executa todos os health checks"""
        results = {}
        
        for name, check_func in self.checks.items():
            results[name] = check_func()
        
        # Status geral
        all_healthy = all(
            r.get('status') == 'healthy' 
            for r in results.values()
        )
        
        results['overall'] = {
            'status': 'healthy' if all_healthy else 'unhealthy',
            'timestamp': datetime.now().isoformat()
        }
        
        return results
    
    def print_report(self):
        """Imprime relatório de health checks"""
        results = self.run_all_checks()
        
        print("🏥 Health Check Report")
        print("="*50)
        
        for name, result in results.items():
            if name == 'overall':
                continue
            
            status = result.get('status', 'unknown')
            icon = '✅' if status == 'healthy' else '⚠️' if status == 'warning' else '❌'
            
            print(f"{icon} {name}: {status}")
            
            if 'error' in result:
                print(f"   Error: {result['error']}")
            
            if 'free_percent' in result:
                print(f"   Free space: {result['free_percent']:.1f}%")
        
        print("="*50)
        print(f"Overall: {results['overall']['status']}")
        print(f"Timestamp: {results['overall']['timestamp']}")

# Uso
checker = HealthChecker()
checker.print_report()
```

---

## 📈 MÉTRICAS DO SISTEMA

### **Coletor de Métricas**
```python
import psutil
import time
from datetime import datetime

class SystemMetricsCollector:
    """Coletor de métricas do sistema"""
    
    def collect_all(self):
        """Coleta todas as métricas"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu': self.get_cpu_metrics(),
            'memory': self.get_memory_metrics(),
            'disk': self.get_disk_metrics(),
            'network': self.get_network_metrics()
        }
        return metrics
    
    def get_cpu_metrics(self):
        """Métricas de CPU"""
        return {
            'percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
    
    def get_memory_metrics(self):
        """Métricas de memória"""
        mem = psutil.virtual_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'percent': mem.percent,
            'used': mem.used
        }
    
    def get_disk_metrics(self):
        """Métricas de disco"""
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }
    
    def get_network_metrics(self):
        """Métricas de rede"""
        net = psutil.net_io_counters()
        return {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv
        }

# Uso
collector = SystemMetricsCollector()
metrics = collector.collect_all()
print(json.dumps(metrics, indent=2))
```

---

## 🚨 SISTEMA DE ALERTAS

### **Alertas via Telegram**
```python
import requests
import os

class TelegramAlerter:
    """Sistema de alertas via Telegram"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_alert(self, message):
        """Envia alerta via Telegram"""
        url = f"{self.api_url}/sendMessage"
        
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print("✅ Alerta enviado via Telegram")
            else:
                print(f"❌ Erro enviando alerta: {response.status_code}")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def send_health_alert(self, health_results):
        """Envia alerta se health check falhar"""
        overall_status = health_results['overall']['status']
        
        if overall_status != 'healthy':
            message = f"⚠️ *Health Check Failed*\n\n"
            
            for name, result in health_results.items():
                if name == 'overall':
                    continue
                
                if result.get('status') != 'healthy':
                    message += f"❌ {name}: {result.get('status')}\n"
                    if 'error' in result:
                        message += f"   Error: {result['error']}\n"
            
            self.send_alert(message)
    
    def send_system_alert(self, metrics):
        """Envia alerta se recursos críticos"""
        alerts = []
        
        # CPU > 90%
        if metrics['cpu']['percent'] > 90:
            alerts.append(f"CPU: {metrics['cpu']['percent']:.1f}%")
        
        # Memory > 90%
        if metrics['memory']['percent'] > 90:
            alerts.append(f"Memory: {metrics['memory']['percent']:.1f}%")
        
        # Disk < 10%
        if metrics['disk']['percent'] > 90:
            alerts.append(f"Disk: {metrics['disk']['percent']:.1f}% used")
        
        if alerts:
            message = f"🚨 *System Alert*\n\n"
            for alert in alerts:
                message += f"❌ {alert}\n"
            
            self.send_alert(message)

# Uso
alerter = TelegramAlerter()

# Health check alert
health_results = checker.run_all_checks()
alerter.send_health_alert(health_results)

# System alert
metrics = collector.collect_all()
alerter.send_system_alert(metrics)
```

---

## 📊 DASHBOARD BÁSICO

### **Streamlit Dashboard**
```python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json

class MonitoringDashboard:
    """Dashboard de monitoring com Streamlit"""
    
    def __init__(self):
        self.checker = HealthChecker()
        self.collector = SystemMetricsCollector()
    
    def render(self):
        """Renderiza dashboard"""
        st.set_page_config(page_title="VBQ Monitoring", layout="wide")
        
        st.title("🔍 VBQ-UNIFIED Monitoring Dashboard")
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["Health Checks", "System Metrics", "Logs"])
        
        with tab1:
            self.render_health_checks()
        
        with tab2:
            self.render_system_metrics()
        
        with tab3:
            self.render_logs()
    
    def render_health_checks(self):
        """Renderiza health checks"""
        st.header("🏥 Health Checks")
        
        results = self.checker.run_all_checks()
        
        # Status geral
        overall_status = results['overall']['status']
        status_color = "green" if overall_status == "healthy" else "red"
        st.markdown(f"**Overall Status:** :{status_color}[{overall_status.upper()}]")
        
        # Detalhes por componente
        for name, result in results.items():
            if name == 'overall':
                continue
            
            status = result.get('status', 'unknown')
            icon = "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"
            
            with st.expander(f"{icon} {name}"):
                st.json(result)
    
    def render_system_metrics(self):
        """Renderiza métricas do sistema"""
        st.header("📊 System Metrics")
        
        metrics = self.collector.collect_all()
        
        # CPU
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("CPU Usage", f"{metrics['cpu']['percent']:.1f}%")
        
        with col2:
            st.metric("Memory Usage", f"{metrics['memory']['percent']:.1f}%")
        
        with col3:
            st.metric("Disk Usage", f"{metrics['disk']['percent']:.1f}%")
        
        # Gráficos
        self.render_cpu_chart()
        self.render_memory_chart()
    
    def render_cpu_chart(self):
        """Renderiza gráfico de CPU"""
        st.subheader("CPU Usage Over Time")
        
        # Dados simulados (em produção, usar dados reais)
        times = pd.date_range(start=datetime.now() - pd.Timedelta(hours=1), 
                             periods=60, freq='min')
        cpu_data = [50 + i * 0.5 for i in range(60)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=times, y=cpu_data, mode='lines', name='CPU'))
        fig.update_layout(title='CPU Usage (%)', xaxis_title='Time', yaxis_title='CPU %')
        st.plotly_chart(fig, use_container_width=True)
    
    def render_memory_chart(self):
        """Renderiza gráfico de memória"""
        st.subheader("Memory Usage Over Time")
        
        times = pd.date_range(start=datetime.now() - pd.Timedelta(hours=1), 
                             periods=60, freq='min')
        memory_data = [60 + i * 0.3 for i in range(60)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=times, y=memory_data, mode='lines', name='Memory'))
        fig.update_layout(title='Memory Usage (%)', xaxis_title='Time', yaxis_title='Memory %')
        st.plotly_chart(fig, use_container_width=True)
    
    def render_logs(self):
        """Renderiza logs"""
        st.header("📝 Recent Logs")
        
        try:
            with open('logs/vbq_api.json', 'r') as f:
                logs = [json.loads(line) for line in f]
            
            # Mostrar últimos 50 logs
            recent_logs = logs[-50:]
            
            for log in recent_logs:
                level = log['level']
                message = log['message']
                timestamp = log['timestamp']
                
                if level == 'ERROR':
                    st.error(f"[{timestamp}] {message}")
                elif level == 'WARNING':
                    st.warning(f"[{timestamp}] {message}")
                else:
                    st.info(f"[{timestamp}] {message}")
        
        except FileNotFoundError:
            st.warning("No logs found")

# Executar dashboard
if __name__ == "__main__":
    dashboard = MonitoringDashboard()
    dashboard.render()
```

### **Iniciar Dashboard**
```bash
streamlit run monitoring_dashboard.py --server.port 8501
```

---

## 🔄 AUTOMAÇÃO DE MONITORING

### **Script de Monitoring Automático**
```python
import time
import schedule

class AutomatedMonitoring:
    """Monitoring automatizado"""
    
    def __init__(self):
        self.checker = HealthChecker()
        self.collector = SystemMetricsCollector()
        self.alerter = TelegramAlerter()
        self.logger = StructuredLogger('monitoring')
    
    def run_health_checks(self):
        """Executa health checks periódicos"""
        self.logger.info("Executando health checks agendados")
        
        results = self.checker.run_all_checks()
        
        # Log results
        self.logger.info("Health check results", 
                        overall=results['overall']['status'],
                        components=list(results.keys()))
        
        # Alertar se necessário
        self.alerter.send_health_alert(results)
    
    def run_system_metrics(self):
        """Coleta métricas do sistema"""
        metrics = self.collector.collect_all()
        
        self.logger.info("System metrics collected",
                        cpu=metrics['cpu']['percent'],
                        memory=metrics['memory']['percent'],
                        disk=metrics['disk']['percent'])
        
        # Alertar se crítico
        self.alerter.send_system_alert(metrics)
    
    def run_scheduler(self):
        """Executa scheduler de monitoring"""
        # Health checks a cada 5 minutos
        schedule.every(5).minutes.do(self.run_health_checks)
        
        # System metrics a cada 10 minutos
        schedule.every(10).minutes.do(self.run_system_metrics)
        
        self.logger.info("Monitoring scheduler iniciado")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

# Uso
monitoring = AutomatedMonitoring()
# monitoring.run_scheduler()  # Descomentar para executar
```

---

## 📋 CHECKLIST DE MONITORING

### **Logging**
- [ ] Logging estruturado configurado
- [ ] Logs guardados em arquivo
- [ ] Logs no console
- [ ] Formato JSON
- [ ] Níveis apropriados

### **Health Checks**
- [ ] API health check
- [ ] Database health check
- [ ] Redis health check
- [ ] Models health check
- [ ] Disk space check

### **Alertas**
- [ ] Telegram bot configurado
- [ ] Health check alerts
- [ ] System resource alerts
- [ ] Error logging
- [ ] Critical alerts

### **Dashboard**
- [ ] Streamlit dashboard
- [ ] Health checks display
- [ ] System metrics display
- [ ] Logs display
- [ ] Acessível localmente

---

## 🚀 PRÓXIMOS PASSOS

### **Implementação:**
1. **Configurar logging** em todos os componentes
2. **Implementar health checks** no FastAPI
3. **Configurar alertas** Telegram
4. **Criar dashboard** Streamlit
5. **Automatizar monitoring** com schedule

### **Melhorias Futuras:**
- Adicionar Grafana/Prometheus quando escalar para VPS
- Implementar tracing distribuído
- Adicionar métricas de negócio (ROI, CLV)
- Criar alertas avançados
- Integrar com sistema de tickets

---

**Status:** Monitoring local configurado  
**Custo:** 0€  
**Componentes:** Logging, Health Checks, Alertas, Dashboard  
**Overhead:** Mínimo  

---

#status/active #priority/critical #phase/infra-local
