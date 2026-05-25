# LOG_ALTERACOES_INDEX — Log de Alterações ao Index

**ID:** `DOC-001` | **Fase:** #phase/1 | **Owner:** Project Manager | **Status:** #status/active

---

## 1. OBJETIVO

Registar todas as alterações ao index da documentação.

---

## 2. FORMATO

```markdown
## [YYYY-MM-DD] - Descrição

- Alteração 1
- Alteração 2
- ...

Responsável: @username
```

---

## 3. EXEMPLO

```markdown
## 2024-01-15 - Adicionada documentação de CLV

- Adicionado CLV_POR_REGIME.md
- Adicionado CLV_POR_MERCADO.md
- Atualizado INDEX.md com links

Responsável: @quant
```

---

## 4. AUTOMAÇÃO

```python
def log_index_change(description, changes, author):
    """
    Registra alteração ao index.
    
    Args:
        description: Descrição da alteração
        changes: Lista de alterações
        author: Autor da alteração
    """
    entry = f"""
## {datetime.now().strftime('%Y-%m-%d')} - {description}

"""
    
    for change in changes:
        entry += f"- {change}\n"
    
    entry += f"\nResponsável: @{author}\n"
    
    # Adicionar ao log
    with open('LOG_ALTERACOES_INDEX.md', 'a') as f:
        f.write(entry)
```

---

## 5. CRITÉRIOS

- **Registrar todas** as alterações ao index
- **Incluir descrição** e autor
- **Manter cronológico** (mais recente no topo)

---

## 6. LINKS CRUZADOS

- [[00_Master_Index/INDEX]]
