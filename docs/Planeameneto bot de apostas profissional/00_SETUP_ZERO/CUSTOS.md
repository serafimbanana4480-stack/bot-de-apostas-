# Verificação de Custos Zero - Setup Zero Euros

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  

---

## 🎯 OBJETIVO

Verificação detalhada de todos os componentes do sistema para garantir que o custo total é **0€**, com calculadora interativa e projeção de custos para 12 meses.

---

## 🧮 CALCULADORA DE CUSTOS INTERATIVA

### **Script Python de Cálculo**
```python
"""
Calculadora de Custos - VBQ-UNIFIED Zero Euros
Calcula custos originais vs zero euros e projeção 12 meses
"""

class CostCalculator:
    """Calculadora de custos do sistema"""
    
    def __init__(self):
        self.costs = {
            'infrastructure': {
                'original_monthly': 77.5,  # média de 70-85
                'zero_monthly': 0,
                'components': ['VPS', 'Domínio', 'SSL']
            },
            'data_apis': {
                'original_monthly': 75,  # média de 50-100
                'zero_monthly': 0,
                'components': ['Pinnacle odds', 'Betfair API', 'NBA API', 'The-Odds-API']
            },
            'database_cache': {
                'original_monthly': 97.5,  # média de 55-140
                'zero_monthly': 0,
                'components': ['PostgreSQL', 'Redis', 'S3 Storage']
            },
            'monitoring': {
                'original_monthly': 100,  # média de 90-110
                'zero_monthly': 0,
                'components': ['MLflow', 'Grafana', 'Prometheus']
            },
            'communication': {
                'original_monthly': 5,  # variável
                'zero_monthly': 0,
                'components': ['Email', 'SMS', 'Notificações']
            }
        }
        
        self.hidden_costs = {
            'electricity_monthly': 7.5,  # 5-10€
            'setup_time_weeks': 2,
            'maintenance_hours_weekly': 2
        }
    
    def calculate_monthly(self):
        """Calcula custo mensal"""
        original_total = sum(c['original_monthly'] for c in self.costs.values())
        zero_total = sum(c['zero_monthly'] for c in self.costs.values())
        electricity = self.hidden_costs['electricity_monthly']
        
        return {
            'original': original_total,
            'zero': zero_total,
            'zero_with_electricity': zero_total + electricity,
            'savings': original_total - zero_total,
            'savings_percentage': ((original_total - zero_total) / original_total * 100)
        }
    
    def project_12_months(self):
        """Projeta custos para 12 meses"""
        monthly = self.calculate_monthly()
        
        original_yearly = monthly['original'] * 12
        zero_yearly = monthly['zero'] * 12
        zero_yearly_with_electricity = monthly['zero_with_electricity'] * 12
        savings_yearly = monthly['savings'] * 12
        
        return {
            'original_yearly': original_yearly,
            'zero_yearly': zero_yearly,
            'zero_yearly_with_electricity': zero_yearly_with_electricity,
            'savings_yearly': savings_yearly
        }
    
    def calculate_roi(self):
        """Calcula ROI e trade-offs"""
        yearly = self.project_12_months()
        
        return {
            'roi_yearly': yearly['savings_yearly'],
            'setup_time_cost': self.hidden_costs['setup_time_weeks'] * 40,  # horas
            'maintenance_yearly': self.hidden_costs['maintenance_hours_weekly'] * 52,
            'break_even_months': 1  # poupança imediata
        }
    
    def generate_report(self):
        """Gera relatório completo"""
        monthly = self.calculate_monthly()
        yearly = self.project_12_months()
        roi = self.calculate_roi()
        
        print("="*70)
        print("🧮 RELATÓRIO DE CUSTOS - VBQ-UNIFIED ZERO EUROS")
        print("="*70)
        
        print("\n📊 CUSTO MENSAL")
        print(f"Original:  €{monthly['original']:.2f}/mês")
        print(f"Zero Euros: €{monthly['zero']:.2f}/mês")
        print(f"Zero + Eletricidade: €{monthly['zero_with_electricity']:.2f}/mês")
        print(f"Poupança: €{monthly['savings']:.2f}/mês ({monthly['savings_percentage']:.1f}%)")
        
        print("\n📅 PROJEÇÃO 12 MESES")
        print(f"Original (1 ano): €{yearly['original_yearly']:.2f}")
        print(f"Zero Euros (1 ano): €{yearly['zero_yearly']:.2f}")
        print(f"Zero + Eletricidade (1 ano): €{yearly['zero_yearly_with_electricity']:.2f}")
        print(f"Poupança Anual: €{yearly['savings_yearly']:.2f}")
        
        print("\n💡 ROI E TRADE-OFFS")
        print(f"Poupança Anual: €{roi['roi_yearly']:.2f}")
        print(f"Custo Setup: {self.hidden_costs['setup_time_weeks']} semanas ({roi['setup_time_cost']} horas)")
        print(f"Manutenção Anual: {roi['maintenance_yearly']} horas")
        print(f"Break-even: {roi['break_even_months']} mês")
        
        print("\n📋 DETALHE POR COMPONENTE")
        for category, data in self.costs.items():
            print(f"\n{category.upper()}:")
            print(f"  Original: €{data['original_monthly']:.2f}/mês")
            print(f"  Zero: €{data['zero_monthly']:.2f}/mês")
            print(f"  Componentes: {', '.join(data['components'])}")
        
        print("\n" + "="*70)
        
        return {
            'monthly': monthly,
            'yearly': yearly,
            'roi': roi
        }

if __name__ == "__main__":
    calculator = CostCalculator()
    report = calculator.generate_report()
```

### **Como Usar a Calculadora**
```bash
# Salvar como cost_calculator.py
# Executar:
python cost_calculator.py

# Resultado esperado:
# 🧮 RELATÓRIO DE CUSTOS - VBQ-UNIFIED ZERO EUROS
# ======================================================================
# 
# 📊 CUSTO MENSAL
# Original:  €355.00/mês
# Zero Euros: €0.00/mês
# Zero + Eletricidade: €7.50/mês
# Poupança: €355.00/mês (100.0%)
# 
# 📅 PROJEÇÃO 12 MESES
# Original (1 ano): €4260.00
# Zero Euros (1 ano): €0.00
# Zero + Eletricidade (1 ano): €90.00
# Poupança Anual: €4260.00
# 
# 💡 ROI E TRADE-OFFS
# Poupança Anual: €4260.00
# Custo Setup: 2 semanas (80 horas)
# Manutenção Anual: 104 horas
# Break-even: 1 mês
```

---

## 📈 GRÁFICO DE PROJEÇÃO 12 MESES

### **Script de Visualização**
```python
"""
Gráfico de Projeção de Custos 12 Meses
Compara custos originais vs zero euros
"""

import matplotlib.pyplot as plt
import numpy as np

def plot_cost_projection():
    """Gera gráfico de projeção de custos"""
    
    # Dados
    months = np.arange(1, 13)
    original_monthly = 355  # média
    zero_monthly = 0
    zero_with_electricity = 7.5
    
    original_cumulative = original_monthly * months
    zero_cumulative = zero_monthly * months
    zero_with_electricity_cumulative = zero_with_electricity * months
    
    # Criar gráfico
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Gráfico 1: Custos Mensais
    ax1.plot(months, [original_monthly]*12, 'r-', label='Original (Cloud)', linewidth=2)
    ax1.plot(months, [zero_monthly]*12, 'g-', label='Zero Euros (Local)', linewidth=2)
    ax1.plot(months, [zero_with_electricity]*12, 'b--', label='Zero + Eletricidade', linewidth=2)
    ax1.set_xlabel('Mês')
    ax1.set_ylabel('Custo (€)')
    ax1.set_title('Custo Mensal por Mês')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Gráfico 2: Custos Acumulados
    ax2.plot(months, original_cumulative, 'r-', label='Original (Cloud)', linewidth=2)
    ax2.plot(months, zero_cumulative, 'g-', label='Zero Euros (Local)', linewidth=2)
    ax2.plot(months, zero_with_electricity_cumulative, 'b--', label='Zero + Eletricidade', linewidth=2)
    ax2.set_xlabel('Mês')
    ax2.set_ylabel('Custo Acumulado (€)')
    ax2.set_title('Custo Acumulado (12 Meses)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('cost_projection_12_months.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("✅ Gráfico salvo como: cost_projection_12_months.png")

if __name__ == "__main__":
    plot_cost_projection()
```

---

## 💰 TABELA COMPLETA DE CUSTOS

### **Infraestrutura**

| Componente | Custo Original | Alternativa Zero | Custo Final | Economia |
|-------------|----------------|------------------|-------------|----------|
| VPS (Hetzner CPX21) | 50-60€/mês | PC local | 0€ | 100% |
| Domínio (Namecheap) | 10-15€/ano | localhost | 0€ | 100% |
| SSL Certificate | 10€/mês | Auto-assinado | 0€ | 100% |
| **TOTAL INFRA** | **70-85€/mês** | **Local** | **0€** | **100%** |

### **Dados e APIs**

| Componente | Custo Original | Alternativa Zero | Custo Final | Economia |
|-------------|----------------|------------------|-------------|----------|
| Pinnacle odds | 50-100€/mês | CLV proxy + APIs grátis | 0€ | 100% |
| Betfair API | 0€ (demo) | Betfair API (demo) | 0€ | 0% |
| NBA API | 0€ (oficial) | nba_api (gratuito) | 0€ | 0% |
| The-Odds-API | 0€ (500 req/day) | Tier gratuito | 0€ | 0% |
| **TOTAL DADOS** | **50-100€/mês** | **Gratuito** | **0€** | **100%** |

### **Database e Cache**

| Componente | Custo Original | Alternativa Zero | Custo Final | Economia |
|-------------|----------------|------------------|-------------|----------|
| PostgreSQL managed | 30-80€/mês | PostgreSQL local | 0€ | 100% |
| Redis managed | 20-50€/mês | Redis local | 0€ | 100% |
| S3 Storage | 5-10€/mês | Disco local | 0€ | 100% |
| **TOTAL DB/CACHE** | **55-140€/mês** | **Local** | **0€** | **100%** |

### **Monitoring e MLOps**

| Componente | Custo Original | Alternativa Zero | Custo Final | Economia |
|-------------|----------------|------------------|-------------|----------|
| MLflow cloud | 50€/mês | MLflow local | 0€ | 100% |
| Grafana Cloud | 20-30€/mês | Grafana local | 0€ | 100% |
| Prometheus cloud | 20-30€/mês | Prometheus local | 0€ | 100% |
| **TOTAL MONITORING** | **90-110€/mês** | **Local** | **0€** | **100%** |

### **Comunicação**

| Componente | Custo Original | Alternativa Zero | Custo Final | Economia |
|-------------|----------------|------------------|-------------|----------|
| Email (SendGrid) | 0€ (1000/mês) | Telegram bot | 0€ | 0% |
| SMS (Twilio) | 0.05€/msg | Telegram bot | 0€ | 100% |
| **TOTAL COMMS** | **Variável** | **Telegram** | **0€** | **100%** |

---

## 📊 CUSTO TOTAL ZERO EUROS

### **Resumo Final**
```
INFRAESTRUTURA:     70-85€/mês → 0€ (100% economia)
DADOS E APIs:       50-100€/mês → 0€ (100% economia)
DATABASE/CACHE:     55-140€/mês → 0€ (100% economia)
MONITORING/MLOPS:   90-110€/mês → 0€ (100% economia)
COMUNICAÇÃO:        Variável → 0€ (100% economia)

TOTAL ORIGINAL:     265-435€/mês
TOTAL ZERO EUROS:   0€
ECONOMIA:           100%
```

---

## 🔄 ALTERNATIVAS GRATUITAS DETALHADAS

### **1. Dados de Odds**

#### **Pinnacle Closing Odds → CLV Proxy**
```python
# PROBLEMA: Pinnacle odds de fecho são pagos (50-100€/mês)
# SOLUÇÃO: Usar odds de abertura como proxy

# Alternativas gratuitas:
1. The-Odds-API.com (500 req/day grátis)
2. Betfair API (demo gratuita)
3. Sportsbookreview scraper (10 anos dados históricos)
4. Scraping manual (legal grey area)

# Precisão esperada:
# CLV real: 85-90% precisão
# CLV proxy: 60-70% precisão
# Trade-off: Aceitável para MVP/learning
```

#### **GitHub Datasets**
```python
# Repositórios gratuitos com dados históricos:
1. flancast90/sportsbookreview-scraper
   - 10 anos de odds NBA/NFL/MLB/NHL
   - Atualizado Jul 2024
   - 100% gratuito

2. nealmick/Sports-Betting-ML-Tools-NBA
   - Dados NBA para ML
   - Features pré-computadas
   - 100% gratuito
```

### **2. Dados NBA**

#### **NBA API Oficial**
```python
# 100% gratuito e ilimitado:
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder

# Sem rate limits significativos
# Dados oficiais da NBA
# Atualização em tempo real
```

#### **Basketball-Reference Scraping**
```python
# 100% gratuito via scraping:
import basketball_reference_web_scraper as br

# Estatísticas históricas completas
- Player stats
- Team stats
- Advanced metrics
- Play-by-play data
```

### **3. Infraestrutura Local**

#### **PostgreSQL Local vs Managed**
```bash
# Managed (RDS, etc.): 30-80€/mês
# Local: 0€

# Vantagens local:
- 0€ custo
- Full controle
- Sem latência rede
- Backup local (grátis)

# Desvantagens local:
- Sem HA automático
- Backup manual
- Escalabilidade limitada
```

#### **Redis Local vs Managed**
```bash
# Managed (ElastiCache): 20-50€/mês
# Local: 0€

# Mesmas vantagens/desvantagens PostgreSQL
```

### **4. Monitoring Local**

#### **Grafana/Prometheus Local**
```bash
# Cloud: 20-30€/mês
# Local: 0€

# Stack completa local:
- Prometheus (métricas)
- Grafana (dashboards)
- AlertManager (alertas)
- Node Exporter (sistema)

# 100% funcional para MVP
```

---

## ✅ VALIDAÇÃO DE CUSTOS ZERO

### **Checklist de Verificação**

#### **Componentes de Infraestrutura**
- [x] VPS → PC local (0€)
- [x] Domínio → localhost (0€)
- [x] SSL → auto-assinado (0€)
- [x] Backup → disco local (0€)

#### **Componentes de Dados**
- [x] Pinnacle odds → CLV proxy (0€)
- [x] NBA API → nba_api (0€)
- [x] Basketball-Reference → scraping (0€)
- [x] The-Odds-API → tier gratuito (0€)

#### **Componentes de Software**
- [x] PostgreSQL → local (0€)
- [x] Redis → local (0€)
- [x] MLflow → local (0€)
- [x] Grafana → local (0€)
- [x] Prometheus → local (0€)

#### **Componentes de Comunicação**
- [x] Email → Telegram bot (0€)
- [x] SMS → Telegram bot (0€)
- [x] Notificações → Telegram bot (0€)

---

## 🎯 CUSTOS OCULTOS A CONSIDERAR

### **Custos Não Monetários**
```
Tempo setup: 2 semanas dedicadas
Manutenção: 2h/semana
Eletricidade PC: ~5-10€/mês (se 24/7)
Risco hardware: PC pode falhar
```

### **Custos de Oportunidade**
```
Sem VPS: Não escalável
Sem backup externo: Risco perda dados
Sem SLA: Sem garantias uptime
Sem monitoring cloud: Menos visibilidade
```

---

## 📊 COMPARAÇÃO ROI

### **Cenário Original (Cloud)**
```
Custo mensal: 265-435€
Setup: 1 semana
Escalável: Sim
HA: Sim
Backup: Automático
SLA: 99.9%
```

### **Cenário Zero Euros (Local)**
```
Custo mensal: 0€ (5-10€ eletricidade)
Setup: 2 semanas
Escalável: Não (máximo 10 utilizadores)
HA: Não
Backup: Manual
SLA: Nenhum
```

### **Recomendação**
```
Para MVP/Learning: Zero euros (local)
Para produção: VPS (cloud)
Para escala: VPS + managed services
```

---

## 🚀 CONCLUSÃO

### **Verificação Final**
```
✅ Todos os componentes têm alternativa gratuita
✅ Custo total: 0€ (exceto eletricidade)
✅ Trade-offs aceitáveis para MVP
✅ Escalável para VPS mais tarde
```

### **Próximos Passos**
1. **Validar setup:** [[00_SETUP_ZERO/VALIDACAO]]
2. **Configurar dados:** [[04_Data_Engineering/FONTES_GRATUITAS]]
3. **Começar desenvolvimento:** Seguir roadmap

---

**Status:** Custos verificados = 0€  
**Economia:** 100% vs original  
**Viabilidade:** Confirmada para MVP  

---

#status/active #priority/critical #phase/setup-zero
