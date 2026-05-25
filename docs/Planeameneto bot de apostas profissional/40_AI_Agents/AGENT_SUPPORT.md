# Agent Support

**ID:** AI-004 | **Fase:** #phase/10+ | **Owner:** Chief Systems Architect | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Agente de IA para responder a FAQs de subscritores Telegram automaticamente. O Agent-Support usa LLM + RAG (Retrieval-Augmented Generation) sobre a documentação do projeto para fornecer respostas precisas.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Suporte automatizado a subscritores |
| **Stack** | LLM + RAG + Vector Database + Telegram |
| **Custo** | ~$15/mês (API LLM + Vector DB) |

---

## 2. ARQUITETURA DO AGENTE

### 2.1 Fluxo de Suporte

```
┌─────────────────────────────────────────────────────────────┐
│ AGENT-SUPPORT                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. RECEÇÃO DE PERGUNTA (Telegram)                   │   │
│  │    - Usuário envia mensagem                           │   │
│  │    - Bot detecta comando (/faq ou /help)             │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. EMBEDDING DA PERGUNTA                            │   │
│  │    - Converter pergunta em embedding                │   │
│  │    - Usar modelo de embedding (OpenAI)               │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. BUSCA SIMILAR (RAG)                              │   │
│  │    - Buscar documentos similares na BD vetorial     │   │
│  │    - Retornar top 5 documentos mais relevantes        │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. GERAÇÃO DE RESPOSTA (LLM)                        │   │
│  │    - Prompt com contexto dos documentos             │   │
│  │    - LLM gera resposta baseada na documentação        │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 5. ENVIO DE RESPOSTA (Telegram)                     │   │
│  │    - Formatar resposta                              │   │
│  │    - Enviar para usuário                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. CONFIGURAÇÃO DO TELEGRAM BOT

### 3.1 Handler de Comandos

```python
# vbq/agents/support/telegram_handler.py
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters
from vbq.agents.support.rag_agent import answer_question

async def faq_command(update: Update, context):
    """Handler para comando /faq"""
    await update.message.reply_text(
        "Envia a tua pergunta e eu responderei baseado na documentação do projeto."
    )

async def handle_message(update: Update, context):
    """Handler para mensagens"""
    question = update.message.text
    
    # Gerar resposta
    answer = answer_question(question)
    
    # Enviar resposta
    await update.message.reply_text(answer)

# Configurar handlers
faq_handler = CommandHandler('faq', faq_command)
message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
```

### 3.2 Integração com Telegram Bot

```python
# vbq/agents/support/bot.py
from telegram.ext import Application
from vbq.agents.support.telegram_handler import faq_handler, message_handler

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

application.add_handler(faq_handler)
application.add_handler(message_handler)

application.run_polling()
```

---

## 4. EMBEDDINGS E RAG

### 4.1 Criação de Embeddings

```python
# vbq/agents/support/embeddings.py
from openai import OpenAI
import numpy as np

client = OpenAI()

def create_embedding(text: str) -> list:
    """Cria embedding para um texto"""
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    
    return response.data[0].embedding
```

### 4.2 Indexação de Documentos

```python
# vbq/agents/support/indexer.py
from vbq.agents.support.embeddings import create_embedding
import chromadb

def index_documentation():
    """Indexa toda a documentação do projeto"""
    
    client = chromadb.Client()
    collection = client.get_or_create_collection("documentation")
    
    # Percorrer todos os arquivos .md
    for root, dirs, files in os.walk("Planeameneto bot de apostas profissional"):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                
                # Ler conteúdo
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Criar embedding
                embedding = create_embedding(content)
                
                # Adicionar à coleção
                collection.add(
                    documents=[content],
                    embeddings=[embedding],
                    metadatas=[{"source": filepath}],
                    ids=[filepath]
                )
```

### 4.3 Busca Similar

```python
# vbq/agents/support/retriever.py
import chromadb

def retrieve_similar_documents(question: str, top_k: int = 5) -> list:
    """Recupera documentos similares à pergunta"""
    
    client = chromadb.Client()
    collection = client.get_collection("documentation")
    
    # Criar embedding da pergunta
    from vbq.agents.support.embeddings import create_embedding
    question_embedding = create_embedding(question)
    
    # Buscar similar
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )
    
    return results
```

---

## 5. GERAÇÃO DE RESPOSTA

### 5.1 Template de Prompt

```python
# vbq/agents/support/rag_agent.py
from openai import OpenAI

client = OpenAI()

def answer_question(question: str) -> str:
    """Responde pergunta usando RAG"""
    
    # Recuperar documentos similares
    documents = retrieve_similar_documents(question)
    
    # Construir contexto
    context = "\n\n".join([
        f"Documento {i+1}:\n{doc}"
        for i, doc in enumerate(documents['documents'][0])
    ])
    
    prompt = f"""
És um assistente de suporte para um projeto de value betting NBA.

DOCUMENTAÇÃO RELEVANTE:
{context}

PERGUNTA DO USUÁRIO:
{question}

INSTRUÇÕES:
1. Responde baseado APENAS na documentação fornecida
2. Se a documentação não contiver a resposta, diz "Não encontrei essa informação na documentação"
3. Sê conciso e direto
4. Usa formato amigável
5. Máximo 200 palavras

Resposta:
"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.3
    )
    
    return response.choices[0].message.content
```

### 5.2 Exemplo de Resposta

```
O sistema usa Kelly Criterion para calcular o stake ideal. O Kelly fraction é calculado como (edge / odds) e representa a percentagem da banca a apostar. Para mais detalhes, consulta o documento 08_Risk_Management/KELLY_CRITERIO_AUTOMATICO.md.
```

---

## 6. CONFIGURAÇÃO DO VECTOR DATABASE

### 6.1 ChromaDB

```bash
pip install chromadb
```

### 6.2 Configuração

```python
# vbq/agents/support/vector_db.py
import chromadb

client = chromadb.PersistentClient(path="./vbq/agents/support/chroma_db")
collection = client.get_or_create_collection("documentation")
```

---

## 7. INDEXAÇÃO AUTOMATIZADA

### 7.1 Script de Indexação

```python
# vbq/agents/support/index_script.py
from vbq.agents.support.indexer import index_documentation

if __name__ == "__main__":
    print("Indexando documentação...")
    index_documentation()
    print("Indexação concluída!")
```

### 7.2 Agendamento de Reindexação

```python
# vbq/agents/support/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from vbq.agents.support.indexer import index_documentation

scheduler = BackgroundScheduler()

scheduler.add_job(
    func=index_documentation,
    trigger="interval",
    days=7  # Reindexar a cada 7 dias
)

scheduler.start()
```

---

## 8. EXEMPLOS DE PERGUNTAS

### 8.1 Perguntas Comuns

```
Q: Como funciona o Kelly Criterion?
A: O sistema usa Kelly Criterion para calcular o stake ideal. O Kelly fraction é calculado como (edge / odds) e representa a percentagem da banca a apostar.

Q: Qual é o critério para paper trading?
A: O paper trading dura mínimo 30 dias ou 100 sinais, o que for maior. Para passar para micro banca, o CLV paper deve ser > 1%, ROI > 0%, e drawdown < 15%.

Q: Como são calculados os sinais?
A: Os sinais são gerados pelo motor de value que combina features estatísticas, forma recente, e dias de descanso para calcular o edge e gerar recomendações.
```

---

## 9. CONFIGURAÇÃO

### 9.1 Variáveis de Ambiente

```bash
# .env
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

### 9.2 Configuração do Agente

```python
# vbq/agents/support/config.py
import os

AGENT_SUPPORT_CONFIG = {
    'openai_api_key': os.getenv('OPENAI_API_KEY'),
    'model': 'gpt-4o-mini',
    'embedding_model': 'text-embedding-3-small',
    'max_tokens': 300,
    'temperature': 0.3,
    'top_k_documents': 5,
    'reindex_interval_days': 7
}
```

---

## 10. TESTES

### 10.1 Teste de RAG

```python
# vbq/agents/support/tests/test_rag.py
def test_answer_question():
    """Teste de resposta a pergunta"""
    question = "Como funciona o Kelly Criterion?"
    
    answer = answer_question(question)
    
    assert len(answer) > 50
    assert "Kelly" in answer
```

---

## 11. LINKS CRUZADOS

- [[40_AI_Agents/INDEX]] ← Secção mãe
- [[40_AI_Agents/ASSISTENTE_ANALISE]] → Agente de análise
- [[19_Telegram_System/INDEX]] → Sistema Telegram
- [[25_SOPs/INDEX]] → SOPs do projeto

---

**Custo de implementação:** ~$15/mês (API LLM + Vector DB)  
**Tempo estimado de implementação:** 2 semanas  
**Prioridade:** BAIXA (útil mas não crítico)
