# Provider And Authentication Model

HarnessGenerator should support multiple provider modes without assuming that every harness calls a
frontier model directly.

A harness can be deterministic, offline, local-model backed, API-backed, or exposed inside ChatGPT
as an action or connector. These are different deployment paths with different authentication
models.

## Provider Modes

| Mode | Runtime model access | Typical use |
| --- | --- | --- |
| Deterministic | None | Baselines, validators, fixed heuristics |
| Cached provider output | None during run | Tests, replay, draft-data cleanup |
| Local model | Local runtime credentials/config | Private or offline deployments |
| Direct API | Provider API key or service account | Server-side production harness |
| ChatGPT action/connector | ChatGPT invokes an external service | User-facing ChatGPT integration |

Tests should use deterministic, local, mocked, or cached modes. Live external APIs must not be used
in tests unless a task explicitly opts into an integration check.

## Direct OpenAI API Access

For direct OpenAI API calls, OpenAI's API documentation describes API-key authentication using
Bearer tokens. The key should be loaded from a server-side environment variable or secret manager,
not exposed to clients.

Relevant OpenAI docs:

- API authentication: https://platform.openai.com/docs/api-reference/authentication
- Quickstart authentication: https://platform.openai.com/docs/quickstart/authentication
- Models API: https://platform.openai.com/docs/api-reference/models/list

For a harness that calls a model such as `gpt-5.5`, the provider config should declare the model id
and API mode, while the actual key stays outside the export:

```yaml
provider: openai
auth_mode: api_key
model: gpt-5.5
api_key_env: OPENAI_API_KEY
project_env: OPENAI_PROJECT_ID
organization_env: OPENAI_ORGANIZATION_ID
```

## OpenAI Service Accounts

For production server-side harnesses, prefer project-scoped service accounts or project API keys
over personal user keys when possible. OpenAI documents project service accounts as bot users not
associated with a human user, which avoids breakage when an employee leaves an organization.

Relevant OpenAI docs:

- Project service accounts:
  https://platform.openai.com/docs/api-reference/project-service-accounts
- Project API keys:
  https://platform.openai.com/docs/api-reference/project-api-keys/retrieve
- Administration keys:
  https://platform.openai.com/docs/api-reference/administration

Admin API keys are for organization administration, not normal model calls.

## ChatGPT Actions, Apps, And OAuth

OAuth in ChatGPT Actions or connectors is for authenticating a ChatGPT user to an external service.
It is not the same as giving an exported harness access to call OpenAI models using that user's
ChatGPT subscription.

Relevant OpenAI docs:

- GPT Action authentication:
  https://platform.openai.com/docs/actions/authentication/api-key-authentication%23.gz
- ChatGPT connectors:
  https://help.openai.com/en/articles/11487775/

Use this path when the harness is exposed as a tool inside ChatGPT:

```text
ChatGPT user -> ChatGPT action/connector -> your service -> your harness
```

In that design:

- ChatGPT handles the conversation UI.
- OAuth authenticates the user to your service or data source.
- Your service enforces authorization.
- Your service decides whether it calls OpenAI, another provider, or no model at all.

Do not assume a ChatGPT Plus, Pro, Business, Enterprise, or Edu license can be exchanged for API
runtime credentials for an external harness.

## Export Rules

Provider config may be exported. Provider secrets must not be exported.

Allowed in export:

- provider name
- model id
- endpoint family
- environment variable names
- required scopes
- cost policy
- timeout policy
- cache policy

Not allowed in export:

- API keys
- OAuth client secrets
- refresh tokens
- access tokens
- raw request logs containing secrets

## Provider-Agnostic Harnesses

Where possible, keep the harness provider-agnostic:

- put model ids in config
- isolate provider adapters
- validate outputs with local code
- record model/provider versions in reports
- support cached provider output for replay

This mirrors the core HarnessGenerator goal: optimize the process around the model without tying
the entire harness to one provider.
