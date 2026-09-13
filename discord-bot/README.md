# Discord Bot: Twitch e Instagram

Bot em Python 3.12+ com `discord.py` 2.x e comandos slash. Ele inclui `/ping`, `/comandos`,
`/boasvindas`, `/reenviar_live` e `/limpar`; notifica
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

Em **Installation** — ou **OAuth2 > URL Generator** — selecione os escopos `bot` e `applications.commands` para convidar o bot. Dê ao bot permissão para ver e enviar mensagens apenas nos canais necessários. Para usar `/limpar`, conceda também **Read Message History** e **Manage Messages** no canal de moderação.

Ative **Message Content Intent** na seção **Bot > Privileged Gateway Intents** do Discord Developer Portal para que o listener de reações automáticas receba os anexos das mensagens. O cliente já o solicita por código; sem a ativação no portal, o Discord não entrega o conteúdo da mensagem ao bot.

Ative também **Server Members Intent** nessa mesma seção. Ele é necessário para que o Morcegão receba
entradas de membros e atribua o cargo automático. O código já solicita esse intent; o portal precisa
autorizá-lo também.

`DISCORD_GUILD_ID` registra os slash commands rapidamente no servidor de desenvolvimento. `SYNC_GLOBAL_COMMANDS=true` também sincroniza comandos globais, que podem demorar mais para aparecer.

### Reações automáticas em mídias

Defina o ID de um canal de texto para o Morcegão reagir automaticamente a imagens, GIFs e vídeos:

```dotenv
DISCORD_MEDIA_REACTION_CHANNEL_ID=123456789012345678
```

Com o **Developer Mode** ativo, clique com o botão direito no canal e escolha **Copiar ID do canal**.
Deixe a variável vazia para desativar a funcionalidade. O bot precisa de **View Channel**, **Read
Message History** e **Add Reactions** nesse canal; **Administrator** não é necessário. Ao detectar
mídia enviada por uma pessoa, ele adiciona a sequência Unicode `🇻 🇦 🇲 🇵 🇮` na ordem. Esta primeira
versão usa somente emojis Unicode.

### Cargos automáticos e por reação

O sistema usa exclusivamente IDs. Assim, renomear um cargo no Discord não quebra a configuração.
Primeiro crie os cargos que deseja oferecer e posicione o cargo do **Morcegão acima de todos os
cargos que ele pode atribuir**. Não coloque o bot acima de cargos administrativos que ele não deve
gerenciar. No canal dos menus, conceda ao bot **View Channel**, **Read Message History**, **Add
Reactions** e **Manage Roles**.

Com o Developer Mode ativo, clique com o botão direito em um cargo, canal ou mensagem e escolha
**Copiar ID**. Preencha inicialmente o canal e os cargos no `.env`; os IDs das mensagens podem ficar
vazios até elas serem publicadas:

```dotenv
DISCORD_AUTO_ROLE_ID=123456789012345678
DISCORD_ROLE_MENU_CHANNEL_ID=123456789012345678

DISCORD_ROLE_AGE_PLUS_18_ID=123456789012345678
DISCORD_ROLE_AGE_MINUS_18_ID=123456789012345678
DISCORD_ROLE_GENDER_FEMININE_ID=123456789012345678
DISCORD_ROLE_GENDER_MASCULINE_ID=123456789012345678
DISCORD_ROLE_GENDER_NON_BINARY_ID=
DISCORD_ROLE_GENDER_OTHER_ID=
DISCORD_ROLE_PRONOUN_SHE_HER_ID=123456789012345678
DISCORD_ROLE_PRONOUN_HE_HIM_ID=123456789012345678
```

Os emojis padrão estão em `.env.example`: `🔞` e `🔓` para idade; `♀️`, `♂️`, `⭐` e `🌈` para
gênero; `🌙` e `☀️` para pronomes. Todos são emojis Unicode disponíveis no Discord padrão. Você
pode alterar qualquer um por
`DISCORD_ROLE_*_EMOJI`. Para emoji personalizado, informe a string completa, por exemplo
`<:meuemoji:123456789012345678>`; o bot compara tanto a string quanto o ID do emoji.

Depois de reiniciar, um administrador pode executar `/configurar-cargos`. O comando publica as
mensagens configuradas apenas quando você o chama, adiciona as reações e responde de forma efêmera
com os IDs criados. Copie-os para as variáveis abaixo, reinicie o bot e não execute o comando de
novo, pois isso criaria outras mensagens:

```dotenv
DISCORD_AGE_ROLE_MESSAGE_ID=123456789012345678
DISCORD_GENDER_ROLE_MESSAGE_ID=123456789012345678
DISCORD_PRONOUN_ROLE_MESSAGE_ID=123456789012345678
```

Se preferir criar as mensagens manualmente, escreva uma mensagem por categoria, adicione as reações
configuradas e copie os IDs das mensagens para essas variáveis. Caso uma mensagem seja apagada e
recriada, atualize somente seu ID no `.env` e reinicie. Não há persistência de configurações além do
ambiente, por escolha: nenhum dado pessoal é armazenado.

Depois de configurados os IDs das mensagens, o próprio bot adiciona automaticamente todos os emojis
definidos no `.env` a cada inicialização. Portanto, basta deixar as mensagens no canal: ninguém precisa
procurar os emojis manualmente. O bot precisa de **Add Reactions** para essa etapa.

O comportamento é um toggle:

1. Reaja com `🔞` para receber o cargo +18.
2. Reaja com `🔓` para receber o cargo -18.
3. Se já tiver o cargo escolhido e reagir novamente, o cargo será removido.
4. Ao escolher a outra opção de idade, o cargo anterior será substituído.
5. A reação do usuário é removida automaticamente após o processamento.

Idade é exclusiva por padrão (`DISCORD_ROLE_AGE_EXCLUSIVE=true`). Gênero e pronomes permitem
múltiplas opções por padrão; defina `DISCORD_ROLE_GENDER_EXCLUSIVE=true` ou
`DISCORD_ROLE_PRONOUN_EXCLUSIVE=true` se quiser limitar cada categoria a uma opção. Reações em outro
canal, outra mensagem ou com emoji não configurado são ignoradas. O processamento usa
`on_raw_reaction_add`, portanto continua funcionando mesmo que a mensagem não esteja no cache.

Se aparecer nos logs que um cargo não é gerenciável, confira se o cargo existe, se não é integrado e
se está abaixo do cargo do bot. Se o bot não remover reações, confira também **Read Message History**
e as permissões do canal. O bot não envia erros públicos para cada reação para não poluir o canal.

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

A integração Instagram é independente da Twitch, desativada por padrão e usa o fluxo **Instagram Login**
oficial da Meta. O cliente consulta `graph.instagram.com`; portanto, não misture suas credenciais com o
fluxo Business Login/Facebook Login que usa endpoints e permissões diferentes. A conta monitorada deve
ser profissional (Business ou Creator). Para este projeto, o perfil esperado é `nosferarityy`.

1. Crie ou selecione o app em [Meta for Developers](https://developers.facebook.com/apps/) e adicione
   o produto Instagram API com Instagram Login.
2. Cadastre a URI pública HTTPS de callback na configuração OAuth da Meta. Em produção, por exemplo,
   use `https://morcegao-bot.duckdns.org/instagram/oauth/callback`.
3. Solicite apenas `instagram_business_basic`, que é suficiente para identificar a conta e consultar
   suas mídias. Em modo de desenvolvimento, a conta precisa estar entre as funções/testadores do app;
   em modo Live, ela deve concluir o consentimento OAuth e as permissões exigidas pela Meta devem estar
   aprovadas.
4. Configure o ambiente sem inserir token manualmente. `INSTAGRAM_USER_ID` e
   `INSTAGRAM_ACCESS_TOKEN` podem ficar inicialmente vazios: serão preenchidos no armazenamento seguro
   pelo callback OAuth.

```dotenv
INSTAGRAM_ENABLED=true
INSTAGRAM_USERNAME=nosferarityy
INSTAGRAM_USER_ID=
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_TOKEN_EXPIRES_AT=
INSTAGRAM_APP_ID=
INSTAGRAM_APP_SECRET=
INSTAGRAM_REDIRECT_URI=https://example.com/instagram/oauth/callback
INSTAGRAM_AUTO_REFRESH_TOKEN=false
INSTAGRAM_TOKEN_REFRESH_DAYS_BEFORE_EXPIRY=10
INSTAGRAM_TOKEN_REFRESH_CHECK_INTERVAL_HOURS=24
INSTAGRAM_API_VERSION=v22.0
INSTAGRAM_POLL_INTERVAL_SECONDS=300
INSTAGRAM_NOTIFY_EXISTING_LATEST=false
DISCORD_INSTAGRAM_CHANNEL_ID=
```

Nunca versione o `.env`, o `INSTAGRAM_APP_SECRET` ou um token. O bot também nunca escreve esses
valores em logs, respostas HTTP ou mensagens Discord.

#### Autorizar a conta

Com o bot e o FastAPI em execução, abra no navegador:

```text
https://seu-dominio/instagram/oauth/start
```

O endpoint gera um `state` aleatório, de uso único e válido por dez minutos, e redireciona à Meta. A
conta `nosferarityy` deve entrar no Instagram e aceitar o consentimento. O callback rejeita `state`
ausente, inválido ou repetido, troca o código no servidor, confere o username autorizado e mostra uma
página genérica de sucesso. Não compartilhe a URL de callback nem o código de autorização.

O resultado é gravado de forma atômica em `data/instagram-token.json`, com permissões `0600` no Linux.
O arquivo contém token, ID, username e datas de expiração/atualização e está ignorado pelo Git. Reinicie
o serviço após uma autorização bem-sucedida para criar o cliente e iniciar o polling:

```bash
sudo systemctl restart morcegao
sudo journalctl -u morcegao -n 100 --no-pager
```

Na EC2, mantenha o FastAPI em `127.0.0.1:8000` e faça o Nginx encaminhar o caminho OAuth público; não
abra a porta 8000 no Security Group. Se sua configuração Nginx ainda só encaminha o webhook Twitch,
inclua uma localização equivalente a:

```nginx
location /instagram/oauth/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Depois valide e recarregue o Nginx com `sudo nginx -t` e `sudo systemctl reload nginx`.

O bot precisa de **Ver canal**, **Enviar mensagens** e **Incorporar links** no canal cujo ID está em
`DISCORD_INSTAGRAM_CHANNEL_ID`.

#### Polling e renovação

O polling começa somente quando `INSTAGRAM_ENABLED=true`, há token disponível e o canal Discord foi
configurado. Ele consulta a mídia mais recente a cada `INSTAGRAM_POLL_INTERVAL_SECONDS`, percorre até
cinco páginas da API e persiste o ID da mídia somente depois que a mensagem Discord é enviada. Assim,
reinicializações e falhas de envio não causam duplicidade ou perda de post.

Na primeira execução, `INSTAGRAM_NOTIFY_EXISTING_LATEST=false` marca a publicação atual como conhecida
sem enviá-la. Publique uma mídia nova e aguarde o intervalo configurado para testar. Defina a variável
como `true` somente se quiser anunciar a publicação mais recente na primeira sincronização.

A renovação só funciona enquanto o token ainda está válido. Para ativá-la, informe a expiração com
fuso horário ISO 8601 e defina `INSTAGRAM_AUTO_REFRESH_TOKEN=true`. O bot verifica no intervalo de
horas configurado e renova somente quando restarem os dias definidos pela janela de antecedência.
Token expirado, revogado ou recusado exige nova autorização no painel Meta; o bot registra somente
uma mensagem segura e continua executando.

No backend padrão `TOKEN_STORAGE_BACKEND=env`, o token renovado e sua expiração são atualizados no
arquivo JSON local protegido. Em Linux, mantenha o diretório `data/` acessível apenas à conta do
serviço. Em Windows, restrinja o acesso ao arquivo pela conta que executa o processo.

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

O segredo deve ser um JSON com `access_token`, `token_type`, `user_id`, `username`, `expires_at` e
`updated_at`. A IAM Role
da instância precisa somente de `secretsmanager:GetSecretValue` e `secretsmanager:PutSecretValue`
para esse segredo. Após uma reautorização manual, atualize o backend seguro e reinicie o serviço.

Para desenvolvimento local, use `python -m bot` a partir da raiz do projeto e abra `/instagram/oauth/start`
no domínio configurado. Na EC2, use a URL HTTPS do Nginx e reinicie a unidade `morcegao` após o callback.
Erros `401`/`400` indicam token inválido ou expirado; `403` indica permissão insuficiente ou fluxo Meta
incorreto; `429` indica rate limit. Não tente acessar o perfil por scraping. Caso o token seja revogado,
execute novamente o OAuth e reinicie o serviço.

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
- `/configurar-cargos`: publica mensagens de idade, gênero e pronomes no canal de cargos e mostra os
  IDs criados. Exige **Gerenciar servidor**. Execute apenas durante a configuração inicial.
- **Canais temporários de voz:** entre no canal criador configurado para receber uma sala exclusiva.
  Não há comando adicional; use as opções nativas de edição do Discord na sua própria sala.
- `/limpar quantidade:<número>`: apaga até a quantidade informada de mensagens anteriores no mesmo
  canal. Exige **Gerenciar mensagens** para o usuário e para o bot. Exemplo: `/limpar quantidade:10`.
  O limite padrão é `100` e pode ser alterado com
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
