---
ID: OPS-004
tags: #status/active #operations #documentation #knowledge #wiki
---

# Documentação Operacional

## Objetivo
Criar e manter um repositório vivo, completo e estruturado de toda a informação operacional necessária para que a equipa de operações (e futuros membros) consiga executar, monitorizar, resolver problemas e melhorar o sistema de value betting NBA sem depender de conhecimento tribal ou de indivíduos específicos. A documentação operacional é a memória institucional formal do sistema.

## O que faz
- Estrutura a informação em cinco camadas: (1) Visão Geral do Sistema, (2) Runbooks (procedimentos de resolução), (3) SOPs (procedimentos rotineiros), (4) Referência Técnica (arquitetura, APIs, configurações), (5) Decisões e ADRs (Architecture Decision Records).
- Define um processo de revisão e atualização: cada documento tem um owner, uma data de última revisão, uma data de próxima revisão obrigatória, e um indicador de frescura ( freshness score).
- Implementa mecanismo de busca e descoberta: tags, backlinks, índices por categoria, e glossário de termos operacionais.
- Garante redundância: a documentação primária está no vault Obsidian, mas cópias exportadas existem em PDF (arquivo offline) e em Notion (acesso web para equipa não técnica).

## Porque existe
- **Bus Factor**: Se o único operador que sabe como restaurar o PostgreSQL ou como recalibrar o modelo deixa a equipa, o sistema fica em risco operacional grave.
- **Onboarding Eficiente**: Um novo operador deve ser autossuficiente em 80% das tarefas em 2 semanas, com a documentação como principal tutor.
- **Auditoria e Compliance**: Autoridades reguladoras e auditorias externas exigem evidência de processos documentados. A ausência de documentação é considerada falha de governance.
- **Consistência**: Quando 3 operadores executam a mesma tarefa de 3 formas diferentes, o resultado é imprevisível. A documentação padroniza.

## Implementação / Pseudocódigo
```python
class DocumentacaoOperacional:
    def __init__(self):
        self.categorias = {
            "VISAO_GERAL": {"descricao": "Arquitetura do sistema, diagramas, fluxos de dados", "revisao_meses": 6, "owner_default": "arquiteto_sistemas"},
            "RUNBOOK": {"descricao": "Procedimentos de resposta a incidentes e falhas", "revisao_meses": 3, "owner_default": "gestor_operacoes"},
            "SOP": {"descricao": "Procedimentos operacionais padrão (rotinas, manutenção)", "revisao_meses": 3, "owner_default": "gestor_operacoes"},
            "REFERENCIA_TECNICA": {"descricao": "APIs, schemas, configurações, parametrizações", "revisao_meses": 6, "owner_default": "engenheiro_sistemas"},
            "DECISAO_ADR": {"descricao": "Registo de decisões arquiteturais e operacionais", "revisao_meses": 12, "owner_default": "arquiteto_sistemas"},
            "POSTMORTEM": {"descricao": "Análises de incidentes graves", "revisao_meses": None, "owner_default": "gestor_operacoes"}
        }
        self.padrao_nomeacao = "{categoria}/{id}_{nome_descritivo}.md"
        self.formato_obrigatorio = ["ID", "tags", "objetivo", "o_que_faz", "porque_existe", "implementacao", "thresholds", "riscos", "checklist", "links_cruzados"]

    def avaliar_frescura_documento(self, doc_path):
        doc = self.carregar_documento(doc_path)
        ultima_revisao = datetime.fromisoformat(doc["metadata"]["ultima_revisao"])
        categoria = doc["metadata"]["categoria"]
        prazo_revisao_meses = self.categorias[categoria]["revisao_meses"]
        
        if prazo_revisao_meses is None:
            return {"freshness": "N/A", "status": "DOCUMENTO_UNICO"}
        
        idade_meses = (datetime.utcnow() - ultima_revisao).days / 30
        freshness = max(0, 1 - (idade_meses / prazo_revisao_meses))
        
        status = "ATUALIZADO" if freshness >= 0.8 else "NECESSITA_REVISAO" if freshness >= 0.5 else "DESATUALIZADO"
        return {"freshness": freshness, "status": status, "proxima_revisao": (ultima_revisao + timedelta(days=prazo_revisao_meses*30)).isoformat()}

    def gerar_relatorio_frescura(self):
        todos_docs = self.listar_todos_documentos()
        relatorio = {"atualizados": 0, "necessita_revisao": 0, "desatualizados": 0, "docs": []}
        
        for doc in todos_docs:
            avaliacao = self.avaliar_frescura_documento(doc)
            relatorio["docs"].append({"path": doc, **avaliacao})
            relatorio[avaliacao["status"].lower()] += 1
        
        return relatorio

    def criar_documento(self, categoria, titulo, conteudo, autor):
        doc_id = self.gerar_id_unico(categoria)
        nome_ficheiro = self.padrao_nomeacao.format(categoria=categoria, id=doc_id, nome_descritivo=slugify(titulo))
        metadata = {
            "id": doc_id,
            "tags": f"#status/active #{categoria.lower()}",
            "autor": autor,
            "data_criacao": datetime.utcnow().isoformat(),
            "ultima_revisao": datetime.utcnow().isoformat(),
            "proxima_revisao": (datetime.utcnow() + timedelta(days=self.categorias[categoria]["revisao_meses"]*30)).isoformat() if self.categorias[categoria]["revisao_meses"] else None,
            "owner": self.categorias[categoria]["owner_default"],
            "categoria": categoria
        }
        
        documento_completo = self.renderizar_template(metadata, conteudo)
        self.gravar_documento(nome_ficheiro, documento_completo)
        self.atualizar_indice(categoria, nome_ficheiro, metadata)
        return {"path": nome_ficheiro, "id": doc_id}

    def exportar_para_notion(self, doc_path):
        doc = self.carregar_documento(doc_path)
        self.notion_client.criar_pagina(
            parent_id=self.notion_database_id,
            titulo=doc["titulo"],
            conteudo=doc["conteudo"],
            propriedades={
                "ID": doc["metadata"]["id"],
                "Categoria": doc["metadata"]["categoria"],
                "Owner": doc["metadata"]["owner"],
                "Status": "Publicado",
                "Última Revisão": doc["metadata"]["ultima_revisao"]
            }
        )

    def exportar_para_pdf(self, doc_path):
        doc = self.carregar_documento(doc_path)
        pdf = self.renderizar_pdf(doc)
        self.s3.upload(f"documentacao/pdf/{doc['metadata']['id']}.pdf", pdf)
```

## Thresholds e Tabelas

| Categoria | Revisão Obrigatória | Owner Típico | Formato | Local Principal | Backup |
|-----------|--------------------|-------------|---------|-----------------|--------|
| Visão Geral | 6 meses | Arquiteto | Markdown + Diagramas | Obsidian | Notion + PDF |
| Runbook | 3 meses | Gestor Ops | Markdown | Obsidian | Notion + PDF |
| SOP | 3 meses | Gestor Ops | Markdown | Obsidian | Notion + PDF |
| Ref. Técnica | 6 meses | Engenheiro | Markdown + Código | Obsidian | GitHub Wiki |
| ADR | 12 meses | Arquiteto | Markdown | Obsidian | Notion |
| Postmortem | N/A (único) | Gestor Ops | Markdown | Obsidian | Notion + PDF |

| Métrica de Frescura | Threshold Ação | Ação |
|--------------------|---------------|------|
| Freshness < 50% (Desatualizado) | Qualquer documento | Bloquear para alterações dependentes; agendar revisão em 7 dias |
| 50% <= Freshness < 80% (Necessita Revisão) | Qualquer documento | Notificar owner; agendar revisão em 14 dias |
| >= 80% (Atualizado) | — | Nenhuma ação; manter monitorização |
| Documentos sem revisão > 12 meses | Qualquer categoria | Alerta P3 para gestor de operações |

## Riscos
- **Risco de Documentação Obsoleta**: Uma runbook que descreve o processo de rollback do modelo mas o processo mudou há 6 meses é perigoso — gera confiança falsa e ações erradas em incidente.
- **Risco de Documentação Excessiva**: Documentar tudo indiscriminamente cria "documentação morta" que ninguém lê. Deve haver critério de relevância.
- **Risco de Acesso**: Documentação sensível (ex: credenciais de emergência, configurações de firewall) armazenada em Notion ou Obsidian sem controlo de acesso é vulnerável.
- **Risco de Formatos Incompatíveis**: Markdown em Obsidian não é facilmente consumível por stakeholders não-técnicos. A dualidade Obsidian + Notion resolve, mas exige sincronização.

## Checklist de Documentação Operacional
- [ ] Todos os SOPs (pastas 25-26) têm formato padronizado, ID único, e owner designado.
- [ ] Índice de cada pasta (INDEX.md) atualizado com links para todos os documentos ativos.
- [ ] Relatório semanal de frescura: % de documentos atualizados > 90%; 0 documentos desatualizados com > 12 meses.
- [ ] Exportação mensal para Notion e PDF verificada; links funcionais.
- [ ] Glossário de termos operacionais (ex: "CLV", "Stake", "Circuit Breaker", "Drift") mantido e referenciado.
- [ ] Novos operadores durante onboarding usam a documentação como recurso primário; feedback coletado para melhoria.
- [ ] Decisões operacionais materiais (thresholds alterados, ferramentas adotadas) convertidas em ADR em 48h.
- [ ] Backup mensal do vault Obsidian completo para storage imutável (S3 Glacier), com retenção de 5 anos.

## Links Cruzados
- [[18_Operations/ROTINA_DIARIA]] - Rotina que inclui tarefas de documentação.
- [[18_Operations/COMUNICACAO_EQIPA]] - Comunicação que alimenta e consome a documentação.
- [[25_SOPs/SOP-001_Rotina_Diaria_Abertura]] até [[25_SOPs/SOP-010_Rotacao_Secrets]] - Procedimentos documentados.
- [[26_Runbooks/RB-001_Feed_Dados_Offline]] até [[26_Runbooks/RB-010_Erro_Deploy_Modelo]] - Runbooks documentados.
