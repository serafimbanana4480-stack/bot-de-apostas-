# SOP_ONBOARDING_SUBSCRITOR — Procedimento Operacional Padrão

**ID:** `SOP-007` | **Fase:** #phase/5 | **Owner:** Customer Success | **Status:** #status/active
**Última Revisão:** 2024-05-13 | **Próxima Revisão:** 2024-08-13

---

## 1. OBJETIVO

Estabelecer um processo padronizado para onboarding de novos subscritores do serviço de value betting NBA, garantindo que o subscritor compreende o serviço, tem acesso às ferramentas necessárias, e está preparado para utilizar os sinais de forma eficaz.

---

## 2. APLICAÇÃO

**Quando executar:**
- Após novo subscritor completar registo e pagamento
- Após aprovação de KYC (se aplicável)
- Quando subscritor muda de plano

**Responsável:**
- Customer Success Manager
- Operations Lead (acesso a sistemas)

**Duração estimada:**
- 1-2 horas (processo completo)

---

## 3. PRÉ-REQUISITOS

- [ ] Subscritor completou registo
- [ ] Pagamento confirmado
- [ ] KYC aprovado (se aplicável)
- [ ] Plano de subscrição definido
- [ ] Termos de serviço aceites

---

## 4. PROCEDIMENTO DETALHADO

### 4.1. Verificação Inicial (15 minutos)

**Passos:**

1. **Verificar documentação:**
   - [ ] Confirmar que registo está completo
   - [ ] Confirmar que pagamento foi processado
   - [ ] Confirmar que KYC foi aprovado
   - [ ] Confirmar que termos foram aceites

2. **Rever perfil do subscritor:**
   - [ ] Verificar plano de subscrição
   - [ ] Verificar expectativas (do questionário de onboarding)
   - [ ] Verificar nível de experiência com apostas
   - [ ] Verificar banca disponível (se fornecida)

### 4.2. Configuração de Acesso (30 minutos)

**Passos:**

1. **Criar conta de utilizador:**
   ```sql
   INSERT INTO subscribers (user_id, email, plan, start_date, status)
   VALUES ('[user_id]', '[email]', '[plan]', NOW(), 'ACTIVE');
   ```

2. **Configurar acesso ao Telegram:**
   - [ ] Adicionar subscritor ao canal de sinais apropriado
   - [ ] Enviar mensagem de boas-vindas
   - [ ] Verificar que subscritor recebe mensagens

3. **Configurar acesso ao dashboard (se aplicável):**
   - [ ] Criar credenciais de acesso
   - [ ] Configurar permissões baseadas no plano
   - [ ] Enviar instruções de login

4. **Configurar preferências de notificação:**
   - [ ] Perguntar preferência de canal (Telegram, email, SMS)
   - [ ] Configurar frequência de notificações
   - [ ] Configurar fuso horário

### 4.3. Envio de Documentação (30 minutos)

**Passos:**

1. **Enviar guia do subscritor:**
   - [ ] Enviar PDF com guia completo do serviço
   - [ ] Incluir: como receber sinais, como executar apostas, gestão de banca
   - [ ] Incluir FAQ comum

2. **Enviar vídeo tutorial (opcional):**
   - [ ] Enviar link para vídeo de onboarding
   - [ ] Enviar link para vídeo de execução de apostas

3. **Enviar materiais educacionais:**
   - [ ] Enviar guia de gestão de banca
   - [ ] Enviar glossário de termos (CLV, edge, stake, etc.)
   - [ ] Enviar políticas de risco

### 4.4. Sessão de Onboarding (30 minutos)

**Passos:**

1. **Agendar call:**
   - [ ] Contactar subscritor para agendar call
   - [ ] Enviar link de videoconferência
   - [ ] Confirmar disponibilidade

2. **Durante a call:**
   - [ ] Apresentação pessoal e do serviço
   - [ ] Explicação de como funcionam os sinais
   - [ ] Demonstração de como executar uma aposta
   - [ ] Explicação de gestão de banca
   - [ ] Explicação de riscos e expectativas realistas
   - [ ] Resposta a perguntas

3. **Follow-up:**
   - [ ] Enviar resumo da call por email
   - [ ] Enviar materiais adicionais se solicitado
   - [ ] Agendar follow-up em 7 dias

### 4.5. Verificação Pós-Onboarding (7 dias depois)

**Passos:**

1. **Contactar subscritor:**
   - [ ] Enviar mensagem: "Como está a correr a experiência?"
   - [ ] Perguntar se tem dúvidas
   - [ ] Oferecer ajuda adicional

2. **Verificar utilização:**
   - [ ] Verificar se subscritor está a receber sinais
   - [ ] Verificar se subscritor está a executar apostas
   - [ ] Verificar se subscritor está a usar o dashboard

3. **Resolver problemas:**
   - [ ] Se subscritor não está a receber sinais: investigar
   - [ ] Se subscritor tem dificuldades: oferecer suporte adicional
   - [ ] Se subscritor insatisfeito: entender motivo, tentar resolver

---

## 5. CHECKLIST FINAL

- [ ] Documentação verificada
- [ ] Conta criada
- [ ] Acesso ao Telegram configurado
- [ ] Acesso ao dashboard configurado
- [ ] Documentação enviada
- [ ] Sessão de onboarding concluída
- [ ] Follow-up agendado
- [ ] Subscritor satisfeito

---

## 6. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
- [[16_Compliance/KYC_AML]] → KYC e AML
- [[19_Telegram_System/INDEX]] → Sistema Telegram