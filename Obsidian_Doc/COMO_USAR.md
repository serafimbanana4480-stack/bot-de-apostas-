# 📖 Como Usar Esta Documentação no Obsidian

Guia rápido para configurar e usar a documentação do VBQ-UNIFIED no Obsidian.

---

## 🚀 Configuração Inicial

### 1. Instalar o Obsidian

**Download:** https://obsidian.md/

**Plataformas suportadas:**
- Windows
- macOS
- Linux
- iOS (iPhone/iPad)
- Android

### 2. Abrir o Vault

1. Abra o Obsidian
2. Clique em "Open folder as vault"
3. Navegue até: `c:/Users/rodri/Desktop/bot de apostas/Obsidian_Doc`
4. Clique em "Open"

### 3. Configurar Preferências (Opcional)

**Configurações recomendadas:**

```
Settings → Editor
☑ Spell check
☑ Show line number
☑ Line wrap
☑ Vim key mode (opcional)

Settings → Files & Links
☑ Use [[Wikilinks]]
☑ Detect all
☑ Update internal links on file rename

Settings → Appearance
Base theme: Dark
Accent color: Purple
```

---

## 🧭 Navegação

### Wikilinks

Esta documentação usa wikilinks para navegação:

- **Formato:** `[[Nome do Arquivo]]`
- **Exemplo:** `[[README]]`
- **Como usar:** Clique em qualquer wikilink para navegar

### Grafo de Conhecimento

**Ver relações entre documentos:**
1. Clique no ícone de grafo no painel esquerdo
2. Explore conexões entre documentos
3. Filtre por tipo de conexão

### Backlinks

**Ver onde um documento é referenciado:**
1. Abra qualquer documento
2. Veja o painel "Backlinks" à direita
3. Clique em qualquer referência para navegar

---

## 📱 Estrutura de Documentos

### Hierarquia

```
Índice Mestre (Raiz)
├── README (Visão geral)
├── Visão e Estratégia
├── Modelo de Negócio
├── Ingestão de Dados
├── Feature Engineering
├── Machine Learning
├── Gestão de Risco
├── Motor de Edge
└── Sistema de Telegram
```

### Fluxo Recomendado de Leitura

**Para novos utilizadores:**
1. [[Índice Mestre]] - Comece aqui
2. [[README]] - Visão geral
3. [[Visão e Estratégia]] - Entenda a filosofia
4. [[Modelo de Negócio]] - Entenda o negócio

**Para desenvolvedores:**
1. [[Índice Mestre]] - Visão geral
2. [[Ingestão de Dados]] - Como os dados entram
3. [[Feature Engineering]] - Como os dados são transformados
4. [[Machine Learning]] - Como os modelos funcionam

**Para operadores:**
1. [[Índice Mestre]] - Visão geral
2. [[Gestão de Risco]] - Como gerir o risco
3. [[Motor de Edge]] - Como detectar oportunidades
4. [[Sistema de Telegram]] - Como distribuir sinais

---

## 🔧 Funcionalidades Úteis

### Search

**Pesquisar em todos os documentos:**
- `Ctrl/Cmd + P` - Command palette
- `Ctrl/Cmd + Shift + F` - Search global
- Type your query and press Enter

### Tags

**Adicionar tags (opcional):**
```markdown
#tag/nome
```

**Pesquisar por tags:**
- `Ctrl/Cmd + G` - Search tags
- Type tag name to filter

### Templates

**Criar templates (opcional):**
1. Settings → Core plugins → Templates
2. Create template folder
3. Add template files
4. Use `Ctrl/Cmd + T` to insert template

### Plugins Recomendados

**Essenciais:**
- **Graph Analysis** - Visualizar relações
- **Outgoing Links** - Ver links externos
- **Dataview** - Queries avançadas

**Opcionais:**
- **Kanban** - Gestão de tarefas
- **Calendar** - Vista de calendário
- **Excalidraw** - Diagramas

---

## 📝 Edição e Personalização

### Editar Documentos

**Como editar:**
1. Abra qualquer documento
2. Clique no ícone de lápis (Edit mode)
3. Faça as alterações
4. Clique no ícone de olho (Preview mode)

### Adicionar Novos Documentos

**Criar novo documento:**
1. Clique no ícone "+" no painel esquerdo
2. Dê um nome ao arquivo
3. Adicione conteúdo
4. Use wikilinks para conectar

### Formatação Markdown

**Sintaxe básica:**
```markdown
# Título 1
## Título 2
### Título 3

**Negrito**
*Itálico*
`Código`

- Lista item 1
- Lista item 2

1. Numerado 1
2. Numerado 2

[Link](url)
[[Wikilink]]
```

---

## 🔄 Sincronização

### Local

**Backup automático:**
- Use Git para versionamento
- Configure commit automático
- Push para remote repository

### Cloud

**Opções de sync:**
- **Obsidian Sync** (pago, oficial)
- **Git** (grátis, técnico)
- **Dropbox/OneDrive** (grátis, simples)
- **iCloud** (Mac/iOS only)

### Mobile

**Usar no mobile:**
1. Instale Obsidian mobile
2. Configure sync (Obsidian Sync ou Git)
3. Abra o mesmo vault
4. Edite no mobile, sincronize automaticamente

---

## 🎯 Dicas de Produtividade

### Atalhos de Teclado

**Windows/Linux:**
- `Ctrl + N` - Novo documento
- `Ctrl + P` - Command palette
- `Ctrl + /` - Toggle edit/preview
- `Ctrl + S` - Salvar
- `Ctrl + F` - Find in current note

**macOS:**
- `Cmd + N` - Novo documento
- `Cmd + P` - Command palette
- `Cmd + /` - Toggle edit/preview
- `Cmd + S` - Salvar
- `Cmd + F` - Find in current note

### Workflows Recomendados

**Daily Review:**
1. Abra [[Índice Mestre]]
2. Verifique atualizações recentes
3. Navegue para componentes relevantes
4. Adicione notas ou atualizações

**Meeting Notes:**
1. Crie novo documento: `YYYY-MM-DD - Meeting Topic`
2. Adicione participantes e agenda
3. Use bullet points para decisões
4. Link para documentos relevantes

**Learning:**
1. Crie documento de aprendizado
2. Adicione conceitos importantes
3. Link para documentação técnica
4. Adicione exemplos práticos

---

## 🚨 Troubleshooting

### Wikilinks Não Funcionam

**Solução:**
1. Settings → Files & Links
2. Certifique-se que "Use [[Wikilinks]]" está ativado
3. Reinicie o Obsidian

### Grafo Não Mostra Conexões

**Solução:**
1. Certifique-se que há wikilinks nos documentos
2. Clique no ícone de grafo
3. Ajuste filtros se necessário

### Performance Lenta

**Solução:**
1. Settings → Core plugins → Desative plugins não usados
2. Limpe cache: Settings → About → Clear cache
3. Reduza tamanho de imagens

### Sync Não Funciona

**Solução:**
1. Verifique conexão de internet
2. Verifique configurações de sync
3. Tente sync manual
4. Consulte documentação do método de sync

---

## 📚 Recursos Adicionais

### Documentação Oficial

- **Obsidian Help:** https://help.obsidian.md/
- **Obsidian Forum:** https://forum.obsidian.md/
- **YouTube Tutorials:** https://www.youtube.com/results?search_query=obsidian+tutorial

### Comunidade

- **Reddit:** r/ObsidianMD
- **Discord:** Obsidian Discord Server
- **Twitter:** @obsidianmd

### Plugins

- **Obsidian Plugins:** https://obsidian.md/plugins
- **Community Plugins:** https://github.com/obsidianmd/obsidian-releases

---

## 🎓 Próximos Passos

### Para Começar

1. **Instale o Obsidian** se ainda não tiver
2. **Abra este diretório** como vault
3. **Leia o Índice Mestre** para visão geral
4. **Explore os documentos** usando wikilinks
5. **Personalize** conforme suas necessidades

### Para Desenvolvedores

1. **Estude a arquitetura** no README
2. **Explore os componentes técnicos**
3. **Leia o código fonte** no projeto
4. **Adicione notas** à documentação conforme necessário

### Para Operadores

1. **Entenda a visão e estratégia**
2. **Estude os componentes operacionais**
3. **Revise os procedimentos** regularmente
4. **Mantenha a documentação atualizada**

---

## 📞 Suporte

### Para Questões Sobre o Projeto

- Consulte a documentação técnica específica
- Revise o código fonte
- Contacte a equipa do projeto

### Para Questões Sobre o Obsidian

- Consulte a documentação oficial
- Visite o fórum da comunidade
- Pesquise no YouTube

---

**Última atualização:** 2026-05-19  
**Versão:** 1.0.0