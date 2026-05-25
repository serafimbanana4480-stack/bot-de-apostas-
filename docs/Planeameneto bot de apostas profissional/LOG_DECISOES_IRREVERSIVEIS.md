# LOG_DECISOES_IRREVERSIVEIS — Log de Decisões Irreversíveis

**ID:** `DOC-002` | **Fase:** #phase/1 | **Owner:** Project Manager | **Status:** #status/active

---

## 1. OBJETIVO

Registar todas as decisões irreversíveis do projeto.

---

## 2. FORMATO

```markdown
## [YYYY-MM-DD] - Título da Decisão

**Contexto:** Descrição do contexto
**Decisão:** Decisão tomada
**Justificativa:** Porquê esta decisão
**Impacto:** Impacto esperado
**Responsável:** @username
```

---

## 3. EXEMPLO

```markdown
## 2024-01-10 - Escolha de NBA como desporto inicial

**Contexto:** Múltiplos desportos disponíveis (NBA, NFL, MLB, Soccer)
**Decisão:** Focar inicialmente em NBA
**Justificativa:** Maior liquidez, dados excelentes, complexidade média
**Impacto:** Sistema inicial focado em NBA, expansão futura para outros desportos
**Responsável:** @quant
```

---

## 4. AUTOMAÇÃO

```python
def log_irreversible_decision(title, context, decision, rationale, impact, author):
    """
    Registra decisão irreversível.
    
    Args:
        title: Título da decisão
        context: Contexto
        decision: Decisão tomada
        rationale: Justificativa
        impact: Impacto esperado
        author: Autor
    """
    entry = f"""
## {datetime.now().strftime('%Y-%m-%d')} - {title}

**Contexto:** {context}
**Decisão:** {decision}
**Justificativa:** {rationale}
**Impacto:** {impact}
**Responsável:** @{author}
"""
    
    # Adicionar ao log
    with open('LOG_DECISOES_IRREVERSIVEIS.md', 'a') as f:
        f.write(entry)
```

---

## 5. CRITÉRIOS

- **Registrar todas** as decisões irreversíveis
- **Incluir justificativa** detalhada
- **Aprovação** necessária para decisões críticas

---

## 6. LINKS CRUZADOS

- [[01_Vision_And_Strategy/DECISOES_IRREVERSIVEIS]]
