# PRD — Barbearia do Carille

## Problema original
Site para a Barbearia do Carille onde clientes agendam horário online, escolhem serviço e barbeiro, veem horários livres e recebem confirmação automática na tela.

## Decisões de produto
- Direção visual moderno premium, com preto, branco e vermelho.
- Serviços e barbeiros demonstrativos editáveis para a primeira versão.
- Fluxo público em três etapas: serviço, barbeiro/data/horário e dados do cliente.
- Integração de confirmação por WhatsApp/e-mail fica no backlog; a confirmação visual já está disponível.
- Nome e telefone são os únicos dados obrigatórios do cliente.

## Arquitetura
- Frontend React com fluxo de reserva, painel interno simples e fallback localStorage.
- Backend FastAPI com MongoDB para criar, listar e excluir agendamentos, incluindo bloqueio de horário duplicado por barbeiro.
- Frontend usa exclusivamente `REACT_APP_BACKEND_URL`; backend usa `MONGO_URL` e `DB_NAME` existentes.

## Implementado
- Landing page responsiva com hero, catálogo de serviços, equipe e seção de experiência.
- Modal de agendamento com horários, datas, barbeiro, validação de campos e confirmação.
- Reserva persistida no backend e sincronizada ao abrir uma nova sessão ou área de gestão.
- Painel de gestão com lista de agendamentos, remoção e adição de serviços demonstrativos.
- Imagens, grid editorial, animações de entrada, estados ativos e identificadores de teste nos elementos interativos.
- Integração preparada para WhatsApp Cloud API via tarefa em background após persistência da reserva, com estados `sent`, `failed`, `retry` e `not_configured`.
- Payload de template Utility em `pt_BR` com nome, data/horário, barbeiro e serviço, mantendo token exclusivamente no backend.

## Backlog priorizado
- P0: nenhum item bloqueante conhecido.
- P1: integração de confirmação via WhatsApp e/ou e-mail.
- P1: autenticação da área de gestão e edição completa dos dados de barbeiros e serviços.
- P2: horários e dias de funcionamento configuráveis por barbeiro.
- P1: adicionar credenciais Meta reais e confirmar template aprovado para ativar o envio de WhatsApp em produção.