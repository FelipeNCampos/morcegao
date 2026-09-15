# Graph Report - discord-bot  (2026-09-15)

## Corpus Check
- 61 files · ~424,225 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 1586 nodes · 3237 edges · 83 communities (72 shown, 10 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 345 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6a8af796`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- InstagramAPIError
- test_role_management.py
- test_temporary_voice.py
- test_twitch_webhook.py
- test_welcome.py
- RoleManagement
- Settings
- test_live_commands.py
- TemporaryVoice
- test_media_reactions.py
- config.py
- DiscordNotificationError
- Music
- test_cleanup_command.py
- test_music.py
- .play_youtube
- InstagramTokenData
- InstagramTokenRefreshResult
- InstagramTokenRefreshTask
- .refresh_access_token
- test_twitch.py
- test_sends_instagram_post_content_and_link_button
- test_run_services_composes_single_bot_and_cleans_up_tasks
- MemberActivityLogs
- CommandAccessTree
- TwitchClient
- create_instagram_oauth_router
- General
- NotificationStore
- generate_deployment_article_pdf.py
- DiscordBot
- test_instagram_oauth.py
- Configuração
- InstagramClient
- TwitchAuthClient
- test_call_moderator.py
- AwsSecretsManagerSecretStore
- TwitchOnlineEvent
- test_youtube_audio.py
- test_web_app_exposes_health_and_initializes_shared_store
- InstagramOAuthClient
- ._request
- test_retries_transient_token_endpoint_failure
- generate_deployment_article.py
- FakeVoiceClient
- test_poller_logs_do_not_include_instagram_token
- FakeInteractionResponse
- MediaReactions
- test_oauth_rejects_an_account_other_than_the_configured_profile
- FakeResponse
- test_validator_validates_once_and_stops_cleanly
- FakeInstagramClient
- SecretStore
- environment
- ._run_twitch_notification_worker
- ValueError
- integrations/instagram_oauth.py
- .on_voice_state_update
- models.py
- ._run
- FakeSecretStore
- .close
- InstagramMedia
- youtube_audio.py
- RoleMenuSettings
- RoleReactionOption
- asyncio
- cogs/__init__.py
- bot/__init__.py
- integrations/__init__.py
- general.py
- DiscordNotificationSender
- tasks/__init__.py
- routes.py
- web/__init__.py
- .list_recent_media
- discord-bot
- test_instagram.py
- test_refreshes_access_token_with_official_endpoint
- .send_welcome_message
- member_activity_logs.py
- FakeFollowup

## God Nodes (most connected - your core abstractions)
1. `Settings` - 106 edges
2. `General` - 50 edges
3. `DiscordBot` - 44 edges
4. `TwitchClient` - 42 edges
5. `InstagramMedia` - 42 edges
6. `InstagramTokenData` - 40 edges
7. `ConfigurationError` - 37 edges
8. `InstagramClient` - 37 edges
9. `DiscordNotificationSender` - 36 edges
10. `NotificationStore` - 35 edges

## Surprising Connections (you probably didn't know these)
- `test_media_listener_is_unique_and_preserves_prefix_command_processing()` --uses--> `DiscordBot`  [INFERRED]
  tests/test_media_reactions.py → src/bot/client.py
- `test_call_moderator_is_disabled_without_a_configured_user()` --uses--> `General`  [INFERRED]
  tests/test_call_moderator.py → src/bot/cogs/general.py
- `test_call_moderator_sends_dm_to_fixed_configured_user()` --uses--> `General`  [INFERRED]
  tests/test_call_moderator.py → src/bot/cogs/general.py
- `test_user_id_command_returns_the_selected_user_id()` --uses--> `General`  [INFERRED]
  tests/test_call_moderator.py → src/bot/cogs/general.py
- `test_cleanup_handles_discord_failures()` --uses--> `General`  [INFERRED]
  tests/test_cleanup_command.py → src/bot/cogs/general.py

## Import Cycles
- None detected.

## Communities (83 total, 10 thin omitted)

### Community 0 - "InstagramAPIError"
Cohesion: 0.10
Nodes (22): InstagramAPIError, InstagramPermissionError, InstagramProfileNotFoundError, InstagramRateLimitError, InstagramTokenRefreshError, Any, AsyncClient, datetime (+14 more)

### Community 1 - "test_role_management.py"
Cohesion: 0.06
Nodes (45): discord_error(), FakeBot, FakeChannel, FakeGuild, FakeMember, FakeMessage, FakeRole, payload() (+37 more)

### Community 2 - "test_temporary_voice.py"
Cohesion: 0.06
Nodes (46): build_voice_fixture(), discord_error(), FakeBot, FakeCategory, FakeGuild, FakeMember, FakePrincipal, FakeRole (+38 more)

### Community 3 - "test_twitch_webhook.py"
Cohesion: 0.14
Nodes (22): create_twitch_router(), APIRouter, Monta a rota de webhook usando as dependências da única instância do bot., FakeBot, post_webhook(), asyncio, FastAPI, Path (+14 more)

### Community 4 - "test_welcome.py"
Cohesion: 0.06
Nodes (38): AppCommandError, handle_app_command_error(), Interaction, Tratamento de erros de comandos de aplicativo., Registra um erro técnico e envia uma mensagem segura ao usuário., Envia uma resposta efêmera, inclusive após uma resposta já iniciada., _send_error_message(), discord_error() (+30 more)

### Community 5 - "RoleManagement"
Cohesion: 0.07
Nodes (28): RawReactionActionEvent, Role, Bot, command, Guild, has_permissions, Interaction, listener (+20 more)

### Community 6 - "Settings"
Cohesion: 0.06
Nodes (61): Configuração tipada e segura para inicializar o bot., Cria as configurações a partir de variáveis de ambiente., Settings, parametrize, Testes unitários da configuração do ambiente., Variáveis removidas não voltam a ativar opções de pronomes., A ausência de token Discord deve interromper a leitura da configuração., Os formatos booleanos aceitos devem ser interpretados corretamente. (+53 more)

### Community 7 - "test_live_commands.py"
Cohesion: 0.11
Nodes (33): Envio seguro de notificações para canais do Discord., Dados de uma live consultada após a notificação EventSub., TwitchStream, FakeInteraction, FakeNotificationSender, FakeTwitchClient, open_live(), asyncio (+25 more)

### Community 8 - "TemporaryVoice"
Cohesion: 0.07
Nodes (30): Snowflake, Client, Guild, GuildChannel, listener, Lock, Member, PermissionOverwrite (+22 more)

### Community 9 - "test_media_reactions.py"
Cohesion: 0.12
Nodes (28): discord_error(), FakeAttachment, FakeMessage, media_cog(), media_reaction_settings(), asyncio, HTTPException, parametrize (+20 more)

### Community 10 - "config.py"
Cohesion: 0.08
Nodes (44): _boolean(), ConfigurationError, _https_url(), _instagram_api_version(), _log_level(), _numeric_id(), _optional_https_url(), _optional_iso_datetime() (+36 more)

### Community 11 - "DiscordNotificationError"
Cohesion: 0.13
Nodes (11): File, DiscordNotificationError, Embed, RuntimeError, Envia uma notificação para uma nova publicação do Instagram., Converte o tipo de produto Instagram em rótulo legível da notificação., Fornece a imagem local do gato quando o Reel não trouxer mídia da API., Indica que uma notificação não pôde ser entregue no Discord. (+3 more)

### Community 12 - "Music"
Cohesion: 0.11
Nodes (16): AbstractEventLoop, Music, Exception, Agenda a desconexão no loop correto após callback síncrono do player., Toca uma faixa por vez, com locks e timeout independentes por guild., Cancela timeouts pendentes quando a extensão for descarregada., Any, RuntimeError (+8 more)

### Community 13 - "test_cleanup_command.py"
Cohesion: 0.09
Nodes (28): cleanup_cog(), discord_error(), FakeChannel, FakeFollowup, FakeInteraction, FakeNotificationSender, FakeResponse, asyncio (+20 more)

### Community 14 - "test_music.py"
Cohesion: 0.17
Nodes (25): FakeBot, FakeGuild, FakeInteraction, FakeMember, music_cog(), asyncio, MonkeyPatch, Testes sem Discord, FFmpeg ou YouTube reais para os comandos de música. (+17 more)

### Community 15 - ".play_youtube"
Cohesion: 0.10
Nodes (18): Connectable, describe, command, Guild, guild_only, Interaction, Lock, Para o áudio mantendo a conexão até o timeout de inatividade. (+10 more)

### Community 16 - "InstagramTokenData"
Cohesion: 0.10
Nodes (21): AwsSecretsManagerInstagramTokenStore, InstagramTokenStoreError, JsonFileInstagramTokenStore, _parse_expires_at(), datetime, RuntimeError, Armazenamento seguro e intercambiável para tokens autorizados do Instagram., Persiste token em JSON atômico, fora do Git e com modo 0600 em sistemas POSIX. (+13 more)

### Community 17 - "InstagramTokenRefreshResult"
Cohesion: 0.16
Nodes (18): Usa o mesmo cliente HTTP para renovar um token ainda válido., InstagramTokenRefreshResult, Resultado seguro de uma renovação bem-sucedida de token Instagram., FakeRefreshClient, FakeTokenStore, instagram_refresh_environment(), Exception, Armazena o token em memória para testar a tarefa sem persistência externa. (+10 more)

### Community 18 - "InstagramTokenRefreshTask"
Cohesion: 0.09
Nodes (22): InstagramAuthenticationError, InstagramTokenExpiredError, InstagramTokenRevokedError, Classifica falhas de autorização sem incluir a resposta nem o token na exceção., Indica token inválido, expirado ou revogado., Indica que o token já expirou e precisa de nova autorização manual., Indica que o token foi revogado ou perdeu a autorização., _token_authentication_error() (+14 more)

### Community 19 - ".refresh_access_token"
Cohesion: 0.18
Nodes (6): Obtém o ID do perfil configurado e o reutiliza apenas em memória., Descarta apenas o token que gerou a falha, preservando renovação concorrente., Obtém token novo, valida-o e resolve o perfil antes de usar EventSub., Obtém um token novo uma única vez mesmo sob chamadas concorrentes., Retorna um token válido, renovando-o pouco antes do vencimento., Valida o token atual e, se permitido, o emite uma vez mais quando inválido.

### Community 20 - "test_twitch.py"
Cohesion: 0.14
Nodes (22): oauth_token_response(), asyncio, Response, Testes sem rede para Helix e EventSub com token Twitch renovável., Uma chamada GET recebe um token novo e é repetida uma única vez após HTTP 401., A ausência de dados de stream permite limpar a live atual sem notificar…, Retorna uma resposta OAuth curta e válida para os transportes simulados., EventSub consulta inscrições depois de 401 para não criar uma duplicata. (+14 more)

### Community 21 - "test_sends_instagram_post_content_and_link_button"
Cohesion: 0.16
Nodes (14): FakeChannel, FakeDiscordClient, instagram_environment(), asyncio, Testes do envio de embeds Discord sem conexão externa., Um ID que não resolve para canal de mensagens não é aceito., Canal que registra mensagens enviadas em memória., Cliente mínimo para testar busca de canal. (+6 more)

### Community 22 - "test_run_services_composes_single_bot_and_cleans_up_tasks"
Cohesion: 0.10
Nodes (11): FakeBot, FakeServer, FakeStore, asyncio, MonkeyPatch, Testes da composição integrada sem conectar Discord, Twitch ou Uvicorn reais., Store sem I/O para confirmar que a composição cria apenas uma instância., Bot mínimo que permanece ativo até o desligamento coordenado. (+3 more)

### Community 23 - "MemberActivityLogs"
Cohesion: 0.13
Nodes (17): MemberActivityLogs, Any, listener, Member, Publica eventos de entrada e saída no canal de auditoria configurado., Registra a entrada de um membro no servidor., Registra a saída de um membro do servidor., FakeBot (+9 more)

### Community 24 - "CommandAccessTree"
Cohesion: 0.14
Nodes (19): CommandAccessTree, Interaction, Controle global de acesso aos comandos slash por cargo Discord., Impede comandos restritos, preservando exceções públicas explícitas., Valida o cargo antes de qualquer comando registrado na árvore., FakeResponse, make_interaction(), SimpleNamespace (+11 more)

### Community 25 - "TwitchClient"
Cohesion: 0.12
Nodes (14): Configurações necessárias para o EventSub da Twitch., TwitchSettings, AsyncClient, Expõe somente o ID já resolvido, sem I/O na rota do webhook., Acessa Helix/EventSub com token renovável e restrito à memória do processo., Descarta o token em memória e fecha somente recursos próprios., TwitchClient, Validação periódica do App Access Token Twitch em memória. (+6 more)

### Community 26 - "create_instagram_oauth_router"
Cohesion: 0.15
Nodes (9): create_instagram_oauth_router(), InstagramOAuthService, APIRouter, Protocol, Rotas HTTP do Instagram Login, isoladas do webhook da Twitch., Parte do cliente OAuth usada pela camada HTTP., Monta a URL de consentimento do Instagram., Troca o código por uma autorização persistida. (+1 more)

### Community 27 - "General"
Cohesion: 0.14
Nodes (19): default_permissions, General, command, guild_only, has_permissions, Interaction, User, Agrupa comandos slash de uso geral. (+11 more)

### Community 28 - "NotificationStore"
Cohesion: 0.15
Nodes (7): Connection, NotificationStore, Path, Persiste identificadores processados para evitar notificações duplicadas., Cria as tabelas e índices necessários, caso ainda não existam., Atualiza o estado de envio de uma notificação Twitch., Informa se uma mídia já foi conhecida ou notificada.

### Community 29 - "generate_deployment_article_pdf.py"
Cohesion: 0.14
Nodes (19): article_sections(), build_article_text(), create_pdf(), https_url(), main(), page_number(), parse_arguments(), Namespace (+11 more)

### Community 30 - "DiscordBot"
Cohesion: 0.06
Nodes (39): Server, DiscordBot, Cliente principal do bot do Discord., Enfileira um evento EventSub sem bloquear a resposta HTTP da Twitch., Registra a conexão e inicia serviços que dependem do cliente pronto., Cliente Discord com comandos slash e o comando prefixado de moderação., Bot, Comandos de reprodução de áudio do YouTube por guild. (+31 more)

### Community 31 - "test_instagram_oauth.py"
Cohesion: 0.14
Nodes (13): FakeBot, FakeOAuthService, oauth_environment(), Testes do Instagram Login sem chamadas à Meta, Discord ou rede real., State inválido, replay e erro da Meta não liberam detalhes ao navegador., Um callback válido é aceito uma vez e sua repetição é bloqueada., Implementa o contrato mínimo do armazenamento compartilhado do FastAPI., Evita criar um segundo cliente Discord ao construir o app HTTP. (+5 more)

### Community 32 - "Configuração"
Cohesion: 0.10
Nodes (20): API FastAPI local, Autorizar a conta, Canais de voz temporários, Cargos automáticos e por reação, Chamar moderador, Comandos Discord, Configuração, Discord (+12 more)

### Community 33 - "InstagramClient"
Cohesion: 0.09
Nodes (21): Expõe o cliente Instagram compartilhado para comandos administrativos., InstagramSettings, Configurações para a consulta oficial de mídia do Instagram., Indica se as três credenciais necessárias para OAuth foram informadas., Indica se há dados mínimos no ambiente para iniciar polling imediatamente., InstagramClient, Cliente da API oficial Instagram Graph e renovação segura de token., Consulta perfis e mídias, sempre usando o token atual do armazenamento… (+13 more)

### Community 34 - "TwitchAuthClient"
Cohesion: 0.21
Nodes (10): Any, Response, Confirma com a Twitch se um token ainda pode ser usado., Repete somente falhas transitórias de rede ou servidor, sem registrar segredos., Token Twitch inválido, expirado ou com resposta de validação incorreta., Obtém e valida tokens OAuth sem persistir valores sensíveis., Fecha somente o cliente HTTP criado por esta instância., Solicita um novo App Access Token pelo fluxo client credentials. (+2 more)

### Community 35 - "test_call_moderator.py"
Cohesion: 0.10
Nodes (15): FakeDiscordClient, FakeFollowup, FakeInteraction, FakeModerator, FakeResponse, AllowedMentions, Testes do comando público /chamar., Registra respostas iniciais da interação. (+7 more)

### Community 36 - "AwsSecretsManagerSecretStore"
Cohesion: 0.25
Nodes (5): AwsSecretsManagerSecretStore, Any, Adaptador assíncrono para AWS Secrets Manager via IAM Role da instância EC2., Lê SecretString sem registrar seu conteúdo ou detalhes da resposta AWS., Persiste SecretString usando as permissões da IAM Role configurada.

### Community 37 - "TwitchOnlineEvent"
Cohesion: 0.11
Nodes (14): Expõe o estado em memória da última live Twitch ainda aberta., Client, CurrentTwitchLive, CurrentTwitchLiveStore, Estado em memória da última live Twitch confirmada como aberta., Combina o evento EventSub e os dados mais recentes de uma live aberta., Mantém uma única live atual com leituras e alterações consistentes. O conteúdo…, Registra a live somente se a API Twitch a confirmou como online. (+6 more)

### Community 38 - "test_youtube_audio.py"
Cohesion: 0.13
Nodes (13): FakeExtractor, asyncio, Exception, Testes sem rede para validação e extração de áudio do YouTube., A extração não bloqueia o loop e retorna URL temporária apenas ao chamador…, Falhas do yt-dlp não vazam detalhes do vídeo nem do stream., Extrator controlado compatível com o context manager do yt-dlp., O runtime Node instalado no host é habilitado explicitamente no yt-dlp. (+5 more)

### Community 39 - "test_web_app_exposes_health_and_initializes_shared_store"
Cohesion: 0.17
Nodes (11): FakeBot, asyncio, Testes da fábrica FastAPI e do seu lifespan sem iniciar Discord real., Representa a única instância compartilhada recebida pela fábrica web., Atende ao contrato da rota sem criar um cliente Discord., Registra a inicialização do armazenamento pelo lifespan da aplicação., A fábrica não instancia Discord e usa o store recebido durante o lifespan., A API de saúde continua disponível sem expor rota Twitch quando ela está… (+3 more)

### Community 40 - "InstagramOAuthClient"
Cohesion: 0.25
Nodes (8): InstagramOAuthClient, InstagramOAuthError, Any, RuntimeError, Erro seguro do fluxo OAuth, apropriado para uma resposta HTTP genérica., Executa Instagram Login, troca o código e salva apenas dados validados., Monta a URL de consentimento usando somente a permissão de leitura necessária., Troca code por token duradouro, valida a conta e persiste o resultado.

### Community 41 - "._request"
Cohesion: 0.16
Nodes (10): Falha segura em uma chamada à API Helix ou EventSub., TwitchApiError, Any, Response, Busca ID, login e nome exibido de um perfil pelo login., Busca o título atual da live para enriquecer uma notificação., Obtém inscrições EventSub para detectar duplicidades antes de criar uma nova., Monta o payload EventSub conforme o contrato ``stream.online`` v1. (+2 more)

### Community 42 - "test_retries_transient_token_endpoint_failure"
Cohesion: 0.20
Nodes (11): asyncio, Testes unitários do OAuth de App Access Token Twitch, sem rede externa., O token recebido inclui vencimento calculado e não depende de variável legada., Falha HTTP 5xx é repetida de forma limitada antes de aceitar a resposta válida., O endpoint OAuth de validação sinaliza token inválido sem expor seu valor., Credenciais recusadas geram erro claro sem revelar o segredo configurado., test_invalid_client_error_does_not_include_client_secret(), test_requests_token_with_expiration_in_memory() (+3 more)

### Community 43 - "generate_deployment_article.py"
Cohesion: 0.22
Nodes (12): build_article(), _https_url(), main(), parse_arguments(), Namespace, Lê os links públicos e o destino sem incluir dados sensíveis., Gera o arquivo e informa uma contagem de palavras verificável., Valida links públicos sem fazer requisições de rede. (+4 more)

### Community 44 - "FakeVoiceClient"
Cohesion: 0.10
Nodes (9): FakeVoiceChannel, FailingVoiceChannel, FakeVoiceChannel, FakeVoiceClient, MissingPyNaClChannel, Cliente de voz controlável que não reproduz áudio real., Canal de voz com conexão local controlada., Canal que simula a ausência da dependência de voz no host. (+1 more)

### Community 45 - "test_poller_logs_do_not_include_instagram_token"
Cohesion: 0.33
Nodes (5): LogCaptureFixture, FailingInstagramClient, Simula uma falha segura da API sem carregar detalhes de requisição., Erros recuperáveis do polling não podem vazar o token configurado., test_poller_logs_do_not_include_instagram_token()

### Community 46 - "FakeInteractionResponse"
Cohesion: 0.18
Nodes (5): FakeFollowup, FakeInteractionResponse, Embed, Captura a resposta inicial da interação slash., Captura as respostas posteriores ao defer.

### Community 47 - "MediaReactions"
Cohesion: 0.14
Nodes (14): Message, MediaReactions, _message_contains_media(), Bot, Client, listener, Reações automáticas para mídias enviadas em um canal configurado., Registra uma mensagem uma vez e limita o cache estritamente em memória. (+6 more)

### Community 48 - "test_oauth_rejects_an_account_other_than_the_configured_profile"
Cohesion: 0.20
Nodes (8): MemoryTokenStore, asyncio, Uma autorização de outro perfil não sobrescreve o armazenamento atual., Armazena apenas dados de teste para verificar a persistência do callback., O callback troca code, valida username e salva os dados sem revelar token., test_oauth_authorizes_expected_account_and_persists_complete_token(), handler(), test_oauth_rejects_an_account_other_than_the_configured_profile()

### Community 50 - "test_validator_validates_once_and_stops_cleanly"
Cohesion: 0.28
Nodes (6): FakeTwitchClient, asyncio, Testes do ciclo de vida do validador periódico de token Twitch., Cliente mínimo que registra validações sem chamadas HTTP., A tarefa pode ser iniciada uma vez e cancelada sem deixar trabalho pendente., test_validator_validates_once_and_stops_cleanly()

### Community 51 - "FakeInstagramClient"
Cohesion: 0.18
Nodes (12): FakeInstagramClient, latest_instagram_media(), latest_instagram_post(), Cria a publicação usada nos testes do reenvio Instagram., Cria o post de feed usado nos testes do reenvio Instagram., O reenvio manual usa o remetente existente e o Reel mais recente da API., O comando de post ignora Reels e reenvia apenas uma mídia de feed., Falhas técnicas não são reveladas ao administrador. (+4 more)

### Community 52 - "SecretStore"
Cohesion: 0.25
Nodes (5): Protocol, Contrato mínimo para um serviço gerenciado de segredos., Lê o valor de um segredo pelo identificador configurado., Atualiza o valor de um segredo pelo identificador configurado., SecretStore

### Community 53 - "environment"
Cohesion: 0.33
Nodes (4): fixture, environment(), Fixtures compartilhadas, sem credenciais reais., Fornece o mínimo de configuração válida para os testes.

### Community 55 - "ValueError"
Cohesion: 0.20
Nodes (7): InstagramNotificationView, Client, View com botão de acesso à live da Twitch., View com botão para abrir a publicação original no Instagram., TwitchNotificationView, AsyncClient, ValueError

### Community 56 - "integrations/instagram_oauth.py"
Cohesion: 0.24
Nodes (6): InstagramOAuthStateStore, datetime, OAuth do Instagram Login para autorizar uma conta profissional sem expor…, Guarda estados de uso único somente pelo tempo necessário para o callback., Cria um state criptograficamente aleatório e registra sua expiração., Valida e remove o state, impedindo seu reuso.

### Community 57 - ".on_voice_state_update"
Cohesion: 0.25
Nodes (6): GuildChannel, listener, Member, VoiceState, Sai de uma sala sem humanos para não impedir a limpeza de salas temporárias., Verifica se há alguém além do bot na sala atual.

### Community 58 - "models.py"
Cohesion: 0.22
Nodes (8): Cliente assíncrono da API Helix e do EventSub da Twitch., Indica um HTTP 401 da API Helix, sem incluir dados sensíveis., TwitchUnauthorizedError, datetime, Modelos tipados trocados entre integrações, armazenamento e tarefas., App Access Token Twitch mantido exclusivamente na memória do processo., Informa se o token deve ser renovado antes de uma nova chamada à API., TwitchToken

### Community 59 - "._run"
Cohesion: 0.33
Nodes (3): Inicia uma única tarefa de polling quando a integração está ativada., Consulta mídias recentes e envia cada publicação nova ainda pendente., Mantém o polling ativo sem derrubar o bot após uma falha recuperável.

### Community 61 - ".close"
Cohesion: 0.50
Nodes (3): Cancela tarefas e fecha clientes auxiliares antes de encerrar o Discord., Fecha o cliente HTTP privado quando o FastAPI encerrar., lifespan()

### Community 62 - "InstagramMedia"
Cohesion: 0.13
Nodes (13): Identifica Reels pelo tipo de produto oficial, com fallback compatível., Identifica posts de feed e exclui Reels explicitamente., InstagramMedia, Representa uma mídia retornada pela API Graph do Instagram., Registra uma mídia depois de conhecida ou enviada com sucesso., FakeInstagramClient, FakeSender, Retorna mídias controladas sem chamar a API real. (+5 more)

### Community 63 - "youtube_audio.py"
Cohesion: 0.13
Nodes (14): is_valid_youtube_url(), normalize_youtube_video_url(), Extração segura de URLs temporárias de áudio do YouTube, sem downloads., Metadados públicos e URL temporária usada somente pelo FFmpeg., Aceita links públicos que apontem para um vídeo específico do YouTube., Retorna a URL canônica de um vídeo e descarta parâmetros de playlist/rádio., YouTubeAudio, FakeAudioService (+6 more)

### Community 64 - "RoleMenuSettings"
Cohesion: 0.50
Nodes (3): Configuração opcional dos cargos automáticos e menus por reação., Indica se há ao menos uma mensagem de reação configurada., RoleMenuSettings

### Community 65 - "RoleReactionOption"
Cohesion: 0.50
Nodes (3): Vínculo seguro entre um emoji configurado e um cargo do Discord., Retorna chaves compatíveis com emojis Unicode e personalizados., RoleReactionOption

### Community 66 - "asyncio"
Cohesion: 0.21
Nodes (13): asyncio, datetime, Path, Cria token de teste sem usar credenciais reais., Consultas posteriores usam o token salvo após renovação, sem reiniciar o bot., O backend local grava token e expiração em JSON fora do repositório., O adaptador AWS usa o contrato de segredo injetado e preserva os metadados., A resposta oficial é convertida mesmo quando campos opcionais estão ausentes. (+5 more)

### Community 70 - "general.py"
Cohesion: 0.14
Nodes (14): Bot, Comandos gerais do bot., Registra o cog de comandos gerais na extensão., setup(), AsyncClient, datetime, RuntimeError, Autenticação OAuth de App Access Token da Twitch, somente em memória. (+6 more)

### Community 71 - "DiscordNotificationSender"
Cohesion: 0.22
Nodes (8): Expõe o remetente compartilhado para extensões do bot., DiscordNotificationSender, Path, Escolhe uma imagem aleatória para a notificação da Twitch., Escolhe uma imagem aleatória para a mensagem de boas-vindas., Envia uma notificação formatada para uma live iniciada., Envia notificações usando o cliente Discord já conectado., Escolhe aleatoriamente uma imagem compatível no diretório.

### Community 73 - "routes.py"
Cohesion: 0.22
Nodes (12): receive_twitch_webhook(), is_twitch_timestamp_fresh(), _parse_optional_timestamp(), _parse_twitch_online_event(), Any, datetime, Rotas FastAPI para notificações EventSub da Twitch., Converte um payload EventSub mínimo, tolerando campos opcionais. (+4 more)

### Community 75 - ".list_recent_media"
Cohesion: 0.20
Nodes (6): Monta a URL oficial para consultar o perfil autorizado., Monta a URL oficial para consultar mídias do perfil autorizado., Obtém os dados básicos do perfil profissional autorizado., Obtém até cinco páginas de mídias e converte campos opcionais com segurança., Retorna a mídia mais recente, se a conta tiver conteúdo disponível., Obtém o token atual sem propagar seu valor para logs ou erros.

### Community 78 - "test_instagram.py"
Cohesion: 0.21
Nodes (9): FailingSender, instagram_environment(), Testes sem rede para cliente e polling da API oficial do Instagram., Erros de autenticação são convertidos em exceções seguras., Ativa a integração Instagram com valores de teste não secretos., Simula uma falha Discord para verificar que a mídia continua pendente., Uma mídia só é marcada após a confirmação de envio ao Discord., test_poller_does_not_persist_media_when_discord_send_fails() (+1 more)

### Community 79 - "test_refreshes_access_token_with_official_endpoint"
Cohesion: 0.22
Nodes (7): A renovação usa GET, grant_type oficial e calcula a expiração em UTC., Token expirado pede reautorização e nunca reproduz o valor secreto no erro., Uma falha 5xx tem repetição limitada antes de aceitar a resposta oficial válida., handler(), test_refresh_reports_expired_token_without_exposing_it(), test_refresh_retries_only_transient_server_failure(), test_refreshes_access_token_with_official_endpoint()

### Community 80 - ".send_welcome_message"
Cohesion: 0.29
Nodes (5): Member, User, Envia por DM uma apresentação do Morcegão para o usuário., Obtém o nome atual de um canal ou retorna um fallback., Retorna o nome público mais adequado do usuário.

### Community 81 - "member_activity_logs.py"
Cohesion: 0.33
Nodes (4): Bot, Logs configuráveis de entrada e saída de membros., Registra o cog usando as configurações do cliente principal., setup()

## Knowledge Gaps
- **18 isolated node(s):** `discord-bot`, `Requisitos`, `Instalação`, `API FastAPI local`, `Discord` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 782 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `test_role_management.py`, `test_temporary_voice.py`, `test_twitch_webhook.py`, `test_welcome.py`, `RoleManagement`, `test_live_commands.py`, `TemporaryVoice`, `test_media_reactions.py`, `config.py`, `Music`, `InstagramTokenRefreshResult`, `test_twitch.py`, `test_sends_instagram_post_content_and_link_button`, `test_run_services_composes_single_bot_and_cleans_up_tasks`, `MemberActivityLogs`, `DiscordBot`, `test_instagram_oauth.py`, `InstagramClient`, `test_web_app_exposes_health_and_initializes_shared_store`, `test_retries_transient_token_endpoint_failure`, `test_poller_logs_do_not_include_instagram_token`, `MediaReactions`, `test_oauth_rejects_an_account_other_than_the_configured_profile`, `test_validator_validates_once_and_stops_cleanly`, `ValueError`, `InstagramMedia`, `asyncio`, `DiscordNotificationSender`, `routes.py`, `test_instagram.py`, `member_activity_logs.py`?**
  _High betweenness centrality (0.250) - this node is a cross-community bridge._
- **Why does `DiscordBot` connect `DiscordBot` to `InstagramClient`, `test_twitch_webhook.py`, `TwitchOnlineEvent`, `Settings`, `DiscordNotificationSender`, `general.py`, `RoleManagement`, `routes.py`, `test_media_reactions.py`, `Music`, `MediaReactions`, `InstagramTokenRefreshTask`, `._run_twitch_notification_worker`, `CommandAccessTree`, `TwitchClient`, `NotificationStore`, `.close`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `Music` connect `Music` to `Settings`, `test_music.py`, `.play_youtube`, `.on_voice_state_update`, `DiscordBot`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 86 inferred relationships involving `Settings` (e.g. with `DiscordBot` and `MediaReactions`) actually correct?**
  _`Settings` has 86 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `General` (e.g. with `CurrentTwitchLive` and `CurrentTwitchLiveStore`) actually correct?**
  _`General` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `DiscordBot` (e.g. with `CommandAccessTree` and `Settings`) actually correct?**
  _`DiscordBot` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `TwitchClient` (e.g. with `DiscordBot` and `General`) actually correct?**
  _`TwitchClient` has 15 INFERRED edges - model-reasoned connections that need verification._