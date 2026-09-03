# devboard-integrations

Outbound integrations and notifications for DevBoard. It does three things:

- keeps per-team Slack/Discord webhook settings and GitHub repo links
- receives GitHub push webhooks and links commits to tickets
- consumes the `devboard:events` Redis stream and turns events into in-app notifications or Slack/Discord messages

Flask + SQLAlchemy + Postgres + Redis Streams. Port **8005**.

## Two processes, one image

The Dockerfile builds once and `docker-compose.yml` runs it twice:

| container | command | role |
|---|---|---|
| `devboard-integrations` | `gunicorn wsgi:app` | REST API + GitHub webhook receiver |
| `devboard-integrations-worker` | `python -m app.consumer.worker` | stream consumer |

They share `devboard-db` and `devboard-redis`. The worker calls `create_app()` too, but
only to get a Flask app context — Flask-SQLAlchemy's `db.session` needs one, and outside
a request nobody pushes it for you.

## Where it sits

```
devboard-work ──publish──> devboard:events ──> integrations-worker ──> notifications
                                          └──> analytics (separate consumer group)

GitHub ──push webhook──> integrations ──lookup──> devboard-work
                                      └──XADD──> devboard:events (ticket.commit_linked)

integrations ──X-Service-Key──> devboard-work   (team role checks)
```

It has no user or team tables of its own. `require_team_admin` asks devboard-work on
every request whether the caller is an owner/admin of the team.

## Running it

Everything is orchestrated from `devboard-infra`:

```
cd ..\devboard-infra
setup.bat        # creates integrations_user + integrations_db, brings containers up
migrate.bat      # option 4 for this service alone
redeploy.bat     # rebuild after code changes
```

Standalone, if the shared Postgres and Redis are already up:

```
docker compose up --build
```

Migrations are alembic:

```
alembic upgrade head
alembic revision --autogenerate -m "..."
```

## Configuration

Copy `.env.example` to `.env`. All values are required — `config.py` reads them with
`os.environ[...]` and fails loudly at import if one is missing.

| var | notes |
|---|---|
| `DB_HOST` `DB_PORT` `DB_NAME` `DB_USER` `DB_PASSWORD` | compose overrides host/port to `devboard-db:5432` |
| `REDIS_HOST` | compose overrides to `devboard-redis` |
| `JWT_SECRET` | shared across all services, HS256, `sub` = user UUID |
| `INTERNAL_API_KEY` | sent as `X-Service-Key` on service-to-service calls |
| `DEVBOARD_WORK_URL` | team role checks and ticket lookups |
| `GITHUB_WEBHOOK_SECRET` | HMAC secret for `X-Hub-Signature-256` |
| `EMAIL_SERVICE_URL` `CORE_SERVICE_URL` | required but currently unused — see Known gaps |

## API

### Integration settings

All of these need a JWT *and* owner/admin on the team.

```
GET    /api/integrations/<team_id>/
POST   /api/integrations/<team_id>/
PATCH  /api/integrations/<team_id>/
POST   /api/integrations/<team_id>/repo-links/
DELETE /api/integrations/<team_id>/repo-links/<repo_link_id>/
```

`enabled_triggers` is a JSON switchboard, per provider and per event:

```json
{
  "slack":   { "sprint.started": true, "sprint.completed": false },
  "discord": { "sprint.completed": true }
}
```

A message is sent only if the provider's URL is set **and** its trigger is true.

Webhook URLs are validated on write: `https` only, host must be `hooks.slack.com` for
Slack or `discord.com`/`discordapp.com` for Discord. This matters — without it a team
admin could point the webhook at `devboard-auth` or a cloud metadata endpoint and have
the service POST event payloads to it from inside the docker network.

### Notifications

JWT only; ownership checked per row in the service layer.

```
GET    /api/notifications/
PATCH  /api/notifications/read-all/
PATCH  /api/notifications/<notification_id>/
DELETE /api/notifications/<notification_id>/
```

### GitHub webhook

```
POST /api/webhooks/github/
```

Verifies `X-Hub-Signature-256` with `hmac.compare_digest`, ignores anything that isn't a
`push`, then for each commit message pulls out ticket keys matching
`\b([A-Z][A-Z0-9]{1,9}-\d+)\b`, looks each one up in devboard-work, and publishes
`ticket.commit_linked` to the stream.

Two things worth knowing:

- The event's `actor_id` is a fixed system UUID, not the commit author. Anyone can
  `git commit --author`, so the author field is not an identity.
- GitHub redelivers webhooks. Each redelivery produces a *new* Redis message id, so
  analytics' id-based dedup would not catch it. `linked_commits` exists purely for this:
  a unique constraint on `(repo, commit_sha, ticket_id)`, inserted before publishing.
  The second delivery hits the constraint and skips.

## The consumer

Reads `devboard:events` as consumer group `devboard-integrations-group`. Analytics reads
the same stream under its own group, so both see every message independently.

Per loop:

1. `xautoclaim` with `min_idle_time=60s`, up to 50 pages of 100, to pick up messages a
   previous crash left stranded
2. `xreadgroup(">")` for new messages, `count=10`, `block=5000`
3. dispatch through `HANDLERS`

Handled events:

| event | result |
|---|---|
| `ticket.assigned` | in-app notification |
| `ticket.status_changed` | in-app notification |
| `comment.created` | in-app notification |
| `comment.mentioned` | in-app notification |
| `sprint.started` | Slack + Discord |
| `sprint.completed` | Slack + Discord |

Everything else on the stream (`ticket.updated`, `label.*`, `ticket.epic_*`, …) has no
handler, gets acked, and is dropped. That is intentional — those are analytics' business —
but it also means a mistyped handler key is completely silent. That is how
`comment.mention` vs `comment.mentioned` survived for a week.

A handler that raises is logged and **not** acked, so the message stays pending and comes
back on the next reclaim. After 3 delivery attempts it is written to `failed_events` and
acked. In practice a permanently-broken message runs three times over about three minutes
before it dead-letters.

## Tables

- `team_integrations` — one row per team; webhook URLs, `enabled_triggers`, `email_notifications`
- `repo_links` — `github_repo` (unique) → project + team
- `linked_commits` — idempotency ledger for commit linking; nothing reads it
- `notifications` — the in-app inbox
- `failed_events` — consumer dead-letter queue

## Known gaps

- **Email notifications are not wired up.** `email_notifications` is stored and returned
  by the API but nothing reads it, and `EMAIL_SERVICE_URL` is unused.
- **No pagination on `GET /api/notifications/`.** It returns every notification a user has
  ever received, and `recipient_id` has no index.
- **Validation errors return the wrong status.** `_validate_webhook_url` raises
  `ValueError`, which the views map to 409 on create and 404 on update. A rejected webhook
  URL should be a 400.
- **`logging.basicConfig` is only called in the worker.** In the gunicorn process
  `logger.info` goes nowhere (WARNING and above still reach stderr via `lastResort`).
- **`CONSUMER` is a hardcoded name.** More than one worker replica would make both
  processes share a pending list, which breaks reclaim. One replica only.
- **The retry counter reads `xpending_range(count=100)`.** If the pending list is deeper
  than 100, messages past that window never reach the dead-letter branch.
- **`repo_links.github_repo` is globally unique**, so a repo can be linked to exactly one
  project across all teams.
