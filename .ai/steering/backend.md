# Backend — Convenções do Backend Java

## Arquitetura

**Modular monolith** em Java + Spring Boot. Extração de serviços independentes somente quando houver justificativa operacional ou de escala.

## Módulos de domínio

| Módulo | Responsabilidade | Release |
|--------|-----------------|---------|
| Identity | Cadastro, autenticação (OAuth 2.0/OIDC), sessões e tokens | R2 |
| User | Perfis e preferências | R2 |
| Workspace | Espaços de trabalho e equipes | R2 |
| Document | Metadados e gerenciamento de documentos | R2 |
| Storage | Upload (URLs pré-assinadas), download, versionamento e quotas | R2 |
| Synchronization | Controle de sincronização, sequenciamento de operações | R2 |
| Collaboration | Sessões colaborativas, presença e cursores | R3 |
| Sharing | Convites, permissões e ACL | R3 |

**Removidos do escopo inicial:** Billing e Notification — só entram quando o modelo de negócio for decidido.

## Papel do servidor (P-05)

O servidor **ordena, autoriza e distribui**. Ele NÃO:
- Interpreta a cena do documento.
- Aplica semântica gráfica (blend modes, composição).
- Renderiza conteúdo do documento.

Para operações que exigem o core (miniaturas, exportação, validação de formato, compactação de snapshots):
- **Worker Rust** acionado por fila de mensagens.
- Mesma base de código do core do cliente.

## APIs

- **REST:** OpenAPI 3.1 gerado a partir de `contracts/api/`. Clientes gerados, nunca editados à mão.
- **WebSocket:** AsyncAPI com JSON Schema para eventos em tempo real.
- **Upload de arquivos grandes:** URLs pré-assinadas para object storage, com expiração e validação de integridade.

## Modelo de dados

```
USER → USER_PROFILE, SESSION
USER → WORKSPACE → WORKSPACE_MEMBER
WORKSPACE → DOCUMENT → DOCUMENT_VERSION, DOCUMENT_ASSET, DOCUMENT_PERMISSION, DOCUMENT_COLLABORATOR, DOCUMENT_ACTIVITY
```

- PostgreSQL para dados relacionais e metadados.
- Object storage (S3-compatible / R2) para blobs (tiles, assets, thumbnails).
- **Nunca** armazenar blobs diretamente no PostgreSQL.

## Segurança

- OAuth 2.0 / OpenID Connect.
- Tokens de acesso de curta duração + refresh tokens com rotação.
- RBAC para permissões gerais + ACL por documento.
- Verificação de autorização em **toda** operação sensível (P-10).
- HTTPS obrigatório. Dados sensíveis criptografados em repouso.
- Rate limiting e proteção contra abuso nas APIs.
- Trilhas de auditoria separadas dos logs de aplicação (RNF-04.8).

## Observabilidade (ADR-017)

- **OpenTelemetry** para traces, métricas e logs.
- **SLIs de sincronização:** latência de confirmação, atraso por dispositivo, taxa de conflitos, falhas de upload, tamanho da fila pendente.
- Endpoints de saúde (`/health`, `/ready`).
- Alertas sobre SLIs e painéis por ambiente.

## Privacidade (ADR-018)

- LGPD e GDPR desde o desenho.
- Conteúdo do usuário **não** é usado para treinar modelos.
- Direitos do titular: acesso, portabilidade, exclusão, correção.
- Subprocessadores: lista pública.
- Residência de dados: região por workspace.
- DPIA antes do R2.

## Testes

- Unitários e de integração com Spring Boot Test.
- **Conformance suite:** mesmos vetores de teste de `contracts/conformance/` executados em Java e Rust.
- Testes de falha de rede e de interrupção durante sincronização.
- Testes de carga para operações de sync.
