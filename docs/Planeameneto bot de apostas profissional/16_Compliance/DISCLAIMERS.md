---
ID: CMP-003
tags: #status/active #compliance #disclaimers #legal #risk
---

# Disclaimers Legais

## Objetivo
Consolidar todos os avisos legais, isenções de responsabilidade e declarações de risco que devem ser apresentados aos subscritores em todos os pontos de contacto com o sistema (onboarding, Telegram, dashboard, emails, faturas). Garantir que o subscritor compreende inequivocamente que o serviço é de informação pura, não constitui aconselhamento financeiro nem de investimento, e que perdas são possíveis e esperáveis.

## O que faz
- Define templates de disclaimers para 5 contextos distintos: (1) landing page / site, (2) contrato de subscrição, (3) mensagens de sinal Telegram, (4) relatórios de performance, (5) comunicações de marketing.
- Especifica requisitos de legibilidade (tamanho de letra mínimo, contraste, posicionamento não escondido).
- Mapeia variações linguísticas por jurisdição (PT, EN, ES, DE, FR).
- Define cadência de reafirmação do disclaimer (ex: mensal para subscritores ativos).

## Porque existe
A natureza do serviço — recomendações baseadas em modelos quantitativos para apostas desportivas — coloca-o numa zona de risco reputacional e legal elevado. Um disclaimer inadequado expõe a:
- Ações judiciais de subscritores insatisfeitos que alegam "perda de confiança" ou "aconselhamento enganoso".
- Reclassificação por autoridades reguladoras como serviço de investimento ou intermediação de apostas.
- Responsabilidade por danos diretos e indiretos quando o subscritor não foi adequadamente informado dos riscos.
- Proibições de publicidade em plataformas (Google, Meta, Twitter) por violação de políticas de serviços financeiros/jogo.

## Implementação / Pseudocódigo
```python
class DisclaimerEngine:
    def __init__(self):
        self.templates = {
            "onboarding": self.carregar_template("disclaimer_onboarding_v2.md"),
            "sinal": self.carregar_template("disclaimer_sinal_curto.md"),
            "relatorio": self.carregar_template("disclaimer_relatorio_performance.md"),
            "marketing": self.carregar_template("disclaimer_marketing.md"),
            "fatura": self.carregar_template("disclaimer_fatura_legal.md")
        }
        self.regras_visibilidade = {
            "min_font_size_pt": 10,
            "contrast_ratio": 4.5,
            "posicao": "ANTES_DA_ACAO",  # disclaimer antes do botão de subscrição/confirmação
            "scroll_required": False      # não pode estar escondido após scroll
        }

    def renderizar_disclaimer(self, contexto, idioma, risco_perfil="standard"):
        template = self.templates[contexto]
        variaveis = {
            "data_atual": datetime.utcnow().isoformat(),
            "jurisdicao": self.detetar_jurisdicao_subscritor(),
            "taxa_acerto_historica": self.obter_metrica("taxa_acerto_12m"),
            "drawdown_maximo": self.obter_metrica("drawdown_maximo_12m"),
            "clv_medio": self.obter_metrica("clv_medio_12m")
        }
        texto = template.render(**variaveis, idioma=idioma)
        
        if risco_perfil == "agressivo":
            texto += self.templates["aviso_reforcado_agressivo"].render()
        
        return {
            "texto": texto,
            "hash_sha256": hashlib.sha256(texto.encode()).hexdigest(),
            "timestamp_geracao": datetime.utcnow().isoformat()
        }

    def validar_consentimento_explicto(self, subscritor_id, contexto):
        registo = self.db.consultar(
            "SELECT consentimento_hash, timestamp FROM disclaimers_consentimentos "
            "WHERE subscritor_id = %s AND contexto = %s ORDER BY timestamp DESC LIMIT 1",
            (subscritor_id, contexto)
        )
        if not registo:
            return False
        
        disclaimer_atual = self.renderizar_disclaimer(contexto, idioma="pt")
        if registo["consentimento_hash"] != disclaimer_atual["hash_sha256"]:
            return False  # disclaimer foi alterado; requer novo consentimento
        
        idade_consentimento = datetime.utcnow() - registo["timestamp"]
        if idade_consentimento.days > 90 and contexto == "sinal":
            return False  # reafirmação trimestral
        
        return True
```

## Thresholds e Tabelas

| Contexto | Frequência Mínima | Reafirmação Obrigatória | Tamanho Mínimo Texto | Idiomas Obrigatórios |
|----------|-------------------|------------------------|---------------------|---------------------|
| Onboarding | Uma vez por subscrição | Se alteração material | 800 caracteres | PT, EN |
| Sinal Telegram | Cada mensagem de sinal | Trimestral | 200 caracteres | PT (principal), EN |
| Relatório Performance | Mensal | Mensal | 400 caracteres | PT, EN |
| Comunicação Marketing | Cada campanha | Por campanha | 300 caracteres | PT, EN, ES |
| Fatura / Recibo | Cada transação | N/A (incorporado) | 150 caracteres | PT |

| Variação por Jurisdição | Texto Adicional Obrigatório |
|------------------------|----------------------------|
| Portugal | "O serviço não constitui jogo nem intermediação de apostas. As perdas são possíveis. Consulte o seu contabilista para efeitos de IRS." |
| Reino Unido | "Gamble responsibly. For help visit GambleAware.org. This is not financial advice." |
| Alemanha | "Dies ist keine Anlageberatung. Verluste sind möglich. Spielen Sie verantwortungsbewusst." |
| Espanha | "El servicio no constituye asesoramiento financiero. Las pérdidas son posibles. Juegue con responsabilidad." |
| França | "Ce service ne constitue pas un conseil en investissement. Les pertes sont possibles. Jouez de manière responsable." |

## Riscos
- **Risco de Invalidação por Fraude de Clarity**: Se o disclaimer for considerado "ilegível" ou "escondido em letra miúda", os tribunais de consumo podem invalidar a cláusula de isenção (direito português e europeu do consumidor).
- **Risco de Alteração Não Comunicada**: Qualquer mudança material no modelo de precificação ou na taxa de turnover pode invalidar consentimentos prévios se não houver reafirmação.
- **Risco de Publicidade Enganosa**: Mesmo com disclaimer, se as comunicações de marketing enfatizarem apenas ganhos e omitirem riscos, a atividade pode ser classificada como publicidade enganosa (DL 66/2015 art. 23º).
- **Risco de Retenção de Consentimentos**: A ausência de prova de consentimento (hash + timestamp + IP) torna impossível defender em litígio que o subscritor foi devidamente informado.

## Checklist de Implementação de Disclaimers
- [ ] Templates de disclaimers validados por advogado em PT, EN, ES, DE, FR.
- [ ] Registo de consentimentos com hash SHA-256 do texto exibido, timestamp, IP e user-agent.
- [ ] Validação automática de que o subscritor passou pelo disclaimer antes de qualquer pagamento (onboarding flow).
- [ ] Verificação trimestral de "stale consent" — subscritores com consentimento há mais de 90 dias recebem reafirmação antes do próximo sinal.
- [ ] Inclusão de disclaimer em TODAS as mensagens Telegram (nunca omitido, mesmo em mensagens de "teste").
- [ ] Revisão semestral de templates por alterações regulamentares ou jurisprudência nova.
- [ ] Backup criptografado de todos os consentimentos por 10 anos (prescrição civil portuguesa).

## Links Cruzados
- [[16_Compliance/REGULAMENTACAO_PT]] - Base legal portuguesa que molda o conteúdo dos disclaimers.
- [[16_Compliance/REGULAMENTACAO_EU]] - Diretivas europeias aplicáveis às variações linguísticas.
- [[16_Compliance/RESPONSIBLE_GAMBLING]] - Disclaimer ligado a intervenções de jogo responsável.
- [[17_Legal/TERMS_OF_SERVICE]] - Contrato onde os disclaimers são incorporados por referência.
- [[17_Legal/PRIVACY_POLICY]] - Disclaimer de privacidade complementar.
