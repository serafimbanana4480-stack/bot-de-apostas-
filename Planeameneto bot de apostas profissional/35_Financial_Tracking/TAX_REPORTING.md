---
ID: FT-004
tags: #status/active #financial #tax #compliance #portugal #irs
---

# Relatórios Fiscais e Compliance

## Objetivo
Documentar o processo completo de cálculo, declaração e pagamento de impostos relacionados com atividades de apostas em Portugal, incluindo IRS (Imposto sobre o Rendimento Singular), retenções na fonte, e compliance com a Autoridade Tributária. O sistema deve garantir precisão fiscal, manter registos auditáveis por 5 anos, e automatizar o máximo possível do processo.

## O que faz
- Calcula o rendimento tributável de apostas: lucros líquidos após dedução de perdas e custos.
- Implementa retenções na fonte para subscritores (se aplicável) e para a empresa.
- Gera relatórios fiscais trimestrais e anuais no formato exigido pela Autoridade Tributária.
- Mantém registos detalhados de todas as transações para auditoria.
- Define processo de declaração de IRS: categorias de rendimento, prazos, e formulários.
- Estabelece provisões fiscais mensais para evitar surpresas no pagamento de impostos.

## Porque existe
- **Obrigação Legal**: Em Portugal, os lucros de apostas são tributáveis. Não declarar pode resultar em multas severas e processos criminais.
- **Precisão**: Erros no cálculo de impostos podem levar a pagamentos excessivos (dinheiro perdido) ou insuficientes (multas e juros).
- **Previsibilidade**: Provisões fiscais mensais permitem planeamento de fluxo de caixa e evitam problemas de liquidez.
- **Auditabilidade**: Em caso de auditoria fiscal, registos detalhados e organizados são essenciais para demonstrar conformidade.

---

## Enquadramento Fiscal em Portugal

### Classificação de Rendimentos

**Atividade Principal (Venda de Sinais):**
- **Categoria B**: Rendimentos Empresariais e Profissionais
- Taxa: 20% sobre o lucro tributável (se englobado) ou taxa fixa de 20% com opção de englobamento
- IVA: Isento se faturação anual < 12.500€ (regime simplificado)

**Atividade Secundária (Apostas Próprias):**
- **Categoria G**: Incrementos Patrimoniais (ganhos de jogo)
- Taxa: 10% sobre lucros (retido na fonte pelo bookmaker)
- Nota: Perdas não são dedutíveis em Categoria G

**Receitas de Subscrições:**
- **Categoria B**: Rendimentos Empresariais
- IVA: 23% se faturação anual > 12.500€ (regime normal)
- Retenção na fonte: 20% (pode ser deduzido no pagamento final)

### Tabela de Impostos

| Tipo de Rendimento | Categoria | Taxa | Retenção na Fonte | Dedutível |
|-------------------|-----------|------|-------------------|-----------|
| Venda de sinais | B | 20% | 20% | Sim |
| Receitas de subscrições | B | 20% | 20% | Sim |
| Lucros de apostas (Betfair) | G | 10% | 10% (pelo bookmaker) | Não |
| Lucros de apostas (outros) | G | 10% | 10% (pelo bookmaker) | Não |
| Juros de contas bancárias | E | 28% | 28% | Sim (englobamento opcional) |

---

## Cálculo de Impostos

### Cálculo de IRS Categoria B (Venda de Sinais)
```python
class TaxCalculatorCategoryB:
    """
    Calcula IRS para rendimentos empresariais (Categoria B).
    """
    def __init__(self, config):
        self.config = config

    def calculate_taxable_income(self, year):
        """
        Calcula rendimento coletável.
        """
        # 1. Receitas
        revenues = {
            "subscription_revenue": self._get_subscription_revenue(year),
            "signal_sales": self._get_signal_sales_revenue(year),
            "other_revenue": self._get_other_revenue(year)
        }
        total_revenue = sum(revenues.values())

        # 2. Custos dedutíveis
        expenses = {
            "vps_costs": self._get_vps_costs(year),
            "data_costs": self._get_data_costs(year),
            "software_costs": self._get_software_costs(year),
            "marketing_costs": self._get_marketing_costs(year),
            "payment_fees": self._get_payment_fees(year),
            "other_expenses": self._get_other_expenses(year)
        }
        total_expenses = sum(expenses.values())

        # 3. Rendimento líquido
        net_income = total_revenue - total_expenses

        # 4. Aplicar coeficiente do regime simplificado (se aplicável)
        # Regime simplificado: 15% do rendimento bruto é considerado como custo
        if self._is_simplified_regime(year):
            simplified_deduction = total_revenue * 0.15
            taxable_income = max(0, total_revenue - simplified_deduction)
        else:
            # Regime de contabilidade organizada: custos reais
            taxable_income = max(0, net_income)

        return {
            "revenues": revenues,
            "expenses": expenses,
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_income": net_income,
            "taxable_income": taxable_income,
            "regime": "simplified" if self._is_simplified_regime(year) else "organized"
        }

    def calculate_irs(self, taxable_income):
        """
        Calcula IRS devido.
        """
        # Taxa de 20% para Categoria B (englobamento opcional)
        tax_rate = 0.20
        irs = taxable_income * tax_rate

        # Deduzir retenções na fonte já pagas
        withholding_paid = self._get_withholding_paid()
        irs_due = max(0, irs - withholding_paid)

        return {
            "tax_rate": tax_rate,
            "gross_irs": round(irs, 2),
            "withholding_paid": round(withholding_paid, 2),
            "irs_due": round(irs_due, 2)
        }

    def calculate_iva(self, year):
        """
        Calcula IVA (se aplicável).
        """
        revenue = self._get_subscription_revenue(year)

        # Isento se faturação anual < 12.500€
        if revenue < 12500:
            return {
                "iva_due": 0,
                "regime": "isento"
            }

        # IVA a 23%
        iva_rate = 0.23
        iva_due = revenue * iva_rate

        # Deduzir IVA suportado (custos)
        iva_deductible = self._get_iva_deductible(year)
        iva_net = max(0, iva_due - iva_deductible)

        return {
            "iva_rate": iva_rate,
            "iva_due": round(iva_due, 2),
            "iva_deductible": round(iva_deductible, 2),
            "iva_net": round(iva_net, 2),
            "regime": "normal"
        }
```

### Cálculo de IRS Categoria G (Lucros de Apostas)
```python
class TaxCalculatorCategoryG:
    """
    Calcula IRS para ganhos de jogo (Categoria G).
    """
    def __init__(self, config):
        self.config = config

    def calculate_taxable_income(self, year):
        """
        Calcula rendimento tributável de apostas.

        Nota: Perdas NÃO são dedutíveis em Categoria G.
        """
        # Obter todos os lucros de apostas
        winnings = self._get_winnings(year)
        losses = self._get_losses(year)

        # Apenas lucros são tributáveis
        taxable_income = max(0, winnings - losses)

        return {
            "winnings": winnings,
            "losses": losses,
            "taxable_income": taxable_income
        }

    def calculate_irs(self, taxable_income):
        """
        Calcula IRS para Categoria G.

        Taxa: 10% (retido na fonte pelo bookmaker)
        """
        tax_rate = 0.10
        irs = taxable_income * tax_rate

        # Verificar se retenção foi feita na fonte
        withholding_paid = self._get_bookmaker_withholding()

        # Normalmente, o bookmaker já retém, então IRS devido é 0
        irs_due = max(0, irs - withholding_paid)

        return {
            "tax_rate": tax_rate,
            "gross_irs": round(irs, 2),
            "withholding_paid": round(withholding_paid, 2),
            "irs_due": round(irs_due, 2)
        }
```

---

## Provisões Fiscais

### Cálculo Mensal de Provisões
```python
class TaxProvisioning:
    """
    Calcula provisões fiscais mensais para planeamento de caixa.
    """
    def __init__(self, config):
        self.config = config

    def calculate_monthly_provision(self, year, month):
        """
        Calcula provisão para um mês específico.
        """
        # 1. Receitas do mês
        revenue = self._get_monthly_revenue(year, month)

        # 2. Custos do mês
        expenses = self._get_monthly_expenses(year, month)

        # 3. Lucro estimado
        estimated_profit = revenue - expenses

        # 4. Provisão IRS (20% do lucro estimado)
        irs_provision = max(0, estimated_profit * 0.20)

        # 5. Provisão IVA (23% das receitas de subscrição)
        subscription_revenue = self._get_monthly_subscription_revenue(year, month)
        if subscription_revenue > 1041:  # 12.500€ / 12 meses
            iva_provision = subscription_revenue * 0.23
        else:
            iva_provision = 0

        # 6. Provisão Segurança Social (se aplicável)
        # Categoria B: 21.4% sobre 70% do rendimento (se > 12x IAS)
        # IAS 2024 = 509,26€
        ias = 509.26
        if estimated_profit > (ias * 12):
            ss_provision = estimated_profit * 0.70 * 0.214
        else:
            ss_provision = 0

        total_provision = irs_provision + iva_provision + ss_provision

        return {
            "month": month,
            "year": year,
            "revenue": revenue,
            "expenses": expenses,
            "estimated_profit": estimated_profit,
            "irs_provision": round(irs_provision, 2),
            "iva_provision": round(iva_provision, 2),
            "ss_provision": round(ss_provision, 2),
            "total_provision": round(total_provision, 2)
        }
```

---

## Relatórios Fiscais

### Relatório Trimestral
```python
class QuarterlyTaxReport:
    """
    Gera relatório fiscal trimestral.
    """
    def generate_quarterly_report(self, year, quarter):
        """
        Gera relatório para um trimestre.
        """
        months = self._get_quarter_months(quarter)

        total_revenue = 0
        total_expenses = 0
        total_irs_withheld = 0

        for month in months:
            total_revenue += self._get_monthly_revenue(year, month)
            total_expenses += self._get_monthly_expenses(year, month)
            total_irs_withheld += self._get_monthly_withholding(year, month)

        taxable_income = max(0, total_revenue - total_expenses)
        irs_due = max(0, taxable_income * 0.20 - total_irs_withheld)

        return {
            "year": year,
            "quarter": quarter,
            "months": months,
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "taxable_income": round(taxable_income, 2),
            "irs_withheld": round(total_irs_withheld, 2),
            "irs_due": round(irs_due, 2)
        }
```

### Relatório Anual (Declaração IRS)
```python
class AnnualTaxReport:
    """
    Gera relatório fiscal anual para declaração de IRS.
    """
    def generate_annual_report(self, year):
        """
        Gera relatório completo para o ano fiscal.
        """
        # 1. Rendimentos Categoria B
        cat_b = TaxCalculatorCategoryB(self.config).calculate_taxable_income(year)
        cat_b_irs = TaxCalculatorCategoryB(self.config).calculate_irs(cat_b["taxable_income"])

        # 2. Rendimentos Categoria G
        cat_g = TaxCalculatorCategoryG(self.config).calculate_taxable_income(year)
        cat_g_irs = TaxCalculatorCategoryG(self.config).calculate_irs(cat_g["taxable_income"])

        # 3. IVA
        iva = TaxCalculatorCategoryB(self.config).calculate_iva(year)

        # 4. Segurança Social
        ss = self._calculate_social_security(year)

        # 5. Resumo
        total_tax = cat_b_irs["irs_due"] + cat_g_irs["irs_due"] + iva["iva_net"] + ss["ss_due"]

        return {
            "year": year,
            "category_b": {
                "taxable_income": cat_b["taxable_income"],
                "irs_due": cat_b_irs["irs_due"]
            },
            "category_g": {
                "taxable_income": cat_g["taxable_income"],
                "irs_due": cat_g_irs["irs_due"]
            },
            "iva": {
                "iva_net": iva["iva_net"],
                "regime": iva["regime"]
            },
            "social_security": {
                "ss_due": ss["ss_due"]
            },
            "total_tax_due": round(total_tax, 2)
        }
```

---

## Prazos de Declaração

### Calendário Fiscal

| Evento | Prazo | Formulário | Notas |
|--------|-------|------------|-------|
| Pagamento por conta (1ª) | Março | N/A | 25% do imposto do ano anterior |
| Pagamento por conta (2ª) | Junho | N/A | 25% do imposto do ano anterior |
| Pagamento por conta (3ª) | Setembro | N/A | 25% do imposto do ano anterior |
| Declaração IRS | 1 Abril - 30 Junho | Modelo 3 | Inclui anexo B e/ou G |
| IVA (trimestral) | Até dia 15 do mês seguinte | Declaração periódica | Se regime normal |
| Segurança Social | Até dia 20 do mês seguinte | RNFF | Se > 12x IAS |
| Liquidação final IRS | Agosto-Setembro | N/A | Autoliquidação após declaração |

---

## Registo e Armazenamento

### Requisitos de Armazenamento
```python
class TaxRecordStorage:
    """
    Gerencia armazenamento de registos fiscais.
    """
    def __init__(self, storage_config):
        self.storage_config = storage_config

    def store_tax_record(self, record_type, year, data):
        """
        Armazena registo fiscal.

        Requisitos:
        - Manter por 5 anos (lei fiscal portuguesa)
        - Formato não modificável (PDF assinado ou blockchain)
        - Backup redundante
        """
        # 1. Gerar hash do registo para integridade
        record_hash = self._generate_hash(data)

        # 2. Criar ficheiro
        filename = f"{record_type}_{year}_{datetime.utcnow().strftime('%Y%m%d')}.json"
        filepath = f"{self.storage_config['tax_records_path']}/{filename}"

        with open(filepath, 'w') as f:
            json.dump({
                "data": data,
                "hash": record_hash,
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            }, f, indent=2)

        # 3. Armazenar backup em cloud
        self._upload_to_cloud(filepath)

        # 4. Registrar na base de dados
        self._db.insert("tax_records", {
            "type": record_type,
            "year": year,
            "filepath": filepath,
            "hash": record_hash,
            "created_at": datetime.utcnow()
        })

    def verify_record_integrity(self, record_id):
        """
        Verifica integridade de um registo fiscal.
        """
        record = self._db.get_tax_record(record_id)

        with open(record["filepath"], 'r') as f:
            stored_data = json.load(f)

        current_hash = self._generate_hash(stored_data["data"])

        if current_hash != stored_data["hash"]:
            raise IntegrityError("Registo fiscal foi modificado!")

        return True
```

---

## Compliance e Auditoria

### Checklist de Compliance
```python
class ComplianceChecker:
    """
    Verifica compliance fiscal.
    """
    def check_annual_compliance(self, year):
        """
        Verifica compliance para um ano fiscal.
        """
        checks = []

        # 1. Verificar se todas as transações foram registadas
        missing_transactions = self._check_missing_transactions(year)
        if missing_transactions:
            checks.append({
                "check": "MISSING_TRANSACTIONS",
                "status": "FAIL",
                "details": f"{len(missing_transactions)} transações não registadas"
            })
        else:
            checks.append({
                "check": "MISSING_TRANSACTIONS",
                "status": "PASS"
            })

        # 2. Verificar se provisões foram calculadas
        provisions = self._check_provisions(year)
        if not provisions:
            checks.append({
                "check": "PROVISIONS_CALCULATED",
                "status": "FAIL",
                "details": "Provisões não foram calculadas"
            })
        else:
            checks.append({
                "check": "PROVISIONS_CALCULATED",
                "status": "PASS"
            })

        # 3. Verificar se declaração foi submetida
        declaration = self._check_declaration_submitted(year)
        if not declaration:
            checks.append({
                "check": "DECLARATION_SUBMITTED",
                "status": "FAIL",
                "details": "Declaração IRS não foi submetida"
            })
        else:
            checks.append({
                "check": "DECLARATION_SUBMITTED",
                "status": "PASS"
            })

        # 4. Verificar integridade dos registos
        integrity = self._check_record_integrity(year)
        if not integrity:
            checks.append({
                "check": "RECORD_INTEGRITY",
                "status": "FAIL",
                "details": "Alguns registos foram modificados"
            })
        else:
            checks.append({
                "check": "RECORD_INTEGRITY",
                "status": "PASS"
            })

        return checks
```

---

## Thresholds e Tabelas

| Limite Fiscal | Valor | Categoria | Ação |
|---------------|-------|-----------|------|
| Isenção IVA | < 12.500€/ano | B | Regime simplificado |
| Isenção Segurança Social | < 12x IAS/ano | B | Não paga SS |
| Taxa IRS Categoria B | 20% | B | Englobamento opcional |
| Taxa IRS Categoria G | 10% | G | Retido na fonte |
| Taxa IVA | 23% | B | Regime normal |
| Taxa Segurança Social | 21.4% | B | Sobre 70% do rendimento |

| Período de Retenção | Tipo de Documento | Localização |
|----------------------|-------------------|-------------|
| 5 anos | Faturas e recibos | Cloud + local |
| 5 anos | Extratos bancários | Cloud + local |
| 5 anos | Declarações fiscais | Cloud + local |
| 5 anos | Registos de apostas | Cloud + local |
| 10 anos | Contratos | Cloud + local |

---

## Links Cruzados

- [[PNL_TRACKING]] → Dados para cálculo fiscal
- [[BANKROLL_MANAGEMENT]] → Movimentos de capital
- [[FINANCIAL_REPORTS]] → Relatórios financeiros
- [[02_Business_Model/PLANO_FINANCEIRO_6_MESES]] → Projeções de receitas