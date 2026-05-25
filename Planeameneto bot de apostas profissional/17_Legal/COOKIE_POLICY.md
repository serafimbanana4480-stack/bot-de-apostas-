---
ID: LEG-003
tags: #status/active #legal #cookies #e-privacy #gdpr #consent
---

# Política de Cookies

## Objetivo
Garantir total conformidade com a Diretiva 2002/58/CE (e-Privacy), o Regulamento ePrivacy (em negociação), e as orientações do GDPR relativas ao uso de tecnologias de rastreamento (cookies, localStorage, sessionStorage, device fingerprinting, pixels de rastreamento). A política deve informar o utilizador de forma granular sobre cada tecnologia utilizada, a sua finalidade, duração, e operador responsável, recolhendo consentimento explícito prévio para cookies não estritamente necessários.

## O que faz
- Cataloga todas as tecnologias de rastreamento utilizadas no site, dashboard, e comunicações (e-mail, Telegram web).
- Classifica cookies/tecnologias em três categorias: (1) Estritamente Necessários, (2) Preferências / Estatísticos (funcionais), (3) Marketing / Terceiros (profilagem).
- Implementa mecanismo de banner/cookie consent com opção de rejeição granular (não "tudo ou nada").
- Regista consentimentos com timestamp, versão da política, e seleções efetuadas.
- Fornece interface de gestão de preferências (alteração/revogação de consentimento).

## Porque existe
- **Obrigação Legal**: O art. 5º, nº3 da Diretiva 2002/58/CE exige informação e consentimento informado para armazenar ou aceder a informação no dispositivo do utilizador. A CNPD e o ICO aplicam coimas por violação.
- **Risco de Publicidade**: Sem consentimento válido para cookies de marketing, campanhas em Google/Meta podem ser suspensas por violação das políticas de publicidade personalizada.
- **Transparência**: Subscritores exigentes quanto à privacidade (perfil típico de utilizadores quantitativos) valorizam controlo granular.
- **Concorrência**: Operadores que não cumprem podem ser denunciados por concorrentes ou por ONGs de defesa do consumidor (ex: Noyb - Max Schrems).

## Implementação / Pseudocódigo
```python
class CookiePolicyEngine:
    def __init__(self):
        self.categorias = {
            "necessarios": {
                "finalidade": "Funcionamento essencial do site e segurança",
                "base_juridica": "INTERESSE_LEGITIMO",
                "consentimento_obrigatorio": False,
                "exemplos": ["session_id", "csrf_token", "auth_token", "cookie_consent_status"]
            },
            "preferencias": {
                "finalidade": "Lembrar preferências de idioma, tema, e configurações de dashboard",
                "base_juridica": "CONSENTIMENTO",
                "consentimento_obrigatorio": True,
                "exemplos": ["idioma_preferido", "dashboard_layout", "notificacoes_email"]
            },
            "estatisticos": {
                "finalidade": "Análise de tráfego, comportamento de navegação, e medição de performance",
                "base_juridica": "CONSENTIMENTO",
                "consentimento_obrigatorio": True,
                "exemplos": ["_ga", "_gid", "_gat", "hotjar_session", "amplitude_id"]
            },
            "marketing": {
                "finalidade": "Publicidade personalizada, remarketing, e medição de conversão de campanhas",
                "base_juridica": "CONSENTIMENTO",
                "consentimento_obrigatorio": True,
                "exemplos": ["_fbp", "fr", "IDE (DoubleClick)", "__Secure-3PSID"]
            }
        }
        self.duracoes_maximas = {
            "necessarios": 365,  # dias
            "preferencias": 365,
            "estatisticos": 365,
            "marketing": 90
        }

    def avaliar_consentimento(self, request):
        consent_cookie = request.cookies.get("cookie_consent_v2")
        if not consent_cookie:
            return {"status": "NAO_SOLICITADO", "permissoes": {c: False for c in self.categorias if c != "necessarios"}}
        
        consent = json.loads(consent_cookie)
        return {
            "status": "SOLICITADO",
            "timestamp": consent["timestamp"],
            "versoes": consent["versoes"],
            "permissoes": {cat: consent.get(cat, False) for cat in self.categorias}
        }

    def ativar_scripts_por_categoria(self, consentimento):
        scripts_permitidos = []
        for categoria, permitido in consentimento["permissoes"].items():
            if categoria == "necessarios" or permitido:
                scripts_permitidos.extend(self.categorias[categoria]["exemplos"])
        return scripts_permitidos

    def bloquear_pre_consentimento(self, request):
        # Antes do consentimento, bloquear todos os scripts não necessários
        consent = self.avaliar_consentimento(request)
        if consent["status"] == "NAO_SOLICITADO":
            return {"bloquear": ["estatisticos", "marketing", "preferencias"], "permitir": ["necessarios"]}
        return {"bloquear": [c for c, p in consent["permissoes"].items() if not p and c != "necessarios"], "permitir": [c for c, p in consent["permissoes"].items() if p or c == "necessarios"]}

    def registrar_consentimento(self, subscritor_id, selecoes, versao_politica):
        registo = {
            "subscritor_id": subscritor_id,
            "timestamp": datetime.utcnow().isoformat(),
            "selecoes": selecoes,
            "versao_politica": versao_politica,
            "ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "hash": hashlib.sha256(json.dumps(selecoes, sort_keys=True).encode()).hexdigest()
        }
        self.db.inserir("cookie_consent_log", registo)
        return registo["hash"]

    def gerar_banner_conteudo(self, idioma):
        template = self.carregar_template(f"cookie_banner_{idioma}.md")
        return template.render(
            categorias=self.categorias,
            duracoes=self.duracoes_maximas,
            link_privacidade="/privacidade",
            link_detalhes_cookies="/cookies/detalhes"
        )
```

## Thresholds e Tabelas

| Categoria | Base Jurídica | Banner Obrigatório | Pode Pré-carregar | Duração Máxima | Operadores |
|-----------|--------------|-------------------|-------------------|----------------|------------|
| Necessários | Interesse legítimo | Não | Sim | 12 meses | Próprio |
| Preferências | Consentimento | Sim | Não | 12 meses | Próprio |
| Estatísticos | Consentimento | Sim | Não | 12 meses | Próprio, Google, Hotjar, Amplitude |
| Marketing | Consentimento | Sim | Não | 3 meses | Meta, Google, Programáticas |

| Tecnologia | Finalidade | Categoria | Duração | Pode Ser Bloqueado |
|-----------|-----------|-----------|---------|-------------------|
| session_id | Autenticação | Necessários | Sessão | Não |
| cookie_consent_v2 | Memorizar escolhas de cookies | Necessários | 12 meses | Não |
| _ga (Google Analytics) | Análise de tráfego | Estatísticos | 12 meses | Sim |
| _fbp (Facebook Pixel) | Remarketing | Marketing | 3 meses | Sim |
| amplitude_id | Tracking de produto | Estatísticos | 12 meses | Sim |
| hotjar_userid | Heatmaps, gravações | Estatísticos | 12 meses | Sim |

## Riscos
- **Risco de Consentimento Inválido**: Banner que não permite recusa granular (ex: botão "Aceitar tudo" sem "Recusar tudo" ou seleção por categoria) é considerado inválido pelo Tribunal de Justiça da UE (Sentença Planet49, C-673/17).
- **Risco de Carregamento Prévio**: Se scripts de marketing ou analytics carregam ANTES do utilizador clicar em "Aceitar", o consentimento é nulo e a operação é ilícita.
- **Risco de Dados de Navegação**: O histórico de navegação do utilizador (páginas visitadas no site, tempo de permanência) é considerado dado pessoal; sem base jurídica adequada, constitui infração.
- **Risco de Transferência de Dados**: Cookies do Google/Meta transferem dados para EUA. Sem TIA/SCC e consentimento explícito, viola o Schrems II e o GDPR.

## Checklist de Política de Cookies
- [ ] Inventário completo de cookies e tecnologias de rastreamento no site, dashboard, e e-mails (pixel tracking).
- [ ] Implementação de banner de cookies com opções: "Aceitar todos", "Recusar todos", "Personalizar" (toggle por categoria).
- [ ] Bloqueio prévio de scripts não necessários: nenhum cookie de 3ª parte carrega antes do consentimento.
- [ ] Registo de consentimentos com timestamp, IP, user-agent, versão da política, e hash das seleções.
- [ ] Interface de alteração de preferências acessível no rodapé do site e no dashboard ("Gerir cookies").
- [ ] Revisão trimestral do inventário de cookies por evolução de ferramentas (ex: adição de nova ferramenta de analytics).
- [ ] Cláusulas de processamento de dados (DPA) com Google, Meta, Hotjar, Amplitude que incluam garantias de não transferência não autorizada.
- [ ] Teste automatizado mensal (Cypress/Playwright) que verifica se scripts de marketing estão bloqueados antes de consentimento.

## Links Cruzados
- [[17_Legal/PRIVACY_POLICY]] - Política de privacidade geral que incorpora a política de cookies.
- [[16_Compliance/REGULAMENTACAO_EU]] - Diretiva e-Privacy e jurisprudência Planet49.
- [[16_Compliance/REGULAMENTACAO_PT]] - Orientações da CNPD sobre cookies.
- [[34_Security/SECRETS_MANAGEMENT]] - Gestão de API keys de analytics e tracking.
