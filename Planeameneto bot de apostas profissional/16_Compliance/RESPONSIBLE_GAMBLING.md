---
ID: CMP-006
tags: #status/active #compliance #responsible-gambling #player-protection #intervention
---

# Jogo Responsável (Responsible Gambling)

## Objetivo
Implementar um sistema proativo de proteção ao jogador que identifique, intervenha e, se necessário, exclua subscritores que exibam padrões de comportamento de jogo de risco ou problemático. Alinhar com as melhores práticas da European Gaming and Betting Association (EGBA), os códigos de conduta do SRIJ (Portugal) e as diretrizes de jogo responsável das principais jurisdições de operação, garantindo que o serviço de informação nunca seja utilizado como catalisador de comportamento compulsivo.

## O que faz
- Monitoriza métricas comportamentais de cada subscritor: frequência de apostas por dia, aumento de stake sequencial (chasing), tempo de resposta a sinais (indicador de compulsividade), dias consecutivos de atividade, drawdown emocional (expresso em reclamações/alertas), e utilização de múltiplas contas.
- Define níveis de intervenção: Informação (verde), Alerta (amarelo), Intervenção Direta (laranja), Autoexclusão/Recomendação de Ajuda (vermelho).
- Automatiza a entrega de mensagens de jogo responsável, limites de gasto sugeridos, pausas obrigatórias e bloqueios temporários.
- Mantém parceria informacional com entidades de apoio (SRIJ - Linha Apoio Jogo, GamCare, GambleAware, Jogadores Anónimos) fornecendo links e contactos.

## Porque existe
- **Obrigação Ética e Regulatória**: O operador de um serviço diretamente ligado ao jogo tem obrigação de prevenir danos, mesmo que indiretos. A legislação portuguesa (DL 66/2015) impõe aos operadores de jogo deveres de informação e prevenção; embora o serviço seja de informação, a proximidade justifica a adoção de standards equivalentes.
- **Responsabilidade Civil**: Se um subscritor com padrões evidentes de comportamento problemático não for intervencionado, e sofrer prejuízos severos, o operador pode ser alvo de ação de responsabilidade civil por omissão de proteção.
- **Reputação e Sustentabilidade**: Um serviço associado a "vícios" ou "ruínas financeiras" não é sustentável. A longevidade do negócio depende de subscritores saudáveis e lucrativos a longo prazo.
- **Compliance de Gateways**: Stripe, PayPal e outros gateways monitoram chargebacks e reclamações relacionadas com "jogo problemático"; a ausência de política de jogo responsável pode levar à suspensão da conta merchant.

## Implementação / Pseudocódigo
```python
class ResponsibleGamblingEngine:
    def __init__(self):
        self.metricas_risco = {
            "apostas_dia": {"threshold_alerta": 5, "threshold_intervencao": 10},
            "stake_sequencial_aumento": {"threshold_alerta": 3, "threshold_intervencao": 5},  # aumentos consecutivos
            "dias_consecutivos": {"threshold_alerta": 7, "threshold_intervencao": 14},
            "drawdown_7d_percent": {"threshold_alerta": 25, "threshold_intervencao": 50},
            "reclamacoes_30d": {"threshold_alerta": 2, "threshold_intervencao": 5},
            "tempo_resposta_sinal_min": {"threshold_alerta": 2, "threshold_intervencao": 1}  # resposta < 1 min indica obsessão
        }
        self.niveis = {
            "VERDE": {"acao": "nenhuma", "mensagem": None},
            "AMARELO": {"acao": "alerta_mensagem", "mensagem": "template_alerta_comportamento.md"},
            "LARANJA": {"acao": "intervencao_direta", "mensagem": "template_intervencao.md", "limite_temporario": True},
            "VERMELHO": {"acao": "autoexclusao_sugerida", "mensagem": "template_autoexclusao.md", "bloqueio_sinais": True}
        }
        self.entidades_apoio = {
            "PT": {"nome": "SRIJ - Linha Apoio Jogo", "contacto": "+351 213 893 700", "url": "https://www.srij.turismodeportugal.pt/"},
            "UK": {"nome": "GambleAware", "contacto": "0808 8020 133", "url": "https://www.begambleaware.org/"},
            "ES": {"nome": "FEJAR", "contacto": "900 533 025", "url": "https://www.fejugarresponsable.org/"},
            "GERAL": {"nome": "Gamblers Anonymous", "url": "https://www.gamblersanonymous.org/"}
        }

    def avaliar_risco_subscritor(self, subscritor_id):
        metricas = self.db.obter_metricas_30d(subscritor_id)
        score = 0
        fatores = []
        
        if metricas["apostas_dia_media"] >= self.metricas_risco["apostas_dia"]["threshold_intervencao"]:
            score += 40
            fatores.append("APOSTAS_DIARIAS_EXCESSIVAS")
        elif metricas["apostas_dia_media"] >= self.metricas_risco["apostas_dia"]["threshold_alerta"]:
            score += 15
            fatores.append("APOSTAS_DIARIAS_ELEVADAS")
        
        if metricas["aumentos_stake_consecutivos"] >= self.metricas_risco["stake_sequencial_aumento"]["threshold_intervencao"]:
            score += 35
            fatores.append("CHASING_LOSSES_SEVERO")
        elif metricas["aumentos_stake_consecutivos"] >= self.metricas_risco["stake_sequencial_aumento"]["threshold_alerta"]:
            score += 10
            fatores.append("CHASING_LOSSES_MODERADO")
        
        if metricas["dias_consecutivos_ativo"] >= self.metricas_risco["dias_consecutivos"]["threshold_intervencao"]:
            score += 25
            fatores.append("ATIVIDADE_ININTERRUPTA")
        elif metricas["dias_consecutivos_ativo"] >= self.metricas_risco["dias_consecutivos"]["threshold_alerta"]:
            score += 5
            fatores.append("ATIVIDADE_SUSTENTADA")
        
        if metricas["drawdown_7d"] >= self.metricas_risco["drawdown_7d_percent"]["threshold_intervencao"]:
            score += 30
            fatores.append("DRAWDOWN_EMOCIONAL_SEVERO")
        elif metricas["drawdown_7d"] >= self.metricas_risco["drawdown_7d_percent"]["threshold_alerta"]:
            score += 10
            fatores.append("DRAWDOWN_EMOCIONAL_MODERADO")
        
        nivel = "VERDE" if score < 20 else "AMARELO" if score < 45 else "LARANJA" if score < 70 else "VERMELHO"
        
        return {
            "subscritor_id": subscritor_id,
            "score": score,
            "fatores": fatores,
            "nivel": nivel,
            "timestamp": datetime.utcnow().isoformat()
        }

    def executar_intervencao(self, avaliacao):
        nivel = self.niveis[avaliacao["nivel"]]
        subscritor = self.db.obter_subscritor(avaliacao["subscritor_id"])
        
        if avaliacao["nivel"] == "AMARELO":
            self.telegram.enviar_mensagem_privada(
                subscritor.chat_id,
                self.renderizar_mensagem(nivel["mensagem"], subscritor.idioma, avaliacao)
            )
        elif avaliacao["nivel"] == "LARANJA":
            self.telegram.enviar_mensagem_privada(subscritor.chat_id, self.renderizar_mensagem(nivel["mensagem"], subscritor.idioma, avaliacao))
            self.db.aplicar_limite_temporario(subscritor.id, dias=7, max_stake_diaria=subscritor.stake_media * 0.5)
            self.audit_trail.registrar("RESPONSIBLE_GAMBLING", "subscritor", subscritor.id, "LIMITE_TEMPORARIO_APLICADO", None, {"dias": 7, "max_stake": subscritor.stake_media * 0.5}, "sistema:rg_engine")
        elif avaliacao["nivel"] == "VERMELHO":
            self.telegram.enviar_mensagem_privada(subscritor.chat_id, self.renderizar_mensagem(nivel["mensagem"], subscritor.idioma, avaliacao))
            self.db.bloquear_sinais(subscritor.id, motivo="AUTOEXCLUSAO_SUGERIDA")
            self.enviar_notificacao_equipa(subscritor.id, avaliacao)
            self.audit_trail.registrar("RESPONSIBLE_GAMBLING", "subscritor", subscritor.id, "SINAIS_BLOQUEADOS", None, {"motivo": "AUTOEXCLUSAO_SUGERIDA"}, "sistema:rg_engine")
```

## Thresholds e Tabelas

| Métrica | Threshold Alerta (Amarelo) | Threshold Intervenção (Laranja) | Threshold Crítico (Vermelho) | Peso no Score |
|---------|---------------------------|---------------------------------|------------------------------|---------------|
| Apostas/dia (média 7d) | ≥ 5 | ≥ 10 | — | 15 / 40 |
| Aumentos de stake consecutivos | ≥ 3 | ≥ 5 | — | 10 / 35 |
| Dias consecutivos ativo | ≥ 7 | ≥ 14 | — | 5 / 25 |
| Drawdown 7d (%) | ≥ 25% | ≥ 50% | — | 10 / 30 |
| Reclamações 30d | ≥ 2 | ≥ 5 | — | 10 / 25 |
| Tempo resposta a sinal (min) | < 2 | < 1 | — | 5 / 15 |
| Múltiplas contas detetadas | — | ≥ 2 | ≥ 3 | 20 / 40 |

| Nível | Score | Ação do Sistema | Ação Humana | Mensagem Enviada |
|-------|-------|----------------|-------------|------------------|
| VERDE | < 20 | Monitorização contínua | Nenhuma | Nenhuma |
| AMARELO | 20 - 44 | Mensagem automática de alerta | Revisão semanal pelo RG Officer | Template de autoavaliação |
| LARANJA | 45 - 69 | Limite temporário de stake -50%, pausa 7 dias obrigatória | Contacto direto via e-mail/Telegram em 24h | Template de intervenção + contactos apoio |
| VERMELHO | ≥ 70 | Bloqueio de sinais, oferta de autoexclusão, acesso apenas a recursos de ajuda | Contacto imediato pelo CO; decisão de desativação da conta em 48h | Template de autoexclusão + linhas de apoio |

## Riscos
- **Risco de Falso Positivo**: Subscritores profissionais ou quant traders legítimos podem exibir padrões similares a comportamento problemático (apostas frequentes, stakes elevadas). A intervenção automática pode alienar clientes de valor.
- **Risco de Falso Negativo**: Jogadores problemáticos sofisticados podem fragmentar atividade por múltiplas contas ou usar VPNs para ocultar padrões.
- **Risco de Responsabilidade por Intervenção**: Se o sistema intervém e o subscritor sofre danos reputacionais (ex: mensagem enviada para grupo partilhado de Telegram), pode haver litígio por difamação ou violação de privacidade.
- **Risco de Desvio de Recursos**: Monitorização extensiva consome recursos computacionais e humanos; o ROI do programa RG deve ser medido não apenas em termos de proteção, mas também de retenção saudável.

## Checklist de Jogo Responsável
- [ ] Política de Jogo Responsável aprovada pelo gestor de operações e revisada semestralmente.
- [ ] Mecanismo de autoexclusão disponível 24/7 para o subscritor (botão no dashboard, comando no Telegram).
- [ ] Sistema de avaliação de risco executado diariamente para todos os subscritores ativos (batch noturno).
- [ ] Templates de mensagem traduzidos para PT, EN, ES, DE e revisados por psicólogo especializado em adições comportamentais.
- [ ] Registo de todas as intervenções no [[16_Compliance/AUDIT_TRAIL_COMPLIANCE]] com classificação "RESPONSIBLE_GAMBLING".
- [ ] Limite de "cooling-off" configurável pelo próprio subscritor no dashboard (1 dia, 7 dias, 30 dias, indefinido).
- [ ] Parceria formal com pelo menos uma entidade de apoio em cada jurisdição principal (PT, UK, ES).
- [ ] Relatório mensal de métricas RG: total intervenções, taxa de recuperação (subscritores que retornam a VERDE), custo médio de aquisição de subscritores perdidos por intervenção.

## Links Cruzados
- [[16_Compliance/REGULAMENTACAO_PT]] - Base legal portuguesa para proteção do jogador.
- [[16_Compliance/KYC_AML]] - Verificação de identidade que previne múltiplas contas de risco.
- [[16_Compliance/DISCLAIMERS]] - Disclaimer de risco que acompanha todas as mensagens RG.
- [[17_Legal/TERMS_OF_SERVICE]] - Cláusulas de autoexclusão e limite de responsabilidade.
- [[22_Real_Money_Operations/BANCA_GESTAO]] - Gesto de banca que limita naturalmente a exposição.
