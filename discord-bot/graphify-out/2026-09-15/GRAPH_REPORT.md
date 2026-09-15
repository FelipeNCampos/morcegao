# Graph Report - discord-bot  (2026-09-14)

## Corpus Check
- 61 files · ~424,114 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 1581 nodes · 3223 edges · 80 communities (65 shown, 14 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 343 edges (avg confidence: 0.94)
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
- .from_environment
- DiscordNotificationSender
- Music
- test_cleanup_command.py
- test_music.py
- .play_youtube
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
- create_instagram_oauth_router
- General
- InstagramMedia
- generate_deployment_article_pdf.py
- create_web_app
- test_instagram_oauth.py
- Configuração
- DiscordBot
- twitch_auth.py
- test_call_moderator.py
- instagram_token_store.py
- CurrentTwitchLiveStore
- test_youtube_audio.py
- test_web_app_exposes_health_and_initializes_shared_store
- InstagramOAuthClient
- TwitchError
- test_retries_transient_token_endpoint_failure
- generate_deployment_article.py
- FakeVoiceClient
- instagram_token_refresh.py
- FakeInteractionResponse
- InstagramSettings
- test_oauth_rejects_an_account_other_than_the_configured_profile
- FakeResponse
- test_validator_validates_once_and_stops_cleanly
- FakeInstagramClient
- AwsSecretsManagerInstagramTokenStore
- environment
- ._run_twitch_notification_worker
- ValueError
- InstagramOAuthStateStore
- .on_voice_state_update
- .expires_soon
- ._run
- FakeSecretStore
- .close
- ._is_instagram_post
- ._schedule_idle_from_audio_thread
- RoleMenuSettings
- RoleReactionOption
- test_resend_instagram_post_sends_latest_feed_post
- cogs/__init__.py
- bot/__init__.py
- integrations/__init__.py
- setup
- .refresh_access_token
- tasks/__init__.py
- InstagramTokenRefreshClient
- web/__init__.py
- test_general_cog_does_not_register_duplicate_slash_commands
- discord-bot
- role_settings
- test_builds_stream_online_eventsub_payload

## God Nodes (most connected - your core abstractions)
1. `Settings` - 106 edges
2. `General` - 48 edges
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
- `test_cleanup_handles_discord_failures()` --uses--> `General`  [INFERRED]
  tests/test_cleanup_command.py → src/bot/cogs/general.py
- `test_cleanup_is_registered_as_a_slash_command_and_purges_requested_messages()` --uses--> `General`  [INFERRED]
  tests/test_cleanup_command.py → src/bot/cogs/general.py

## Import Cycles
- None detected.

## Communities (80 total, 14 thin omitted)

### Community 0 - "InstagramAPIError"
Cohesion: 0.07
Nodes (29): InstagramAPIError, InstagramPermissionError, InstagramProfileNotFoundError, InstagramRateLimitError, InstagramTokenRefreshError, Any, AsyncClient, datetime (+21 more)

### Community 1 - "test_role_management.py"
Cohesion: 0.06
Nodes (43): discord_error(), FakeBot, FakeChannel, FakeGuild, FakeMember, FakeMessage, FakeRole, payload() (+35 more)

### Community 2 - "test_temporary_voice.py"
Cohesion: 0.06
Nodes (46): build_voice_fixture(), discord_error(), FakeBot, FakeCategory, FakeGuild, FakeMember, FakePrincipal, FakeRole (+38 more)

### Community 3 - "test_twitch_webhook.py"
Cohesion: 0.09
Nodes (33): create_twitch_router(), receive_twitch_webhook(), is_twitch_timestamp_fresh(), _parse_optional_timestamp(), _parse_twitch_online_event(), Any, APIRouter, datetime (+25 more)

### Community 4 - "test_welcome.py"
Cohesion: 0.06
Nodes (38): AppCommandError, handle_app_command_error(), Interaction, Tratamento de erros de comandos de aplicativo., Registra um erro técnico e envia uma mensagem segura ao usuário., Envia uma resposta efêmera, inclusive após uma resposta já iniciada., _send_error_message(), discord_error() (+30 more)

### Community 5 - "RoleManagement"
Cohesion: 0.07
Nodes (28): RawReactionActionEvent, Role, Bot, command, Guild, has_permissions, Interaction, listener (+20 more)

### Community 6 - "Settings"
Cohesion: 0.04
Nodes (64): Configuração tipada e segura para inicializar o bot., Settings, parametrize, Testes unitários da configuração do ambiente., Variáveis removidas não voltam a ativar opções de pronomes., A ausência de token Discord deve interromper a leitura da configuração., Os formatos booleanos aceitos devem ser interpretados corretamente., O controle de repetição Twitch usa os mesmos formatos booleanos aceitos. (+56 more)

### Community 7 - "test_live_commands.py"
Cohesion: 0.13
Nodes (30): Dados de uma live consultada após a notificação EventSub., TwitchStream, FakeInteraction, FakeNotificationSender, FakeTwitchClient, open_live(), asyncio, Testes dos comandos slash de reenvio de live e lista de comandos. (+22 more)

### Community 8 - "TemporaryVoice"
Cohesion: 0.07
Nodes (33): Snowflake, Bot, Client, Guild, GuildChannel, listener, Lock, Member (+25 more)

### Community 9 - "test_media_reactions.py"
Cohesion: 0.08
Nodes (39): Message, MediaReactions, _message_contains_media(), Bot, Client, listener, Registra uma mensagem uma vez e limita o cache estritamente em memória., Registra o listener sem substituir o on_message do cliente principal. (+31 more)

### Community 10 - ".from_environment"
Cohesion: 0.10
Nodes (45): _boolean(), ConfigurationError, _https_url(), _instagram_api_version(), _log_level(), _numeric_id(), _optional_https_url(), _optional_iso_datetime() (+37 more)

### Community 11 - "DiscordNotificationSender"
Cohesion: 0.08
Nodes (24): File, Expõe o remetente compartilhado para extensões do bot., DiscordNotificationError, DiscordNotificationSender, Embed, Member, Path, RuntimeError (+16 more)

### Community 12 - "Music"
Cohesion: 0.08
Nodes (28): Music, Bot, Comandos de reprodução de áudio do YouTube por guild., Toca uma faixa por vez, com locks e timeout independentes por guild., Registra os comandos de música no cliente Discord existente., Cancela timeouts pendentes quando a extensão for descarregada., setup(), is_valid_youtube_url() (+20 more)

### Community 13 - "test_cleanup_command.py"
Cohesion: 0.09
Nodes (28): cleanup_cog(), discord_error(), FakeChannel, FakeFollowup, FakeInteraction, FakeNotificationSender, FakeResponse, asyncio (+20 more)

### Community 14 - "test_music.py"
Cohesion: 0.15
Nodes (25): FakeBot, FakeGuild, FakeInteraction, FakeMember, music_cog(), asyncio, MonkeyPatch, Testes sem Discord, FFmpeg ou YouTube reais para os comandos de música. (+17 more)

### Community 15 - ".play_youtube"
Cohesion: 0.10
Nodes (18): Connectable, describe, command, Guild, guild_only, Interaction, Lock, Para o áudio mantendo a conexão até o timeout de inatividade. (+10 more)

### Community 16 - "InstagramTokenData"
Cohesion: 0.13
Nodes (11): JsonFileInstagramTokenStore, Persiste token em JSON atômico, fora do Git e com modo 0600 em sistemas POSIX., Lê o JSON persistido; usa o ambiente apenas quando ainda não há arquivo., Grava uma resposta completa de modo atômico e atualiza o fallback em memória., Retorna o token atual e seus metadados, quando estiver configurado., Persiste um token recém-autorizado sem registrá-lo em logs., Valida uma resposta e preserva metadados ausentes de um token válido anterior., Substitui o token em memória depois de validá-lo. (+3 more)

### Community 17 - "test_instagram.py"
Cohesion: 0.06
Nodes (57): LogCaptureFixture, InstagramTokenRefreshResult, Resultado seguro de uma renovação bem-sucedida de token Instagram., FailingSender, FakeInstagramClient, FakeRefreshClient, FakeSender, FakeTokenStore (+49 more)

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
Cohesion: 0.10
Nodes (21): MemberActivityLogs, Any, Bot, listener, Member, Logs configuráveis de entrada e saída de membros., Publica eventos de entrada e saída no canal de auditoria configurado., Registra a entrada de um membro no servidor. (+13 more)

### Community 24 - "CommandAccessTree"
Cohesion: 0.14
Nodes (17): CommandAccessTree, Interaction, Controle global de acesso aos comandos slash por cargo Discord., Impede comandos restritos, preservando exceções públicas explícitas., Valida o cargo antes de qualquer comando registrado na árvore., FakeResponse, make_interaction(), SimpleNamespace (+9 more)

### Community 25 - "TwitchClient"
Cohesion: 0.11
Nodes (15): Configurações necessárias para o EventSub da Twitch., TwitchSettings, AsyncClient, Cliente assíncrono da API Helix e do EventSub da Twitch., Expõe somente o ID já resolvido, sem I/O na rota do webhook., Acessa Helix/EventSub com token renovável e restrito à memória do processo., Descarta o token em memória e fecha somente recursos próprios., TwitchClient (+7 more)

### Community 26 - "create_instagram_oauth_router"
Cohesion: 0.15
Nodes (9): create_instagram_oauth_router(), InstagramOAuthService, APIRouter, Protocol, Rotas HTTP do Instagram Login, isoladas do webhook da Twitch., Parte do cliente OAuth usada pela camada HTTP., Monta a URL de consentimento do Instagram., Troca o código por uma autorização persistida. (+1 more)

### Community 27 - "General"
Cohesion: 0.15
Nodes (18): default_permissions, General, command, guild_only, has_permissions, Interaction, User, Agrupa comandos slash de uso geral. (+10 more)

### Community 28 - "InstagramMedia"
Cohesion: 0.10
Nodes (12): Connection, Retorna a mídia mais recente, se a conta tiver conteúdo disponível., InstagramMedia, Representa uma mídia retornada pela API Graph do Instagram., NotificationStore, Path, Persiste identificadores processados para evitar notificações duplicadas., Cria as tabelas e índices necessários, caso ainda não existam. (+4 more)

### Community 29 - "generate_deployment_article_pdf.py"
Cohesion: 0.14
Nodes (19): article_sections(), build_article_text(), create_pdf(), https_url(), main(), page_number(), parse_arguments(), Namespace (+11 more)

### Community 30 - "create_web_app"
Cohesion: 0.10
Nodes (17): Server, configure_logging(), Configuração centralizada de logs., Configura logs para o terminal sem registrar dados sensíveis., main(), _prepare_twitch_client(), Permite iniciar o projeto com ``python -m bot``., Executa Discord e FastAPI no mesmo loop e garante encerramento coordenado. (+9 more)

### Community 31 - "test_instagram_oauth.py"
Cohesion: 0.15
Nodes (9): FakeBot, FakeOAuthService, Testes do Instagram Login sem chamadas à Meta, Discord ou rede real., Um callback válido é aceito uma vez e sua repetição é bloqueada., Implementa o contrato mínimo do armazenamento compartilhado do FastAPI., Evita criar um segundo cliente Discord ao construir o app HTTP., Representa a Meta para testar state e respostas HTTP da aplicação., test_oauth_callback_consumes_state_after_success() (+1 more)

### Community 32 - "Configuração"
Cohesion: 0.10
Nodes (20): API FastAPI local, Autorizar a conta, Canais de voz temporários, Cargos automáticos e por reação, Chamar moderador, Comandos Discord, Configuração, Discord (+12 more)

### Community 33 - "DiscordBot"
Cohesion: 0.08
Nodes (32): DiscordBot, Cliente principal do bot do Discord., Enfileira um evento EventSub sem bloquear a resposta HTTP da Twitch., Registra a conexão e inicia serviços que dependem do cliente pronto., Cliente Discord com comandos slash e o comando prefixado de moderação., Expõe o cliente Instagram compartilhado para comandos administrativos., Comandos gerais do bot., Reações automáticas para mídias enviadas em um canal configurado. (+24 more)

### Community 34 - "twitch_auth.py"
Cohesion: 0.13
Nodes (19): Any, AsyncClient, datetime, Response, Autenticação OAuth de App Access Token da Twitch, somente em memória., Confirma com a Twitch se um token ainda pode ser usado., Repete somente falhas transitórias de rede ou servidor, sem registrar segredos., Falha ao autenticar a aplicação Twitch. (+11 more)

### Community 35 - "test_call_moderator.py"
Cohesion: 0.10
Nodes (14): FakeDiscordClient, FakeFollowup, FakeInteraction, FakeModerator, FakeResponse, AllowedMentions, Testes do comando público /chamar., Registra respostas iniciais da interação. (+6 more)

### Community 36 - "instagram_token_store.py"
Cohesion: 0.16
Nodes (14): AwsSecretsManagerSecretStore, create_instagram_token_store(), InstagramTokenStoreError, _parse_expires_at(), Any, datetime, Path, RuntimeError (+6 more)

### Community 37 - "CurrentTwitchLiveStore"
Cohesion: 0.14
Nodes (10): Expõe o estado em memória da última live Twitch ainda aberta., Client, CurrentTwitchLive, CurrentTwitchLiveStore, Combina o evento EventSub e os dados mais recentes de uma live aberta., Mantém uma única live atual com leituras e alterações consistentes. O conteúdo…, Registra a live somente se a API Twitch a confirmou como online., Retorna um instantâneo imutável da live atualmente aberta. (+2 more)

### Community 38 - "test_youtube_audio.py"
Cohesion: 0.11
Nodes (16): FakeExtractor, asyncio, Exception, parametrize, Testes sem rede para validação e extração de áudio do YouTube., A extração não bloqueia o loop e retorna URL temporária apenas ao chamador…, Falhas do yt-dlp não vazam detalhes do vídeo nem do stream., Extrator controlado compatível com o context manager do yt-dlp. (+8 more)

### Community 39 - "test_web_app_exposes_health_and_initializes_shared_store"
Cohesion: 0.17
Nodes (11): FakeBot, asyncio, Testes da fábrica FastAPI e do seu lifespan sem iniciar Discord real., Representa a única instância compartilhada recebida pela fábrica web., Atende ao contrato da rota sem criar um cliente Discord., Registra a inicialização do armazenamento pelo lifespan da aplicação., A fábrica não instancia Discord e usa o store recebido durante o lifespan., A API de saúde continua disponível sem expor rota Twitch quando ela está… (+3 more)

### Community 40 - "InstagramOAuthClient"
Cohesion: 0.25
Nodes (8): InstagramOAuthClient, InstagramOAuthError, Any, RuntimeError, Erro seguro do fluxo OAuth, apropriado para uma resposta HTTP genérica., Executa Instagram Login, troca o código e salva apenas dados validados., Monta a URL de consentimento usando somente a permissão de leitura necessária., Troca code por token duradouro, valida a conta e persiste o resultado.

### Community 41 - "TwitchError"
Cohesion: 0.11
Nodes (16): RuntimeError, Erro seguro e genérico de uma integração com a Twitch., Falha segura em uma chamada à API Helix ou EventSub., TwitchApiError, TwitchError, Any, Response, Busca ID, login e nome exibido de um perfil pelo login. (+8 more)

### Community 42 - "test_retries_transient_token_endpoint_failure"
Cohesion: 0.20
Nodes (11): asyncio, Testes unitários do OAuth de App Access Token Twitch, sem rede externa., O token recebido inclui vencimento calculado e não depende de variável legada., Falha HTTP 5xx é repetida de forma limitada antes de aceitar a resposta válida., O endpoint OAuth de validação sinaliza token inválido sem expor seu valor., Credenciais recusadas geram erro claro sem revelar o segredo configurado., test_invalid_client_error_does_not_include_client_secret(), test_requests_token_with_expiration_in_memory() (+3 more)

### Community 43 - "generate_deployment_article.py"
Cohesion: 0.22
Nodes (12): build_article(), _https_url(), main(), parse_arguments(), Namespace, Lê os links públicos e o destino sem incluir dados sensíveis., Gera o arquivo e informa uma contagem de palavras verificável., Valida links públicos sem fazer requisições de rede. (+4 more)

### Community 44 - "FakeVoiceClient"
Cohesion: 0.12
Nodes (9): FakeVoiceChannel, FailingVoiceChannel, FakeVoiceChannel, FakeVoiceClient, MissingPyNaClChannel, Cliente de voz controlável que não reproduz áudio real., Canal de voz com conexão local controlada., Canal que simula a ausência da dependência de voz no host. (+1 more)

### Community 45 - "instagram_token_refresh.py"
Cohesion: 0.24
Nodes (9): InstagramAuthenticationError, InstagramTokenExpiredError, InstagramTokenRevokedError, Indica token inválido, expirado ou revogado., Indica que o token já expirou e precisa de nova autorização manual., Indica que o token foi revogado ou perdeu a autorização., Tarefa assíncrona para renovar tokens Instagram antes do vencimento., FailingInstagramClient (+1 more)

### Community 46 - "FakeInteractionResponse"
Cohesion: 0.18
Nodes (5): FakeFollowup, FakeInteractionResponse, Embed, Captura a resposta inicial da interação slash., Captura as respostas posteriores ao defer.

### Community 47 - "InstagramSettings"
Cohesion: 0.15
Nodes (10): InstagramSettings, Configurações para a consulta oficial de mídia do Instagram., Indica se as três credenciais necessárias para OAuth foram informadas., Indica se há dados mínimos no ambiente para iniciar polling imediatamente., OAuth do Instagram Login para autorizar uma conta profissional sem expor…, _fallback_token(), InMemoryInstagramTokenStore, Cria um valor inicial a partir do ambiente, sem gravá-lo em disco. (+2 more)

### Community 48 - "test_oauth_rejects_an_account_other_than_the_configured_profile"
Cohesion: 0.18
Nodes (10): MemoryTokenStore, oauth_environment(), asyncio, Uma autorização de outro perfil não sobrescreve o armazenamento atual., Armazena apenas dados de teste para verificar a persistência do callback., Habilita somente a configuração pública necessária para o OAuth de teste., O callback troca code, valida username e salva os dados sem revelar token., test_oauth_authorizes_expected_account_and_persists_complete_token() (+2 more)

### Community 49 - "FakeResponse"
Cohesion: 0.20
Nodes (4): FakeFollowup, FakeResponse, Registra respostas iniciais de uma interaction., Registra mensagens posteriores ao defer.

### Community 50 - "test_validator_validates_once_and_stops_cleanly"
Cohesion: 0.28
Nodes (6): FakeTwitchClient, asyncio, Testes do ciclo de vida do validador periódico de token Twitch., Cliente mínimo que registra validações sem chamadas HTTP., A tarefa pode ser iniciada uma vez e cancelada sem deixar trabalho pendente., test_validator_validates_once_and_stops_cleanly()

### Community 51 - "FakeInstagramClient"
Cohesion: 0.25
Nodes (8): FakeInstagramClient, latest_instagram_media(), Cria a publicação usada nos testes do reenvio Instagram., O reenvio manual usa o remetente existente e o Reel mais recente da API., Falhas técnicas não são reveladas ao administrador., Retorna uma mídia controlada sem chamar a API Instagram., test_resend_instagram_reel_handles_api_and_discord_errors(), test_resend_instagram_reel_sends_latest_reel_without_changing_poller_state()

### Community 52 - "AwsSecretsManagerInstagramTokenStore"
Cohesion: 0.15
Nodes (9): AwsSecretsManagerInstagramTokenStore, Protocol, Armazena a estrutura tipada do token em um único segredo JSON da AWS., Converte o segredo JSON em dados de token sem expor seu valor., Grava dados validados em JSON, sem logs ou arquivos públicos., Contrato mínimo para um serviço gerenciado de segredos., Lê o valor de um segredo pelo identificador configurado., Atualiza o valor de um segredo pelo identificador configurado. (+1 more)

### Community 53 - "environment"
Cohesion: 0.33
Nodes (4): fixture, environment(), Fixtures compartilhadas, sem credenciais reais., Fornece o mínimo de configuração válida para os testes.

### Community 55 - "ValueError"
Cohesion: 0.25
Nodes (5): Client, View com botão de acesso à live da Twitch., TwitchNotificationView, AsyncClient, ValueError

### Community 56 - "InstagramOAuthStateStore"
Cohesion: 0.28
Nodes (5): InstagramOAuthStateStore, datetime, Guarda estados de uso único somente pelo tempo necessário para o callback., Cria um state criptograficamente aleatório e registra sua expiração., Valida e remove o state, impedindo seu reuso.

### Community 57 - ".on_voice_state_update"
Cohesion: 0.25
Nodes (6): GuildChannel, listener, Member, VoiceState, Sai de uma sala sem humanos para não impedir a limpeza de salas temporárias., Verifica se há alguém além do bot na sala atual.

### Community 59 - "._run"
Cohesion: 0.33
Nodes (3): Inicia uma única tarefa de polling quando a integração está ativada., Consulta mídias recentes e envia cada publicação nova ainda pendente., Mantém o polling ativo sem derrubar o bot após uma falha recuperável.

### Community 61 - ".close"
Cohesion: 0.50
Nodes (3): Cancela tarefas e fecha clientes auxiliares antes de encerrar o Discord., Fecha o cliente HTTP privado quando o FastAPI encerrar., lifespan()

### Community 63 - "._schedule_idle_from_audio_thread"
Cohesion: 0.50
Nodes (3): AbstractEventLoop, Exception, Agenda a desconexão no loop correto após callback síncrono do player.

### Community 64 - "RoleMenuSettings"
Cohesion: 0.50
Nodes (3): Configuração opcional dos cargos automáticos e menus por reação., Indica se há ao menos uma mensagem de reação configurada., RoleMenuSettings

### Community 65 - "RoleReactionOption"
Cohesion: 0.50
Nodes (3): Vínculo seguro entre um emoji configurado e um cargo do Discord., Retorna chaves compatíveis com emojis Unicode e personalizados., RoleReactionOption

### Community 66 - "test_resend_instagram_post_sends_latest_feed_post"
Cohesion: 0.50
Nodes (4): latest_instagram_post(), Cria o post de feed usado nos testes do reenvio Instagram., O comando de post ignora Reels e reenvia apenas uma mídia de feed., test_resend_instagram_post_sends_latest_feed_post()

### Community 70 - "setup"
Cohesion: 0.67
Nodes (3): Bot, Registra o cog de comandos gerais na extensão., setup()

### Community 73 - "InstagramTokenRefreshClient"
Cohesion: 0.40
Nodes (4): InstagramTokenRefreshClient, Protocol, Parte do cliente Instagram necessária para a tarefa de renovação., Renova um token atual no endpoint oficial.

## Knowledge Gaps
- **18 isolated node(s):** `discord-bot`, `Requisitos`, `Instalação`, `API FastAPI local`, `Discord` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 781 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `test_temporary_voice.py`, `test_twitch_webhook.py`, `test_welcome.py`, `RoleManagement`, `TemporaryVoice`, `test_media_reactions.py`, `.from_environment`, `DiscordNotificationSender`, `Music`, `test_instagram.py`, `test_twitch.py`, `test_sends_instagram_post_content_and_link_button`, `test_run_services_composes_single_bot_and_cleans_up_tasks`, `MemberActivityLogs`, `create_web_app`, `test_instagram_oauth.py`, `DiscordBot`, `test_web_app_exposes_health_and_initializes_shared_store`, `test_retries_transient_token_endpoint_failure`, `test_oauth_rejects_an_account_other_than_the_configured_profile`, `test_validator_validates_once_and_stops_cleanly`, `ValueError`, `role_settings`, `test_builds_stream_online_eventsub_payload`?**
  _High betweenness centrality (0.232) - this node is a cross-community bridge._
- **Why does `DiscordBot` connect `DiscordBot` to `test_twitch_webhook.py`, `CurrentTwitchLiveStore`, `Settings`, `setup`, `RoleManagement`, `test_media_reactions.py`, `TemporaryVoice`, `DiscordNotificationSender`, `Music`, `InstagramTokenRefreshTask`, `._run_twitch_notification_worker`, `CommandAccessTree`, `TwitchClient`, `InstagramMedia`, `.close`, `create_web_app`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Why does `Music` connect `Music` to `DiscordBot`, `Settings`, `test_music.py`, `.play_youtube`, `.on_voice_state_update`, `._schedule_idle_from_audio_thread`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 86 inferred relationships involving `Settings` (e.g. with `DiscordBot` and `MediaReactions`) actually correct?**
  _`Settings` has 86 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `General` (e.g. with `CurrentTwitchLive` and `CurrentTwitchLiveStore`) actually correct?**
  _`General` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `DiscordBot` (e.g. with `CommandAccessTree` and `Settings`) actually correct?**
  _`DiscordBot` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `TwitchClient` (e.g. with `DiscordBot` and `General`) actually correct?**
  _`TwitchClient` has 15 INFERRED edges - model-reasoned connections that need verification._