# Discord Bot: Twitch e Instagram

Bot em Python 3.12+ com `discord.py` 2.x e comandos slash, além do comando prefixado de
moderação `!limpar`. Ele inclui `/ping`, `/comandos`, `/boasvindas` e `/reenviar_live`; notifica
o Discord quando o perfil Twitch configurado entra ao vivo e consulta novas mídias de uma conta
Instagram profissional autorizada usando somente a API oficial da Meta. Não usa scraping,
Selenium, Playwright, navegador automatizado ou APIs não oficiais.

## Requisitos

- Python 3.12 ou superior.
- Uma aplicação de bot no Discord Developer Portal.
- Um aplicativo Twitch com EventSub e callback HTTPS público.
- Uma conta Instagram profissional autorizada e um aplicativo Meta compatível com a API Instagram Graph.

## Instalação

Clone o repositório e entre na pasta do projeto:

```bash
git clone <URL_DO_REPOSITORIO>
cd discord-bot
```

No Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No Linux e macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Instale o pacote e as ferramentas de desenvolvimento:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

As dependências usam limites de versão por major release: permitem correções e versões menores
compatíveis, mas evitam uma atualização automática para uma API principal potencialmente incompatível.

## Configuração

Copie o modelo para um arquivo local, que já está ignorado pelo Git:

No Windows:

```powershell
Copy-Item .env.example .env
```

No Linux e macOS:

```bash
cp .env.example .env
```

Nunca publique, envie por mensagem ou faça commit do `.env`. Revogue imediatamente um token exposto no provedor correspondente.

As integrações são independentes: `TWITCH_ENABLED=true` ativa EventSub;
`INSTAGRAM_ENABLED=true` ativa somente o polling Instagram. Cada uma pode ficar desativada sem
exigir suas credenciais. A API de saúde local permanece disponível, mesmo com as duas integrações
desativadas, e o router Twitch só é registrado quando a Twitch está ativa.

### API FastAPI local

`bot.web.app` contém a fábrica `create_web_app(...)`, e não uma instância global chamada `app`.
Ela recebe o mesmo `DiscordBot` criado pelo processo principal, o `NotificationStore` compartilhado
e registra `/webhooks/twitch` apenas quando a Twitch está ativada. Assim, não há um segundo cliente
Discord no processo.

Use estes valores locais e mantenha a porta fechada para a internet. Em uma EC2, mantenha-os iguais
e exponha somente o proxy HTTPS (Nginx, por exemplo):

```dotenv
WEB_HOST=127.0.0.1
WEB_PORT=8000
```

Não use `uvicorn bot.web.app:app`: esse comando falha porque `app` é uma fábrica, não um atributo
exportado. O único comando oficial de execução é `python -m bot`, que compõe e inicia Discord e
FastAPI no mesmo loop. Isso é necessário para que o webhook entregue eventos à mesma instância do bot.

### Discord

No [Discord Developer Portal](https://discord.com/developers/applications), crie ou abra a aplicação e obtenha o token na seção **Bot** e o Application ID em **General Information**. Ative **Developer Mode** no Discord para copiar o ID do servidor e os IDs dos canais.

Em **Installation** — ou **OAuth2 > URL Generator** — selecione os escopos `bot` e `applications.commands` para convidar o bot. Dê ao bot permissão para ver e enviar mensagens apenas nos canais necessários. Para usar `!limpar`, conceda também **Read Message History** e **Manage Messages** no canal de moderação.

Como `!limpar` é um comando prefixado, ative **Message Content Intent** na seção **Bot > Privileged Gateway Intents** do Discord Developer Portal. O cliente já o solicita por código; sem a ativação no portal, o Discord não entrega o conteúdo da mensagem ao bot.

`DISCORD_GUILD_ID` registra os slash commands rapidamente no servidor de desenvolvimento. `SYNC_GLOBAL_COMMANDS=true` também sincroniza comandos globais, que podem demorar mais para aparecer.

### Canais de voz temporários

Crie um canal de voz permanente, por exemplo **Criar sala**, de preferência dentro da categoria em
que as salas temporárias devem aparecer. Com o Developer Mode ativo, copie o ID desse canal e
configure-o no `.env`:

```dotenv
DISCORD_TEMPORARY_VOICE_CREATOR_CHANNEL_ID=123456789012345678
```

Deixe a variável vazia para desativar o recurso. Ao entrar no canal configurado, o Morcegão cria
`🔊 Sala de {nome}`, na mesma categoria, e move o membro para ela. O dono recebe apenas permissões
no canal temporário para alterar nome, limite e permissões da própria sala; ele não recebe
privilégios globais de servidor.

O bot precisa de **View Channel**, **Connect**, **Move Members** e **Manage Channels** nessa
categoria e nos canais envolvidos. Participantes comuns seguem a política normal da categoria.
Quando a última pessoa sai, a sala é removida; o canal criador nunca é excluído.

Os registros ativos ficam em memória. Após uma reinicialização, o bot tenta recuperar salas que
estejam na categoria do canal criador, usem o prefixo `🔊 Sala de` e tenham um overwrite explícito
de `Manage Channels` para um único dono. Salas sem essas três marcas são preservadas. Não há banco
de dados para esse recurso.

### Twitch EventSub

Defina `TWITCH_ENABLED=true` para ativar esta integração. Com `TWITCH_ENABLED=false`, o bot não
registra o webhook EventSub nem exige variáveis Twitch; a API local continua servindo apenas saúde.

No [Twitch Developer Console](https://dev.twitch.tv/console), crie uma aplicação, registre o callback HTTPS público e copie o Client ID e o Client Secret. Defina um segredo exclusivo para `TWITCH_EVENTSUB_SECRET`.

`TWITCH_BROADCASTER_LOGIN` é somente o login do canal, sem `@` e sem URL:

```dotenv
TWITCH_BROADCASTER_LOGIN=nome_do_canal
```

Deixe `TWITCH_BROADCASTER_USER_ID` vazio para que o bot descubra o ID pela API Twitch e o mantenha em memória. A cada inicialização, o bot obtém um App Access Token novo usando `TWITCH_CLIENT_ID` e `TWITCH_CLIENT_SECRET`; ele nunca lê nem grava um token Twitch no `.env`, banco de dados ou logs. O perfil pode ser alterado modificando apenas o `.env` e reiniciando o bot.

O token é validado a cada `TWITCH_TOKEN_VALIDATE_INTERVAL_SECONDS` segundos (padrão: `3600`).
Com `TWITCH_RETRY_ON_INVALID_TOKEN=true`, o bot emite e valida um novo token uma vez quando a
Twitch reporta token inválido ou a API Helix responde `401`. Para EventSub, ele consulta as
inscrições novamente antes de repetir uma criação, evitando duplicidade.

O callback precisa apontar para o caminho completo abaixo:

```text
https://seu-dominio-publico/webhooks/twitch
```

Para testar localmente, inicie um túnel HTTPS para a porta `8000` e use a URL pública do túnel em `TWITCH_CALLBACK_URL`. O servidor FastAPI responde ao desafio EventSub, valida a assinatura HMAC-SHA256, rejeita mensagens antigas e registra IDs EventSub em SQLite para não duplicar notificações.

Ferramentas como ngrok ou Cloudflare Tunnel devem encaminhar para `http://127.0.0.1:8000`; não abra a
porta `8000` no grupo de segurança da EC2. No deploy, termine TLS no proxy/túnel e encaminhe apenas
localmente para o processo do bot.

Com ngrok instalado, inicie o túnel em outro terminal:

```powershell
ngrok http 8000
```

Copie a URL HTTPS pública exibida e preencha, sem colchetes:

```dotenv
TWITCH_CALLBACK_URL=https://url-publica-do-tunel/webhooks/twitch
```

Reinicie `python -m bot` depois de alterar o callback para que a inscrição EventSub seja verificada.

Após iniciar o bot, verifique as inscrições no painel ou na referência de API EventSub da Twitch. Se a inscrição não for criada, confirme o callback HTTPS, a URL exata, o segredo e as credenciais da aplicação. Não coloque tokens em comandos compartilhados ou capturas de tela.

### Instagram oficial da Meta

A integração Instagram é desativada por padrão e é independente da Twitch. Ela usa o endpoint oficial Graph configurado por `INSTAGRAM_API_VERSION`, acessando exclusivamente o `INSTAGRAM_USER_ID` profissional autorizado. A conta, o aplicativo Meta, as permissões e o token precisam ser compatíveis com a API Instagram Graph usada pela sua aplicação.

No painel de desenvolvedores da Meta, crie o aplicativo adequado, associe a conta profissional autorizada e gere um Access Token com as permissões exigidas pelo produto escolhido. Configure:

```dotenv
INSTAGRAM_ENABLED=true
INSTAGRAM_USERNAME=perfil_autorizado
INSTAGRAM_USER_ID=17800000000000000
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_TOKEN_EXPIRES_AT=2026-11-10T03:30:00+00:00
INSTAGRAM_AUTO_REFRESH_TOKEN=false
INSTAGRAM_TOKEN_REFRESH_DAYS_BEFORE_EXPIRY=10
INSTAGRAM_TOKEN_REFRESH_CHECK_INTERVAL_HOURS=24
INSTAGRAM_API_VERSION=v22.0
INSTAGRAM_POLL_INTERVAL_SECONDS=300
INSTAGRAM_NOTIFY_EXISTING_LATEST=false
DISCORD_INSTAGRAM_CHANNEL_ID=123456789012345678
```

O exemplo não contém token. `INSTAGRAM_USERNAME` aceita apenas o nome de usuário, sem `@` e sem URL; o bot remove um `@` inicial. Para trocar o perfil, atualize essas variáveis e reinicie o processo, sem mudar código.

O intervalo mínimo de polling é 60 segundos; o padrão de 300 segundos reduz consumo e risco de rate limit. Na primeira execução, `INSTAGRAM_NOTIFY_EXISTING_LATEST=false` registra a publicação mais recente como conhecida sem notificá-la. Defina como `true` para notificar essa publicação inicial.

#### Renovação automática do token Instagram

A renovação só funciona enquanto o token ainda está válido. Para ativá-la, informe a expiração com
fuso horário ISO 8601 e defina `INSTAGRAM_AUTO_REFRESH_TOKEN=true`. O bot verifica no intervalo de
horas configurado e renova somente quando restarem os dias definidos pela janela de antecedência.
Token expirado, revogado ou recusado exige nova autorização no painel Meta; o bot registra somente
uma mensagem segura e continua executando.

No backend padrão `TOKEN_STORAGE_BACKEND=env`, o token renovado e sua expiração são atualizados no
`.env` local, que já é ignorado pelo Git. Em Linux, o arquivo recebe permissão `0600`; em Windows,
restrinja o acesso ao arquivo pela conta que executa o serviço. Nunca faça commit do `.env`.

Para EC2, prefira AWS Secrets Manager com IAM Role — não coloque chaves AWS no `.env`:

```dotenv
TOKEN_STORAGE_BACKEND=aws_secrets_manager
AWS_SECRET_NAME=nome-do-segredo-instagram
AWS_REGION=sa-east-1
```

Instale o extra AWS no ambiente de produção:

```bash
python -m pip install -e ".[aws]"
```

O segredo deve ser um JSON com `access_token`, `token_type`, `expires_at` e `updated_at`. A IAM Role
da instância precisa somente de `secretsmanager:GetSecretValue` e `secretsmanager:PutSecretValue`
para esse segredo. Após uma reautorização manual, atualize o backend seguro e reinicie o serviço.

Para testar a API manualmente, use a ferramenta oficial Graph API Explorer ou a documentação do produto Meta habilitado na sua aplicação. Não tente acessar o perfil com scraping. Caso o token expire, gere ou renove um token autorizado, atualize apenas o `.env` e reinicie. Revogue a autorização no painel Meta se o token for comprometido ou se quiser remover o acesso.

Esta versão prepara a separação para futuros callbacks `/webhooks/instagram`, mas não afirma existir um webhook geral de nova publicação. A notificação atual é feita por polling, pois eventos Meta devem ser implementados apenas quando oficialmente suportados pela configuração da conta e do aplicativo.

## Iniciar

Preencha sempre as variáveis Discord. Preencha as variáveis Twitch somente ao usar
`TWITCH_ENABLED=true`, e as Instagram somente ao usar `INSTAGRAM_ENABLED=true`. Com o ambiente
virtual ativado:

```bash
python -m bot
```

Quando o bot estiver pronto, `/ping` responde `Pong!`. A API FastAPI inicia em `WEB_HOST:WEB_PORT`;
com `TWITCH_ENABLED=true`, registra o EventSub `stream.online`. Com `INSTAGRAM_ENABLED=true`, inicia
o polling Instagram e, quando configurada, a tarefa de renovação. As duas integrações podem operar
juntas ou separadamente.

Em outro terminal, teste a saúde da API:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

O resultado esperado é `{"status":"ok"}`. A documentação local fica em
`http://127.0.0.1:8000/docs`. Para encerrar, use `Ctrl+C`; o processo cancela as tarefas periódicas,
fecha os clientes HTTP e encerra o servidor web de modo coordenado.

## Comandos Discord

- `/comandos`: mostra os comandos disponíveis e suas formas de uso.
- `/ping`: confirma que o bot está respondendo.
- `/boasvindas usuario:@membro`: envia a apresentação do Morcegão por DM. Exige a permissão
  **Gerenciar servidor**.
- `/reenviar_live`: reenvia a notificação da última live Twitch ainda aberta. Exige a permissão
  **Gerenciar servidor** e responde somente ao administrador que executou o comando.
- **Canais temporários de voz:** entre no canal criador configurado para receber uma sala exclusiva.
  Não há comando adicional; use as opções nativas de edição do Discord na sua própria sala.
- `!limpar <quantidade>`: apaga até a quantidade informada de mensagens anteriores no mesmo canal
  e também a própria mensagem de comando. Exige **Gerenciar mensagens** para o usuário e para o
  bot. Exemplo: `!limpar 10`. O limite padrão é `100` e pode ser alterado com
  `MAX_MESSAGES_TO_DELETE` no `.env`.

`/reenviar_live` usa o estado em memória criado depois que uma live é confirmada pela API Twitch.
Antes de reenviar, ele confirma novamente que a stream continua online. Esse estado não é
persistido: após reiniciar o bot, não há uma live disponível para reenviar até que um novo evento
`stream.online` seja recebido e confirmado.

O `discord.py` usa exclusão individual como fallback para mensagens com mais de duas semanas. Ainda assim, mensagens protegidas, indisponíveis ou que falhem na API podem não ser removidas; nesse caso o bot mostra uma resposta temporária e registra o erro técnico.

## Qualidade

Os testes usam mocks e SQLite temporário: não chamam Twitch, Instagram, Meta nem Discord reais.

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

## Solução de problemas

- **Webhook Twitch rejeitado:** confirme que o callback é HTTPS público, contém `/webhooks/twitch` e usa o mesmo EventSub Secret configurado no painel Twitch.
- **Sem notificação Twitch:** confirme que o bot tem acesso ao canal definido em `DISCORD_NOTIFICATION_CHANNEL_ID` e que a inscrição EventSub existe. Se as credenciais da aplicação forem recusadas, confira `TWITCH_CLIENT_ID` e `TWITCH_CLIENT_SECRET`; nenhum token Twitch precisa ser configurado manualmente.
- **`Could not import module "bot.web.serve"`:** `serve.py` não existe de propósito. Não use Uvicorn isolado nem `--reload`; execute `python -m bot` para compor uma única instância Discord e a API.
- **`Attribute "app" not found`:** `bot.web.app` expõe a fábrica `create_web_app`, não uma instância global. Execute `python -m bot`.
- **Token Instagram expirado ou sem permissão:** gere um token autorizado no painel Meta, confira a conta profissional e as permissões, atualize o backend seguro e reinicie. A renovação automática não recupera token já expirado ou revogado.
- **Sem mensagem Instagram na primeira execução:** esse é o comportamento esperado com `INSTAGRAM_NOTIFY_EXISTING_LATEST=false`.
- **Canal Discord inválido:** copie o Channel ID com Developer Mode e conceda permissão de visualizar e enviar mensagens ao bot.
