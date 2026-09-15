# Graph Report - discord-bot  (2026-09-14)

## Corpus Check
- 60 files · ~423,464 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 1547 nodes · 3169 edges · 71 communities (62 shown, 8 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 338 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6b55daac`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- InstagramAPIError
- test_role_management.py
- test_temporary_voice.py
- routes.py
- test_welcome.py
- .on_raw_reaction_add
- test_config.py
- test_live_commands.py
- TemporaryVoice
- test_media_reactions.py
- .from_environment
- DiscordNotificationSender
- YouTubeAudioService
- test_cleanup_command.py
- test_music.py
- Music
- InstagramTokenData
- test_instagram.py
- InstagramTokenRefreshTask
- .refresh_access_token
- test_twitch.py
- test_sends_instagram_post_content_and_link_button
- test_run_services_composes_single_bot_and_cleans_up_tasks
- MemberActivityLogs
- CommandAccessTree
- TwitchClient
- InstagramTokenStore
- .resend_instagram_post_command
- NotificationStore
- generate_deployment_article_pdf.py
- main.py
- test_instagram_oauth.py
- Configuração
- client.py
- twitch_auth.py
- InstagramMedia
- instagram_token_store.py
- CurrentTwitchLiveStore
- asyncio
- test_web_app_exposes_health_and_initializes_shared_store
- InstagramOAuthClient
- ._request
- test_retries_transient_token_endpoint_failure
- generate_deployment_article.py
- models.py
- instagram.py
- FakeInteractionResponse
- TwitchError
- handle_app_command_error
- ._parse_media
- test_validator_validates_once_and_stops_cleanly
- FakeInstagramClient
- SecretStore
- environment
- Settings
- .__init__
- test_poller_logs_do_not_include_instagram_token
- ValueError
- .expires_soon
- FakeSecretStore
- General
- RoleMenuSettings
- cogs/__init__.py
- bot/__init__.py
- integrations/__init__.py
- InstagramTokenRefreshResult
- tasks/__init__.py
- InstagramTokenRefreshClient
- web/__init__.py
- discord-bot

## God Nodes (most connected - your core abstractions)
1. `Settings` - 105 edges
2. `General` - 45 edges
3. `DiscordBot` - 44 edges
4. `TwitchClient` - 42 edges
5. `InstagramMedia` - 42 edges
6. `InstagramTokenData` - 40 edges
7. `InstagramClient` - 37 edges
8. `ConfigurationError` - 36 edges
9. `DiscordNotificationSender` - 36 edges
10. `NotificationStore` - 35 edges

## Surprising Connections (you probably didn't know these)
- `test_media_listener_is_unique_and_preserves_prefix_command_processing()` --uses--> `DiscordBot`  [INFERRED]
  tests/test_media_reactions.py → src/bot/client.py
- `test_cleanup_handles_discord_failures()` --uses--> `General`  [INFERRED]
  tests/test_cleanup_command.py → src/bot/cogs/general.py
- `test_cleanup_is_registered_as_a_slash_command_and_purges_requested_messages()` --uses--> `General`  [INFERRED]
  tests/test_cleanup_command.py → src/bot/cogs/general.py
- `test_cleanup_rejects_non_positive_quantities()` --uses--> `General`  [INFERRED]
  tests/test_cleanup_command.py → src/bot/cogs/general.py
- `test_cleanup_rejects_quantity_above_configured_limit()` --uses--> `General`  [INFERRED]
  tests/test_cleanup_command.py → src/bot/cogs/general.py

## Import Cycles
- None detected.

## Communities (71 total, 8 thin omitted)

### Community 0 - "InstagramAPIError"
Cohesion: 0.12
Nodes (16): InstagramAPIError, InstagramPermissionError, InstagramProfileNotFoundError, InstagramRateLimitError, RuntimeError, Monta a URL oficial para consultar o perfil autorizado., Monta a URL oficial para consultar mídias do perfil autorizado., Obtém os dados básicos do perfil profissional autorizado. (+8 more)

### Community 1 - "test_role_management.py"
Cohesion: 0.06
Nodes (45): discord_error(), FakeBot, FakeChannel, FakeGuild, FakeMember, FakeMessage, FakeRole, payload() (+37 more)

### Community 2 - "test_temporary_voice.py"
Cohesion: 0.06
Nodes (46): build_voice_fixture(), discord_error(), FakeBot, FakeCategory, FakeGuild, FakeMember, FakePrincipal, FakeRole (+38 more)

### Community 3 - "routes.py"
Cohesion: 0.10
Nodes (31): receive_twitch_webhook(), is_twitch_timestamp_fresh(), _parse_optional_timestamp(), _parse_twitch_online_event(), Any, datetime, Rotas FastAPI para notificações EventSub da Twitch., Converte um payload EventSub mínimo, tolerando campos opcionais. (+23 more)

### Community 4 - "test_welcome.py"
Cohesion: 0.07
Nodes (33): discord_error(), FakeInteraction, FakeInteractionResponse, FakeNamedChannel, FakeWelcomeClient, FakeWelcomeUser, asyncio, HTTPException (+25 more)

### Community 5 - ".on_raw_reaction_add"
Cohesion: 0.12
Nodes (14): RawReactionActionEvent, Role, Guild, listener, Member, Remove o cargo existente ou o adiciona, respeitando exclusividade., Resolve um membro do cache e usa API somente quando necessário., Remove somente a reação do usuário depois de uma alteração bem-sucedida. (+6 more)

### Community 6 - "test_config.py"
Cohesion: 0.04
Nodes (50): parametrize, Testes unitários da configuração do ambiente., Variáveis removidas não voltam a ativar opções de pronomes., A ausência de token Discord deve interromper a leitura da configuração., Os formatos booleanos aceitos devem ser interpretados corretamente., O controle de repetição Twitch usa os mesmos formatos booleanos aceitos., O limite de moderação tem padrão seguro e não aceita valores não positivos., O caminho de cookies é opcional e permanece uma configuração local do host. (+42 more)

### Community 7 - "test_live_commands.py"
Cohesion: 0.11
Nodes (34): FakeInteraction, FakeNotificationSender, FakeTwitchClient, latest_instagram_post(), open_live(), asyncio, Testes dos comandos slash de reenvio de live e lista de comandos., Interação mínima para executar callbacks do cog diretamente. (+26 more)

### Community 8 - "TemporaryVoice"
Cohesion: 0.07
Nodes (33): Snowflake, Bot, Client, Guild, GuildChannel, listener, Lock, Member (+25 more)

### Community 9 - "test_media_reactions.py"
Cohesion: 0.08
Nodes (39): Message, MediaReactions, _message_contains_media(), Bot, Client, listener, Registra uma mensagem uma vez e limita o cache estritamente em memória., Registra o listener sem substituir o on_message do cliente principal. (+31 more)

### Community 10 - ".from_environment"
Cohesion: 0.08
Nodes (52): _boolean(), ConfigurationError, _https_url(), _instagram_api_version(), _log_level(), _numeric_id(), _optional_https_url(), _optional_iso_datetime() (+44 more)

### Community 11 - "DiscordNotificationSender"
Cohesion: 0.09
Nodes (21): File, Expõe o remetente compartilhado para extensões do bot., DiscordNotificationSender, Embed, Member, Path, User, Escolhe uma imagem aleatória para a notificação da Twitch. (+13 more)

### Community 12 - "YouTubeAudioService"
Cohesion: 0.06
Nodes (37): is_valid_youtube_url(), normalize_youtube_video_url(), Any, RuntimeError, Extração segura de URLs temporárias de áudio do YouTube, sem downloads., Executa a parte bloqueante do yt-dlp fora do loop assíncrono., Importa yt-dlp apenas quando a integração for efetivamente usada., Retorna somente o host, seguro para logs. (+29 more)

### Community 13 - "test_cleanup_command.py"
Cohesion: 0.09
Nodes (28): cleanup_cog(), discord_error(), FakeChannel, FakeFollowup, FakeInteraction, FakeNotificationSender, FakeResponse, asyncio (+20 more)

### Community 14 - "test_music.py"
Cohesion: 0.07
Nodes (38): FakeVoiceChannel, FailingVoiceChannel, FakeBot, FakeFollowup, FakeGuild, FakeInteraction, FakeMember, FakeResponse (+30 more)

### Community 15 - "Music"
Cohesion: 0.06
Nodes (33): AbstractEventLoop, Connectable, describe, Music, Bot, command, Exception, Guild (+25 more)

### Community 16 - "InstagramTokenData"
Cohesion: 0.10
Nodes (12): JsonFileInstagramTokenStore, Persiste token em JSON atômico, fora do Git e com modo 0600 em sistemas POSIX., Lê o JSON persistido; usa o ambiente apenas quando ainda não há arquivo., Grava uma resposta completa de modo atômico e atualiza o fallback em memória., Retorna o token atual e seus metadados, quando estiver configurado., Persiste um token recém-autorizado sem registrá-lo em logs., Retorna o token em memória para testes unitários isolados., Substitui o token em memória depois de validá-lo. (+4 more)

### Community 17 - "test_instagram.py"
Cohesion: 0.20
Nodes (20): FakeRefreshClient, FakeTokenStore, instagram_refresh_environment(), datetime, Testes sem rede para cliente e polling da API oficial do Instagram., Armazena o token em memória para testar a tarefa sem persistência externa., Registra chamadas de renovação e devolve um resultado controlado., Cria token de teste sem usar credenciais reais. (+12 more)

### Community 18 - "InstagramTokenRefreshTask"
Cohesion: 0.15
Nodes (9): InstagramTokenRefreshTask, datetime, Executa verificações periódicas sem repetir em ciclo rápido após uma falha., Verifica e renova token uma vez por janela, sem derrubar o bot em falhas., Informa a última tentativa sem expor informações secretas., Informa o resultado seguro mais recente da renovação., Inicia uma única tarefa se Instagram e renovação automática estiverem ativos., Cancela e aguarda a tarefa para não deixar trabalho pendente no desligamento. (+1 more)

### Community 19 - ".refresh_access_token"
Cohesion: 0.22
Nodes (5): Descarta apenas o token que gerou a falha, preservando renovação concorrente., Obtém token novo, valida-o e resolve o perfil antes de usar EventSub., Obtém um token novo uma única vez mesmo sob chamadas concorrentes., Retorna um token válido, renovando-o pouco antes do vencimento., Valida o token atual e, se permitido, o emite uma vez mais quando inválido.

### Community 20 - "test_twitch.py"
Cohesion: 0.16
Nodes (20): oauth_token_response(), asyncio, Response, Testes sem rede para Helix e EventSub com token Twitch renovável., Uma chamada GET recebe um token novo e é repetida uma única vez após HTTP 401., A ausência de dados de stream permite limpar a live atual sem notificar…, Retorna uma resposta OAuth curta e válida para os transportes simulados., EventSub consulta inscrições depois de 401 para não criar uma duplicata. (+12 more)

### Community 21 - "test_sends_instagram_post_content_and_link_button"
Cohesion: 0.15
Nodes (16): InstagramNotificationView, View com botão para abrir a publicação original no Instagram., FakeChannel, FakeDiscordClient, instagram_environment(), asyncio, Testes do envio de embeds Discord sem conexão externa., Um ID que não resolve para canal de mensagens não é aceito. (+8 more)

### Community 22 - "test_run_services_composes_single_bot_and_cleans_up_tasks"
Cohesion: 0.10
Nodes (11): FakeBot, FakeServer, FakeStore, asyncio, MonkeyPatch, Testes da composição integrada sem conectar Discord, Twitch ou Uvicorn reais., Store sem I/O para confirmar que a composição cria apenas uma instância., Bot mínimo que permanece ativo até o desligamento coordenado. (+3 more)

### Community 23 - "MemberActivityLogs"
Cohesion: 0.13
Nodes (17): AllowedMentions, MemberActivityLogs, Any, listener, Member, Publica eventos de entrada e saída no canal de auditoria configurado., Registra a entrada de um membro no servidor., Registra a saída de um membro do servidor. (+9 more)

### Community 24 - "CommandAccessTree"
Cohesion: 0.14
Nodes (15): CommandAccessTree, Interaction, Controle global de acesso aos comandos slash por cargo Discord., Impede a execução de slash commands por membros sem o cargo configurado., Valida o cargo antes de qualquer comando registrado na árvore., FakeResponse, make_interaction(), SimpleNamespace (+7 more)

### Community 25 - "TwitchClient"
Cohesion: 0.11
Nodes (15): Configurações necessárias para o EventSub da Twitch., TwitchSettings, AsyncClient, Cliente assíncrono da API Helix e do EventSub da Twitch., Expõe somente o ID já resolvido, sem I/O na rota do webhook., Acessa Helix/EventSub com token renovável e restrito à memória do processo., Descarta o token em memória e fecha somente recursos próprios., TwitchClient (+7 more)

### Community 26 - "InstagramTokenStore"
Cohesion: 0.10
Nodes (19): OAuth do Instagram Login para autorizar uma conta profissional sem expor…, InstagramTokenStore, Contrato para obter e salvar tokens sem acoplar o cliente à infraestrutura., create_web_app(), FastAPI, Fábrica da aplicação FastAPI usada pelo webhook da Twitch., Cria o servidor HTTP sem instanciar um segundo cliente Discord., create_instagram_oauth_router() (+11 more)

### Community 27 - ".resend_instagram_post_command"
Cohesion: 0.18
Nodes (14): default_permissions, command, guild_only, has_permissions, Interaction, User, Responde a um teste simples de conectividade., Dispara uma DM de boas-vindas para o usuário selecionado. (+6 more)

### Community 28 - "NotificationStore"
Cohesion: 0.11
Nodes (11): Connection, Enfileira um evento EventSub sem bloquear a resposta HTTP da Twitch., Evento ``stream.online`` recebido pelo webhook EventSub., TwitchOnlineEvent, NotificationStore, Path, Persiste identificadores processados para evitar notificações duplicadas., Cria as tabelas e índices necessários, caso ainda não existam. (+3 more)

### Community 29 - "generate_deployment_article_pdf.py"
Cohesion: 0.14
Nodes (19): article_sections(), build_article_text(), create_pdf(), https_url(), main(), page_number(), parse_arguments(), Namespace (+11 more)

### Community 30 - "main.py"
Cohesion: 0.14
Nodes (17): Server, configure_logging(), Configuração centralizada de logs., Configura logs para o terminal sem registrar dados sensíveis., main(), _prepare_instagram_client(), _prepare_twitch_client(), Ponto de entrada que supervisiona o bot Discord e o servidor FastAPI. (+9 more)

### Community 31 - "test_instagram_oauth.py"
Cohesion: 0.11
Nodes (19): FakeBot, FakeOAuthService, oauth_environment(), asyncio, Testes do Instagram Login sem chamadas à Meta, Discord ou rede real., Uma autorização de outro perfil não sobrescreve o armazenamento atual., State inválido, replay e erro da Meta não liberam detalhes ao navegador., Um callback válido é aceito uma vez e sua repetição é bloqueada. (+11 more)

### Community 32 - "Configuração"
Cohesion: 0.10
Nodes (19): API FastAPI local, Autorizar a conta, Canais de voz temporários, Cargos automáticos e por reação, Comandos Discord, Configuração, Discord, Discord Bot: Twitch e Instagram (+11 more)

### Community 33 - "client.py"
Cohesion: 0.08
Nodes (22): Cliente principal do bot do Discord., Expõe o cliente Instagram compartilhado para comandos administrativos., InstagramSettings, Configurações para a consulta oficial de mídia do Instagram., Indica se as três credenciais necessárias para OAuth foram informadas., Indica se há dados mínimos no ambiente para iniciar polling imediatamente., InstagramClient, Consulta perfis e mídias, sempre usando o token atual do armazenamento… (+14 more)

### Community 34 - "twitch_auth.py"
Cohesion: 0.15
Nodes (17): Any, Response, Autenticação OAuth de App Access Token da Twitch, somente em memória., Confirma com a Twitch se um token ainda pode ser usado., Repete somente falhas transitórias de rede ou servidor, sem registrar segredos., Falha ao autenticar a aplicação Twitch., Client ID ou Client Secret foram recusados pela Twitch., Token Twitch inválido, expirado ou com resposta de validação incorreta. (+9 more)

### Community 35 - "InstagramMedia"
Cohesion: 0.11
Nodes (18): InstagramMedia, Representa uma mídia retornada pela API Graph do Instagram., Registra uma mídia depois de conhecida ou enviada com sucesso., FailingSender, FakeInstagramClient, FakeSender, Path, O backend local grava token e expiração em JSON fora do repositório. (+10 more)

### Community 36 - "instagram_token_store.py"
Cohesion: 0.12
Nodes (19): AwsSecretsManagerInstagramTokenStore, AwsSecretsManagerSecretStore, create_instagram_token_store(), InstagramTokenStoreError, _parse_expires_at(), Any, datetime, RuntimeError (+11 more)

### Community 37 - "CurrentTwitchLiveStore"
Cohesion: 0.20
Nodes (5): Expõe o estado em memória da última live Twitch ainda aberta., CurrentTwitchLiveStore, Mantém uma única live atual com leituras e alterações consistentes. O conteúdo…, Retorna um instantâneo imutável da live atualmente aberta., Limpa o estado somente se ele ainda corresponder ao instantâneo recebido.

### Community 38 - "asyncio"
Cohesion: 0.13
Nodes (16): instagram_environment(), asyncio, Erros de autenticação são convertidos em exceções seguras., A renovação usa GET, grant_type oficial e calcula a expiração em UTC., Token expirado pede reautorização e nunca reproduz o valor secreto no erro., Uma falha 5xx tem repetição limitada antes de aceitar a resposta oficial válida., Consultas posteriores usam o token salvo após renovação, sem reiniciar o bot., Ativa a integração Instagram com valores de teste não secretos. (+8 more)

### Community 39 - "test_web_app_exposes_health_and_initializes_shared_store"
Cohesion: 0.17
Nodes (11): FakeBot, asyncio, Testes da fábrica FastAPI e do seu lifespan sem iniciar Discord real., Representa a única instância compartilhada recebida pela fábrica web., Atende ao contrato da rota sem criar um cliente Discord., Registra a inicialização do armazenamento pelo lifespan da aplicação., A fábrica não instancia Discord e usa o store recebido durante o lifespan., A API de saúde continua disponível sem expor rota Twitch quando ela está… (+3 more)

### Community 40 - "InstagramOAuthClient"
Cohesion: 0.10
Nodes (17): Cancela tarefas e fecha clientes auxiliares antes de encerrar o Discord., InstagramOAuthClient, InstagramOAuthError, InstagramOAuthStateStore, Any, AsyncClient, datetime, RuntimeError (+9 more)

### Community 41 - "._request"
Cohesion: 0.17
Nodes (9): Any, Response, Busca o título atual da live para enriquecer uma notificação., Obtém inscrições EventSub para detectar duplicidades antes de criar uma nova., Monta o payload EventSub conforme o contrato ``stream.online`` v1., Cria EventSub sem duplicar uma inscrição após uma renovação de token., Executa Helix com uma única renovação segura após HTTP 401 quando aplicável., Indica um HTTP 401 da API Helix, sem incluir dados sensíveis. (+1 more)

### Community 42 - "test_retries_transient_token_endpoint_failure"
Cohesion: 0.20
Nodes (11): asyncio, Testes unitários do OAuth de App Access Token Twitch, sem rede externa., O token recebido inclui vencimento calculado e não depende de variável legada., Falha HTTP 5xx é repetida de forma limitada antes de aceitar a resposta válida., O endpoint OAuth de validação sinaliza token inválido sem expor seu valor., Credenciais recusadas geram erro claro sem revelar o segredo configurado., test_invalid_client_error_does_not_include_client_secret(), test_requests_token_with_expiration_in_memory() (+3 more)

### Community 43 - "generate_deployment_article.py"
Cohesion: 0.22
Nodes (12): build_article(), _https_url(), main(), parse_arguments(), Namespace, Lê os links públicos e o destino sem incluir dados sensíveis., Gera o arquivo e informa uma contagem de palavras verificável., Valida links públicos sem fazer requisições de rede. (+4 more)

### Community 44 - "models.py"
Cohesion: 0.13
Nodes (15): Comandos gerais do bot., CurrentTwitchLive, Estado em memória da última live Twitch confirmada como aberta., Combina o evento EventSub e os dados mais recentes de uma live aberta., Registra a live somente se a API Twitch a confirmou como online., Atualiza dados da live sem sobrescrever uma live que chegou depois. Retorna…, DiscordNotificationError, RuntimeError (+7 more)

### Community 45 - "instagram.py"
Cohesion: 0.18
Nodes (17): InstagramAuthenticationError, InstagramTokenExpiredError, InstagramTokenRefreshError, InstagramTokenRevokedError, AsyncClient, Response, Cliente da API oficial Instagram Graph e renovação segura de token., Classifica falhas de autorização sem incluir a resposta nem o token na exceção. (+9 more)

### Community 46 - "FakeInteractionResponse"
Cohesion: 0.18
Nodes (5): FakeFollowup, FakeInteractionResponse, Embed, Captura a resposta inicial da interação slash., Captura as respostas posteriores ao defer.

### Community 47 - "TwitchError"
Cohesion: 0.20
Nodes (7): RuntimeError, Erro seguro e genérico de uma integração com a Twitch., Falha segura em uma chamada à API Helix ou EventSub., TwitchApiError, TwitchError, Busca ID, login e nome exibido de um perfil pelo login., Obtém o ID do perfil configurado e o reutiliza apenas em memória.

### Community 48 - "handle_app_command_error"
Cohesion: 0.32
Nodes (7): AppCommandError, handle_app_command_error(), Interaction, Tratamento de erros de comandos de aplicativo., Registra um erro técnico e envia uma mensagem segura ao usuário., Envia uma resposta efêmera, inclusive após uma resposta já iniciada., _send_error_message()

### Community 49 - "._parse_media"
Cohesion: 0.25
Nodes (5): Any, datetime, Converte uma resposta parcial em um modelo tolerante a campos opcionais., Interpreta timestamps ISO 8601 e mantém o bot resiliente a campo ausente., Converte campos opcionais da API em strings, quando disponíveis.

### Community 50 - "test_validator_validates_once_and_stops_cleanly"
Cohesion: 0.28
Nodes (6): FakeTwitchClient, asyncio, Testes do ciclo de vida do validador periódico de token Twitch., Cliente mínimo que registra validações sem chamadas HTTP., A tarefa pode ser iniciada uma vez e cancelada sem deixar trabalho pendente., test_validator_validates_once_and_stops_cleanly()

### Community 51 - "FakeInstagramClient"
Cohesion: 0.29
Nodes (8): FakeInstagramClient, latest_instagram_media(), Cria a publicação usada nos testes do reenvio Instagram., O reenvio manual usa o remetente existente e o Reel mais recente da API., Falhas técnicas não são reveladas ao administrador., Retorna uma mídia controlada sem chamar a API Instagram., test_resend_instagram_reel_handles_api_and_discord_errors(), test_resend_instagram_reel_sends_latest_reel_without_changing_poller_state()

### Community 52 - "SecretStore"
Cohesion: 0.25
Nodes (5): Protocol, Contrato mínimo para um serviço gerenciado de segredos., Lê o valor de um segredo pelo identificador configurado., Atualiza o valor de um segredo pelo identificador configurado., SecretStore

### Community 53 - "environment"
Cohesion: 0.33
Nodes (4): fixture, environment(), Fixtures compartilhadas, sem credenciais reais., Fornece o mínimo de configuração válida para os testes.

### Community 54 - "Settings"
Cohesion: 0.06
Nodes (32): DiscordBot, Carrega extensões e sincroniza comandos antes de conectar ao gateway., Registra a conexão e inicia serviços que dependem do cliente pronto., Entrega eventos Twitch após o cliente Discord ficar disponível., Cliente Discord com comandos slash e o comando prefixado de moderação., Reações automáticas para mídias enviadas em um canal configurado., Bot, Logs configuráveis de entrada e saída de membros. (+24 more)

### Community 55 - ".__init__"
Cohesion: 0.33
Nodes (3): Client, View com botão de acesso à live da Twitch., TwitchNotificationView

### Community 56 - "test_poller_logs_do_not_include_instagram_token"
Cohesion: 0.33
Nodes (5): LogCaptureFixture, FailingInstagramClient, Simula uma falha segura da API sem carregar detalhes de requisição., Erros recuperáveis do polling não podem vazar o token configurado., test_poller_logs_do_not_include_instagram_token()

### Community 57 - "ValueError"
Cohesion: 0.50
Nodes (3): AsyncClient, datetime, ValueError

### Community 62 - "General"
Cohesion: 0.20
Nodes (8): General, Bot, Identifica Reels pelo tipo de produto oficial, com fallback compatível., Identifica posts de feed e exclui Reels explicitamente., Obtém a live atual e confirma que ela ainda está online antes do reenvio., Registra o cog de comandos gerais na extensão., Agrupa comandos slash de uso geral., setup()

### Community 64 - "RoleMenuSettings"
Cohesion: 0.50
Nodes (3): Configuração opcional dos cargos automáticos e menus por reação., Indica se há ao menos uma mensagem de reação configurada., RoleMenuSettings

### Community 71 - "InstagramTokenRefreshResult"
Cohesion: 0.40
Nodes (4): Usa o mesmo cliente HTTP para renovar um token ainda válido., InstagramTokenRefreshResult, Resultado seguro de uma renovação bem-sucedida de token Instagram., Exception

### Community 73 - "InstagramTokenRefreshClient"
Cohesion: 0.40
Nodes (4): InstagramTokenRefreshClient, Protocol, Parte do cliente Instagram necessária para a tarefa de renovação., Renova um token atual no endpoint oficial.

## Knowledge Gaps
- **17 isolated node(s):** `discord-bot`, `Requisitos`, `Instalação`, `API FastAPI local`, `Discord` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 762 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `test_role_management.py`, `test_temporary_voice.py`, `routes.py`, `test_welcome.py`, `test_config.py`, `TemporaryVoice`, `test_media_reactions.py`, `.from_environment`, `DiscordNotificationSender`, `Music`, `test_instagram.py`, `test_twitch.py`, `test_sends_instagram_post_content_and_link_button`, `test_run_services_composes_single_bot_and_cleans_up_tasks`, `MemberActivityLogs`, `InstagramTokenStore`, `main.py`, `test_instagram_oauth.py`, `client.py`, `InstagramMedia`, `asyncio`, `test_web_app_exposes_health_and_initializes_shared_store`, `test_retries_transient_token_endpoint_failure`, `models.py`, `test_validator_validates_once_and_stops_cleanly`, `.__init__`, `test_poller_logs_do_not_include_instagram_token`?**
  _High betweenness centrality (0.252) - this node is a cross-community bridge._
- **Why does `DiscordBot` connect `Settings` to `client.py`, `routes.py`, `CurrentTwitchLiveStore`, `InstagramOAuthClient`, `test_media_reactions.py`, `TemporaryVoice`, `DiscordNotificationSender`, `models.py`, `Music`, `InstagramTokenRefreshTask`, `main.py`, `CommandAccessTree`, `TwitchClient`, `InstagramTokenStore`, `NotificationStore`, `General`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `Music` connect `Music` to `YouTubeAudioService`, `Settings`, `test_music.py`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Are the 85 inferred relationships involving `Settings` (e.g. with `DiscordBot` and `MediaReactions`) actually correct?**
  _`Settings` has 85 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `General` (e.g. with `CurrentTwitchLive` and `CurrentTwitchLiveStore`) actually correct?**
  _`General` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `DiscordBot` (e.g. with `CommandAccessTree` and `Settings`) actually correct?**
  _`DiscordBot` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `TwitchClient` (e.g. with `DiscordBot` and `General`) actually correct?**
  _`TwitchClient` has 15 INFERRED edges - model-reasoned connections that need verification._