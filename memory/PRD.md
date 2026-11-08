# PRD — Barbearia do Carille

## Problema original
Site para a Barbearia do Carille onde clientes agendam horário online, escolhem serviço e barbeiro, veem horários livres e recebem confirmação automática na tela, com confirmação por WhatsApp e lembrete 24h antes do atendimento.

## Personas
- **Cliente**: quer escolher serviço, barbeiro e horário em poucos passos e ter certeza de que o horário está reservado.
- **Carille (dono)**: quer ver os agendamentos do dia, gerenciar serviços/barbeiros e não perder clientes por esquecimento (lembretes).

## Decisões de produto
- Direção visual moderno premium, com preto, branco e vermelho.
- Serviços e barbeiros demonstrativos editáveis para a primeira versão.
- Fluxo público em três etapas: serviço → barbeiro/data/horário → dados do cliente.
- Nome e telefone são os únicos dados obrigatórios do cliente.
- Confirmação na tela sempre; WhatsApp adicional quando as credenciais Meta estiverem válidas.

## Arquitetura
- Frontend React (CRA) com fluxo de reserva, painel interno simples e fallback em localStorage.
- Backend FastAPI com MongoDB (Motor) para criar, listar e excluir agendamentos, com bloqueio de horário duplicado por barbeiro.
- Frontend usa exclusivamente `REACT_APP_BACKEND_URL`; backend usa `MONGO_URL` e `DB_NAME` existentes.
- Integração WhatsApp via Meta Cloud API (templates Utility em pt_BR) com httpx assíncrono; lembretes por worker em background (asyncio, verificação a cada 5 min).

## Implementado
- Landing page responsiva com hero, catálogo de serviços, equipe e seção de experiência (visual premium preto/branco/vermelho).
- Modal de agendamento em 3 etapas com datas, horários livres, barbeiro, validação de campos e confirmação visual.
- Reserva persistida no backend e sincronizada ao abrir nova sessão ou área de gestão.
- Painel de gestão com lista de agendamentos, remoção e adição de serviços demonstrativos.
- API de agendamentos: `POST /api/appointments` (com erro 409 em colisão de horário), `GET /api/appointments`, `DELETE /api/appointments/{id}`.
- Integração WhatsApp preparada via Cloud API: confirmação imediata em background após a reserva, com estados `sent`, `failed`, `retry`, `not_configured`.
- Worker de lembretes que verifica agendamentos confirmados e prepara o lembrete 24h antes, com `reminderStatus` anti-duplicidade.
- Documentação do projeto (`/app/memory/PRD.md`) e credenciais de teste (`/app/memory/test_credentials.md`).

## Pendências e bloqueios
- **BLOQUEADO — Envio real de WhatsApp**: código pronto e testado com mocks, mas a Meta exige verificação de negócio (CNPJ) para habilitar o número. Usuário decidiu deixar para depois. Quando liberado: adicionar credenciais Meta reais e aprovar os templates `carille_confirmacao` e `carille_lembrete`.

## Backlog priorizado
- P0: nenhum item bloqueante conhecido.
- P1: colocar serviços, preços e barbeiros reais da barbearia (hoje demonstrativos).
- P1: ativar WhatsApp em produção após verificação da Meta (número real + templates aprovados).
- P1: autenticação da área de gestão e edição completa de barbeiros e serviços.
- P2: horários e dias de funcionamento configuráveis por barbeiro.
- P2: migração do worker de lembretes para agendador dedicado (cron/APScheduler) se escalar.

## Próximas tarefas
1. Coletar dados reais de serviços/barbeiros e substituir os demonstrativos.
2. Quando o usuário tiver CNPJ/verificação Meta, validar envio real de confirmação e lembrete.
3. Publicar o site quando o usuário terminar os testes.
