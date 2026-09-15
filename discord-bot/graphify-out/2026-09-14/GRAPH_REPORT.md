# Graph Report - discord-bot  (2026-09-14)

## Corpus Check
- 58 files · ~422,800 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 1511 nodes · 3100 edges · 78 communities (64 shown, 13 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 330 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7bb9dbe7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- InstagramMedia
- test_role_management.py
- test_temporary_voice.py
- NotificationStore
- test_welcome.py
- DiscordBot
- Settings
- General
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
- TwitchClient
- test_twitch.py
- test_sends_instagram_post_content_and_link_button
- test_run_services_composes_single_bot_and_cleans_up_tasks
- test_youtube_audio.py
- CommandAccessTree
- twitch_auth.py
- app.py
- .resend_instagram_post_command
- FakeVoiceClient
- generate_deployment_article_pdf.py
- main.py
- test_instagram_oauth.py
- Configuração
- InstagramSettings
- TwitchAuthClient
- test_first_poll_marks_latest_as_known_then_notifies_new_media
- instagram_token_store.py
- CurrentTwitchLiveStore
- asyncio
- test_web_app_exposes_health_and_initializes_shared_store
- InstagramOAuthClient
- ._request
- test_retries_transient_token_endpoint_failure
- generate_deployment_article.py
- integrations/instagram_oauth.py
- test_oauth_rejects_an_account_other_than_the_configured_profile
- FakeInteractionResponse
- InstagramPoller
- test_instagram_client_reads_current_token_from_store
- FakeResponse
- test_validator_validates_once_and_stops_cleanly
- .on_voice_state_update
- SecretStore
- environment
- role_management.py
- .__init__
- .check_once
- ._run
- TwitchToken
- test_boolean_values_are_converted
- FakeSecretStore
- ._schedule_idle_from_audio_thread
- ._is_instagram_post
- RoleReactionOption
- RoleMenuSettings
- setup
- ._resend_instagram_media
- cogs/__init__.py
- bot/__init__.py
- integrations/__init__.py
- .aclose
- .refresh_access_token
- tasks/__init__.py
- .refresh_access_token
- web/__init__.py
- role_settings
- discord-bot

## God Nodes (most connected - your core abstractions)
1. `Settings` - 99 edges
2. `General` - 45 edges
3. `DiscordBot` - 44 edges
4. `TwitchClient` - 42 edges
5. `InstagramMedia` - 42 edges
6. `InstagramTokenData` - 40 edges
7. `InstagramClient` - 37 edges
8. `DiscordNotificationSender` - 36 edges
9. `ConfigurationError` - 35 edges
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

## Communities (78 total, 13 thin omitted)

### Community 0 - "InstagramMedia"
Cohesion: 0.06
Nodes (51): Cliente principal do bot do Discord., Comandos gerais do bot., Estado em memória da última live Twitch confirmada como aberta., Envio seguro de notificações para canais do Discord., InstagramAPIError, InstagramAuthenticationError, InstagramClient, InstagramPermissionError (+43 more)

### Community 1 - "test_role_management.py"
Cohesion: 0.06
Nodes (43): discord_error(), FakeBot, FakeChannel, FakeGuild, FakeMember, FakeMessage, FakeRole, payload() (+35 more)

### Community 2 - "test_temporary_voice.py"
Cohesion: 0.06
Nodes (46): build_voice_fixture(), discord_error(), FakeBot, FakeCategory, FakeGuild, FakeMember, FakePrincipal, FakeRole (+38 more)

### Community 3 - "NotificationStore"
Cohesion: 0.05
Nodes (43): Connection, NotificationStore, Path, Persiste identificadores processados para evitar notificações duplicadas., Cria as tabelas e índices necessários, caso ainda não existam., Registra um evento EventSub e retorna se ele ainda não havia sido recebido., Atualiza o estado de envio de uma notificação Twitch., Informa se uma mídia já foi conhecida ou notificada. (+35 more)

### Community 4 - "test_welcome.py"
Cohesion: 0.06
Nodes (40): AppCommandError, handle_app_command_error(), Interaction, Tratamento de erros de comandos de aplicativo., Registra um erro técnico e envia uma mensagem segura ao usuário., Envia uma resposta efêmera, inclusive após uma resposta já iniciada., _send_error_message(), discord_error() (+32 more)

### Community 5 - "DiscordBot"
Cohesion: 0.05
Nodes (34): RawReactionActionEvent, Role, DiscordBot, Carrega extensões e sincroniza comandos antes de conectar ao gateway., Enfileira um evento EventSub sem bloquear a resposta HTTP da Twitch., Registra a conexão e inicia serviços que dependem do cliente pronto., Cancela tarefas e fecha clientes auxiliares antes de encerrar o Discord., Entrega eventos Twitch após o cliente Discord ficar disponível. (+26 more)

### Community 6 - "Settings"
Cohesion: 0.05
Nodes (52): Canais de voz temporários criados a partir de um canal configurado., Configuração tipada e segura para inicializar o bot., Settings, Testes unitários da configuração do ambiente., A ausência de token Discord deve interromper a leitura da configuração., O intervalo do validador Twitch é inteiro positivo e tem padrão documentado., O limite de moderação tem padrão seguro e não aceita valores não positivos., O caminho de cookies é opcional e permanece uma configuração local do host. (+44 more)

### Community 7 - "General"
Cohesion: 0.09
Nodes (46): General, Agrupa comandos slash de uso geral., Dados de uma live consultada após a notificação EventSub., TwitchStream, FakeInstagramClient, FakeInteraction, FakeNotificationSender, FakeTwitchClient (+38 more)

### Community 8 - "TemporaryVoice"
Cohesion: 0.07
Nodes (33): Snowflake, Bot, Client, Guild, GuildChannel, listener, Lock, Member (+25 more)

### Community 9 - "test_media_reactions.py"
Cohesion: 0.07
Nodes (40): Message, MediaReactions, _message_contains_media(), Bot, Client, listener, Reações automáticas para mídias enviadas em um canal configurado., Registra uma mensagem uma vez e limita o cache estritamente em memória. (+32 more)

### Community 10 - ".from_environment"
Cohesion: 0.10
Nodes (45): _boolean(), ConfigurationError, _https_url(), _instagram_api_version(), _log_level(), _numeric_id(), _optional_https_url(), _optional_iso_datetime() (+37 more)

### Community 11 - "DiscordNotificationSender"
Cohesion: 0.08
Nodes (23): File, DiscordNotificationError, DiscordNotificationSender, Embed, Member, Path, RuntimeError, User (+15 more)

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
Nodes (13): AwsSecretsManagerInstagramTokenStore, JsonFileInstagramTokenStore, Persiste token em JSON atômico, fora do Git e com modo 0600 em sistemas POSIX., Lê o JSON persistido; usa o ambiente apenas quando ainda não há arquivo., Grava uma resposta completa de modo atômico e atualiza o fallback em memória., Armazena a estrutura tipada do token em um único segredo JSON da AWS., Converte o segredo JSON em dados de token sem expor seu valor., Grava dados validados em JSON, sem logs ou arquivos públicos. (+5 more)

### Community 17 - "test_instagram.py"
Cohesion: 0.17
Nodes (23): InstagramTokenRefreshResult, Resultado seguro de uma renovação bem-sucedida de token Instagram., FakeRefreshClient, FakeTokenStore, instagram_refresh_environment(), datetime, Exception, Testes sem rede para cliente e polling da API oficial do Instagram. (+15 more)

### Community 18 - "InstagramTokenRefreshTask"
Cohesion: 0.11
Nodes (16): InstagramTokenExpiredError, Indica que o token já expirou e precisa de nova autorização manual., InstagramTokenStore, Contrato para obter e salvar tokens sem acoplar o cliente à infraestrutura., Retorna o token atual e seus metadados, quando estiver configurado., Persiste um token recém-autorizado sem registrá-lo em logs., InstagramTokenRefreshClient, InstagramTokenRefreshTask (+8 more)

### Community 19 - "TwitchClient"
Cohesion: 0.11
Nodes (13): AsyncClient, Busca ID, login e nome exibido de um perfil pelo login., Obtém o ID do perfil configurado e o reutiliza apenas em memória., Expõe somente o ID já resolvido, sem I/O na rota do webhook., Busca o título atual da live para enriquecer uma notificação., Descarta apenas o token que gerou a falha, preservando renovação concorrente., Acessa Helix/EventSub com token renovável e restrito à memória do processo., Descarta o token em memória e fecha somente recursos próprios. (+5 more)

### Community 20 - "test_twitch.py"
Cohesion: 0.14
Nodes (22): oauth_token_response(), asyncio, Response, Testes sem rede para Helix e EventSub com token Twitch renovável., Uma chamada GET recebe um token novo e é repetida uma única vez após HTTP 401., A ausência de dados de stream permite limpar a live atual sem notificar…, Retorna uma resposta OAuth curta e válida para os transportes simulados., EventSub consulta inscrições depois de 401 para não criar uma duplicata. (+14 more)

### Community 21 - "test_sends_instagram_post_content_and_link_button"
Cohesion: 0.15
Nodes (16): InstagramNotificationView, View com botão para abrir a publicação original no Instagram., FakeChannel, FakeDiscordClient, instagram_environment(), asyncio, Testes do envio de embeds Discord sem conexão externa., Um ID que não resolve para canal de mensagens não é aceito. (+8 more)

### Community 22 - "test_run_services_composes_single_bot_and_cleans_up_tasks"
Cohesion: 0.10
Nodes (11): FakeBot, FakeServer, FakeStore, asyncio, MonkeyPatch, Testes da composição integrada sem conectar Discord, Twitch ou Uvicorn reais., Store sem I/O para confirmar que a composição cria apenas uma instância., Bot mínimo que permanece ativo até o desligamento coordenado. (+3 more)

### Community 23 - "test_youtube_audio.py"
Cohesion: 0.11
Nodes (16): FakeExtractor, asyncio, Exception, parametrize, Testes sem rede para validação e extração de áudio do YouTube., A extração não bloqueia o loop e retorna URL temporária apenas ao chamador…, Falhas do yt-dlp não vazam detalhes do vídeo nem do stream., Extrator controlado compatível com o context manager do yt-dlp. (+8 more)

### Community 24 - "CommandAccessTree"
Cohesion: 0.14
Nodes (15): CommandAccessTree, Interaction, Controle global de acesso aos comandos slash por cargo Discord., Impede a execução de slash commands por membros sem o cargo configurado., Valida o cargo antes de qualquer comando registrado na árvore., FakeResponse, make_interaction(), SimpleNamespace (+7 more)

### Community 25 - "twitch_auth.py"
Cohesion: 0.14
Nodes (15): Configurações necessárias para o EventSub da Twitch., TwitchSettings, AsyncClient, datetime, RuntimeError, Autenticação OAuth de App Access Token da Twitch, somente em memória., Erro seguro e genérico de uma integração com a Twitch., Falha segura em uma chamada à API Helix ou EventSub. (+7 more)

### Community 26 - "app.py"
Cohesion: 0.11
Nodes (14): Fecha o cliente HTTP privado quando o FastAPI encerrar., create_web_app(), lifespan(), FastAPI, Fábrica da aplicação FastAPI usada pelo webhook da Twitch., Cria o servidor HTTP sem instanciar um segundo cliente Discord., create_instagram_oauth_router(), InstagramOAuthService (+6 more)

### Community 27 - ".resend_instagram_post_command"
Cohesion: 0.19
Nodes (13): default_permissions, command, guild_only, has_permissions, Interaction, User, Responde a um teste simples de conectividade., Dispara uma DM de boas-vindas para o usuário selecionado. (+5 more)

### Community 28 - "FakeVoiceClient"
Cohesion: 0.12
Nodes (9): FakeVoiceChannel, FailingVoiceChannel, FakeVoiceChannel, FakeVoiceClient, MissingPyNaClChannel, Cliente de voz controlável que não reproduz áudio real., Canal de voz com conexão local controlada., Canal que simula a ausência da dependência de voz no host. (+1 more)

### Community 29 - "generate_deployment_article_pdf.py"
Cohesion: 0.14
Nodes (19): article_sections(), build_article_text(), create_pdf(), https_url(), main(), page_number(), parse_arguments(), Namespace (+11 more)

### Community 30 - "main.py"
Cohesion: 0.14
Nodes (17): Server, configure_logging(), Configuração centralizada de logs., Configura logs para o terminal sem registrar dados sensíveis., main(), _prepare_instagram_client(), _prepare_twitch_client(), Ponto de entrada que supervisiona o bot Discord e o servidor FastAPI. (+9 more)

### Community 31 - "test_instagram_oauth.py"
Cohesion: 0.14
Nodes (13): FakeBot, FakeOAuthService, oauth_environment(), Testes do Instagram Login sem chamadas à Meta, Discord ou rede real., State inválido, replay e erro da Meta não liberam detalhes ao navegador., Um callback válido é aceito uma vez e sua repetição é bloqueada., Implementa o contrato mínimo do armazenamento compartilhado do FastAPI., Evita criar um segundo cliente Discord ao construir o app HTTP. (+5 more)

### Community 32 - "Configuração"
Cohesion: 0.11
Nodes (18): API FastAPI local, Autorizar a conta, Canais de voz temporários, Cargos automáticos e por reação, Comandos Discord, Configuração, Discord, Discord Bot: Twitch e Instagram (+10 more)

### Community 33 - "InstagramSettings"
Cohesion: 0.13
Nodes (12): InstagramSettings, Configurações para a consulta oficial de mídia do Instagram., Indica se as três credenciais necessárias para OAuth foram informadas., Indica se há dados mínimos no ambiente para iniciar polling imediatamente., AsyncClient, AsyncClient, _fallback_token(), InMemoryInstagramTokenStore (+4 more)

### Community 34 - "TwitchAuthClient"
Cohesion: 0.17
Nodes (14): Any, Response, Confirma com a Twitch se um token ainda pode ser usado., Repete somente falhas transitórias de rede ou servidor, sem registrar segredos., Falha ao autenticar a aplicação Twitch., Client ID ou Client Secret foram recusados pela Twitch., Token Twitch inválido, expirado ou com resposta de validação incorreta., Obtém e valida tokens OAuth sem persistir valores sensíveis. (+6 more)

### Community 35 - "test_first_poll_marks_latest_as_known_then_notifies_new_media"
Cohesion: 0.13
Nodes (14): LogCaptureFixture, FakeInstagramClient, FakeSender, Path, O backend local grava token e expiração em JSON fora do repositório., Retorna mídias controladas sem chamar a API real., Registra mídias enviadas sem conectar ao Discord., A primeira execução não notifica conteúdo antigo e nunca duplica mídia. (+6 more)

### Community 36 - "instagram_token_store.py"
Cohesion: 0.16
Nodes (14): AwsSecretsManagerSecretStore, create_instagram_token_store(), InstagramTokenStoreError, _parse_expires_at(), Any, datetime, Path, RuntimeError (+6 more)

### Community 37 - "CurrentTwitchLiveStore"
Cohesion: 0.15
Nodes (9): Obtém a live atual e confirma que ela ainda está online antes do reenvio., CurrentTwitchLive, CurrentTwitchLiveStore, Combina o evento EventSub e os dados mais recentes de uma live aberta., Mantém uma única live atual com leituras e alterações consistentes. O conteúdo…, Registra a live somente se a API Twitch a confirmou como online., Retorna um instantâneo imutável da live atualmente aberta., Limpa o estado somente se ele ainda corresponder ao instantâneo recebido. (+1 more)

### Community 38 - "asyncio"
Cohesion: 0.17
Nodes (12): asyncio, Erros de autenticação são convertidos em exceções seguras., A renovação usa GET, grant_type oficial e calcula a expiração em UTC., Token expirado pede reautorização e nunca reproduz o valor secreto no erro., Uma falha 5xx tem repetição limitada antes de aceitar a resposta oficial válida., A resposta oficial é convertida mesmo quando campos opcionais estão ausentes., test_lists_media_with_optional_fields(), handler() (+4 more)

### Community 39 - "test_web_app_exposes_health_and_initializes_shared_store"
Cohesion: 0.17
Nodes (11): FakeBot, asyncio, Testes da fábrica FastAPI e do seu lifespan sem iniciar Discord real., Representa a única instância compartilhada recebida pela fábrica web., Atende ao contrato da rota sem criar um cliente Discord., Registra a inicialização do armazenamento pelo lifespan da aplicação., A fábrica não instancia Discord e usa o store recebido durante o lifespan., A API de saúde continua disponível sem expor rota Twitch quando ela está… (+3 more)

### Community 40 - "InstagramOAuthClient"
Cohesion: 0.25
Nodes (8): InstagramOAuthClient, InstagramOAuthError, Any, RuntimeError, Erro seguro do fluxo OAuth, apropriado para uma resposta HTTP genérica., Executa Instagram Login, troca o código e salva apenas dados validados., Monta a URL de consentimento usando somente a permissão de leitura necessária., Troca code por token duradouro, valida a conta e persiste o resultado.

### Community 41 - "._request"
Cohesion: 0.20
Nodes (8): Any, Response, Obtém inscrições EventSub para detectar duplicidades antes de criar uma nova., Monta o payload EventSub conforme o contrato ``stream.online`` v1., Cria EventSub sem duplicar uma inscrição após uma renovação de token., Executa Helix com uma única renovação segura após HTTP 401 quando aplicável., Indica um HTTP 401 da API Helix, sem incluir dados sensíveis., TwitchUnauthorizedError

### Community 42 - "test_retries_transient_token_endpoint_failure"
Cohesion: 0.20
Nodes (11): asyncio, Testes unitários do OAuth de App Access Token Twitch, sem rede externa., O token recebido inclui vencimento calculado e não depende de variável legada., Falha HTTP 5xx é repetida de forma limitada antes de aceitar a resposta válida., O endpoint OAuth de validação sinaliza token inválido sem expor seu valor., Credenciais recusadas geram erro claro sem revelar o segredo configurado., test_invalid_client_error_does_not_include_client_secret(), test_requests_token_with_expiration_in_memory() (+3 more)

### Community 43 - "generate_deployment_article.py"
Cohesion: 0.22
Nodes (12): build_article(), _https_url(), main(), parse_arguments(), Namespace, Lê os links públicos e o destino sem incluir dados sensíveis., Gera o arquivo e informa uma contagem de palavras verificável., Valida links públicos sem fazer requisições de rede. (+4 more)

### Community 44 - "integrations/instagram_oauth.py"
Cohesion: 0.21
Nodes (7): InstagramOAuthStateStore, datetime, OAuth do Instagram Login para autorizar uma conta profissional sem expor…, Guarda estados de uso único somente pelo tempo necessário para o callback., Cria um state criptograficamente aleatório e registra sua expiração., Valida e remove o state, impedindo seu reuso., Rotas HTTP do Instagram Login, isoladas do webhook da Twitch.

### Community 45 - "test_oauth_rejects_an_account_other_than_the_configured_profile"
Cohesion: 0.20
Nodes (8): MemoryTokenStore, asyncio, Uma autorização de outro perfil não sobrescreve o armazenamento atual., Armazena apenas dados de teste para verificar a persistência do callback., O callback troca code, valida username e salva os dados sem revelar token., test_oauth_authorizes_expected_account_and_persists_complete_token(), handler(), test_oauth_rejects_an_account_other_than_the_configured_profile()

### Community 46 - "FakeInteractionResponse"
Cohesion: 0.18
Nodes (5): FakeFollowup, FakeInteractionResponse, Embed, Captura a resposta inicial da interação slash., Captura as respostas posteriores ao defer.

### Community 47 - "InstagramPoller"
Cohesion: 0.24
Nodes (6): InstagramPoller, Consulta a mídia mais recente sem notificar conteúdo histórico por padrão., Inicia uma única tarefa de polling quando a integração está ativada., Cancela a tarefa pendente e aguarda seu encerramento., Consulta mídias recentes e envia cada publicação nova ainda pendente., Mantém o polling ativo sem derrubar o bot após uma falha recuperável.

### Community 48 - "test_instagram_client_reads_current_token_from_store"
Cohesion: 0.20
Nodes (8): FailingSender, instagram_environment(), Consultas posteriores usam o token salvo após renovação, sem reiniciar o bot., Ativa a integração Instagram com valores de teste não secretos., Simula uma falha Discord para verificar que a mídia continua pendente., Uma mídia só é marcada após a confirmação de envio ao Discord., test_instagram_client_reads_current_token_from_store(), test_poller_does_not_persist_media_when_discord_send_fails()

### Community 49 - "FakeResponse"
Cohesion: 0.20
Nodes (4): FakeFollowup, FakeResponse, Registra respostas iniciais de uma interaction., Registra mensagens posteriores ao defer.

### Community 50 - "test_validator_validates_once_and_stops_cleanly"
Cohesion: 0.28
Nodes (6): FakeTwitchClient, asyncio, Testes do ciclo de vida do validador periódico de token Twitch., Cliente mínimo que registra validações sem chamadas HTTP., A tarefa pode ser iniciada uma vez e cancelada sem deixar trabalho pendente., test_validator_validates_once_and_stops_cleanly()

### Community 51 - ".on_voice_state_update"
Cohesion: 0.25
Nodes (6): GuildChannel, listener, Member, VoiceState, Sai de uma sala sem humanos para não impedir a limpeza de salas temporárias., Verifica se há alguém além do bot na sala atual.

### Community 52 - "SecretStore"
Cohesion: 0.29
Nodes (5): Protocol, Contrato mínimo para um serviço gerenciado de segredos., Lê o valor de um segredo pelo identificador configurado., Atualiza o valor de um segredo pelo identificador configurado., SecretStore

### Community 53 - "environment"
Cohesion: 0.33
Nodes (4): fixture, environment(), Fixtures compartilhadas, sem credenciais reais., Fornece o mínimo de configuração válida para os testes.

### Community 54 - "role_management.py"
Cohesion: 0.33
Nodes (4): Cargos automáticos e menus seguros de cargos por reação., Configuração de uma mensagem de cargos por reação., Localiza somente um cargo explicitamente autorizado para o emoji., RoleCategorySettings

### Community 55 - ".__init__"
Cohesion: 0.33
Nodes (3): Client, View com botão de acesso à live da Twitch., TwitchNotificationView

### Community 56 - ".check_once"
Cohesion: 0.33
Nodes (3): Executa verificações periódicas sem repetir em ciclo rápido após uma falha., Inicia uma única tarefa se Instagram e renovação automática estiverem ativos., Recarrega, valida a janela e renova o token somente quando necessário.

### Community 57 - "._run"
Cohesion: 0.33
Nodes (3): Inicia no máximo uma tarefa periódica quando a integração está ativa., Executa uma validação para uso em testes ou disparos controlados., Mantém a validação independente e recuperável enquanto o bot estiver aberto.

### Community 58 - "TwitchToken"
Cohesion: 0.40
Nodes (4): datetime, App Access Token Twitch mantido exclusivamente na memória do processo., Informa se o token deve ser renovado antes de uma nova chamada à API., TwitchToken

### Community 59 - "test_boolean_values_are_converted"
Cohesion: 0.40
Nodes (5): parametrize, Os formatos booleanos aceitos devem ser interpretados corretamente., O controle de repetição Twitch usa os mesmos formatos booleanos aceitos., test_boolean_values_are_converted(), test_twitch_retry_boolean_is_converted()

### Community 61 - "._schedule_idle_from_audio_thread"
Cohesion: 0.50
Nodes (3): AbstractEventLoop, Exception, Agenda a desconexão no loop correto após callback síncrono do player.

### Community 63 - "RoleReactionOption"
Cohesion: 0.50
Nodes (3): Vínculo seguro entre um emoji configurado e um cargo do Discord., Retorna chaves compatíveis com emojis Unicode e personalizados., RoleReactionOption

### Community 64 - "RoleMenuSettings"
Cohesion: 0.50
Nodes (3): Configuração opcional dos cargos automáticos e menus por reação., Indica se há ao menos uma mensagem de reação configurada., RoleMenuSettings

### Community 65 - "setup"
Cohesion: 0.67
Nodes (3): Bot, Registra o cog de comandos gerais na extensão., setup()

## Knowledge Gaps
- **16 isolated node(s):** `discord-bot`, `Requisitos`, `Instalação`, `API FastAPI local`, `Discord` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 749 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `InstagramMedia`, `test_temporary_voice.py`, `NotificationStore`, `test_welcome.py`, `DiscordBot`, `TemporaryVoice`, `test_media_reactions.py`, `.from_environment`, `DiscordNotificationSender`, `Music`, `test_instagram.py`, `InstagramTokenRefreshTask`, `test_twitch.py`, `test_sends_instagram_post_content_and_link_button`, `test_run_services_composes_single_bot_and_cleans_up_tasks`, `app.py`, `main.py`, `test_instagram_oauth.py`, `test_first_poll_marks_latest_as_known_then_notifies_new_media`, `asyncio`, `test_web_app_exposes_health_and_initializes_shared_store`, `test_retries_transient_token_endpoint_failure`, `test_oauth_rejects_an_account_other_than_the_configured_profile`, `test_instagram_client_reads_current_token_from_store`, `test_validator_validates_once_and_stops_cleanly`, `role_management.py`, `.__init__`, `test_boolean_values_are_converted`, `role_settings`?**
  _High betweenness centrality (0.233) - this node is a cross-community bridge._
- **Why does `DiscordBot` connect `DiscordBot` to `InstagramMedia`, `setup`, `NotificationStore`, `CurrentTwitchLiveStore`, `Settings`, `TemporaryVoice`, `test_media_reactions.py`, `DiscordNotificationSender`, `Music`, `InstagramPoller`, `InstagramTokenRefreshTask`, `TwitchClient`, `role_management.py`, `CommandAccessTree`, `twitch_auth.py`, `app.py`, `main.py`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Why does `Music` connect `Music` to `DiscordBot`, `Settings`, `test_music.py`, `.play_youtube`, `.on_voice_state_update`, `._schedule_idle_from_audio_thread`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `Settings` (e.g. with `DiscordBot` and `MediaReactions`) actually correct?**
  _`Settings` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `General` (e.g. with `CurrentTwitchLive` and `CurrentTwitchLiveStore`) actually correct?**
  _`General` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `DiscordBot` (e.g. with `CommandAccessTree` and `Settings`) actually correct?**
  _`DiscordBot` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `TwitchClient` (e.g. with `DiscordBot` and `General`) actually correct?**
  _`TwitchClient` has 15 INFERRED edges - model-reasoned connections that need verification._