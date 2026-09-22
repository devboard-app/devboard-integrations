# devboard-integrations

**Tells people what happened.** It sends Slack and Discord messages, shows in-app notifications, and links GitHub commits to tickets.

- **Port:** `8005`
- **Stack:** Flask, SQLAlchemy, PostgreSQL, Redis Streams
- **Two containers, one image:**

| Container | Command | Job |
|---|---|---|
| `devboard-integrations` | `gunicorn wsgi:app` | REST API and GitHub webhook. |
| `devboard-integrations-worker` | `python -m app.consumer.worker` | Reads the event stream. |

---

## Start here (about 5 minutes)

1. Open a terminal in `devboard-infra`.
2. Run `setup.bat`. It creates the database, starts both containers and runs the migrations.
3. Open `http://localhost:8005/api/notifications/`. It answers `401`, which means the service is up and wants a login.

Only want this service? Postgres and Redis must already be running. Then:

```bash
docker compose up --build
alembic upgrade head
```

To change code later: `redeploy.bat` in `devboard-infra`, option `5`.

---

## What it does

1. **Team settings** – each team saves a Slack webhook, a Discord webhook and linked GitHub repos.
2. **Notifications** – an in-app inbox for each user.
3. **Slack and Discord messages** – sent when a sprint starts or ends.
4. **GitHub commit links** – a commit message with `DEV-12` links that commit to ticket `DEV-12`.

---

## How it fits

```
devboard-work ──> Redis stream (devboard:events) ──> integrations-worker ──> notifications
                                                 │                        └──> Slack / Discord
                                                 └──> analytics (its own reader)

GitHub ──push webhook──> integrations ──> devboard-work (find the ticket)
                                     └──> Redis stream (ticket.commit_linked)

integrations ──X-Service-Key──> devboard-work   (is this user a team admin?)
```

This service has **no user or team tables**. Each time, it asks devboard-work whether the caller is an owner or admin of the team.

---

## Events it handles

| Event | What happens |
|---|---|
| `ticket.assigned` | In-app notification |
| `ticket.status_changed` | In-app notification |
| `comment.created` | In-app notification |
| `comment.mentioned` | In-app notification |
| `sprint.started` | Slack and Discord message |
| `sprint.completed` | Slack and Discord message |

All other events are acked and dropped on purpose. They are for analytics. So a typo in an event name fails **silently**.

**A message is sent to Slack or Discord only if** the webhook URL is set **and** that trigger is `true`.

### If a handler fails

1. The message is not acked, so it stays pending.
2. It is picked up again after 60 seconds.
3. After **3 tries**, it goes into `failed_events` and is acked.

---

## API

### Team settings

Needs a JWT **and** owner/admin role on the team.

| Method | Path | What it does |
|---|---|---|
| `GET` `POST` `PATCH` | `/api/integrations/<team_id>/` | Read, create, update the settings. |
| `POST` | `/api/integrations/<team_id>/repo-links/` | Link a GitHub repo to a project. Body: `project_id`, `github_repo`. |
| `DELETE` | `/api/integrations/<team_id>/repo-links/<repo_link_id>/` | Remove a link. |

`enabled_triggers` chooses which events go to which provider:

```json
{
  "slack":   { "sprint.started": true, "sprint.completed": false },
  "discord": { "sprint.completed": true }
}
```

**Webhook URL rules** (checked on save):

- `https` only.
- Slack: host must be `hooks.slack.com`.
- Discord: host must be `discord.com` or `discordapp.com`.
- A bad URL returns `400`.

This stops a team admin from pointing the webhook at an internal service.

### Notifications

JWT only. You can only see and change your own.

| Method | Path | What it does |
|---|---|---|
| `GET` | `/api/notifications/` | Your inbox. Uses `limit` (default 20, max 100) and `offset`. |
| `PATCH` | `/api/notifications/read-all/` | Mark all as read. |
| `PATCH` | `/api/notifications/<notification_id>/` | Mark one as read. |
| `DELETE` | `/api/notifications/<notification_id>/` | Delete one. |

### GitHub webhook

`POST /api/webhooks/github/`

1. Checks the `X-Hub-Signature-256` header with `GITHUB_WEBHOOK_SECRET`.
2. Ignores everything except `push`.
3. Finds ticket keys in each commit message (pattern like `DEV-12`).
4. Asks devboard-work if the ticket exists.
5. Publishes `ticket.commit_linked`.

Two details:

- The event's actor is a **fixed system id**, not the commit author. Anyone can fake a commit author.
- GitHub sometimes sends the same webhook twice. The table `linked_commits` has a unique key on `(repo, commit_sha, ticket_id)`, so the second one is skipped.

---

## Settings

Copy `.env.example` to `.env`. **All values are required.** The service crashes at start if one is missing.

| Variable | What it is |
|---|---|
| `DB_HOST` `DB_PORT` `DB_NAME` `DB_USER` `DB_PASSWORD` | Database. Docker overrides host and port. |
| `REDIS_HOST` | Docker overrides it to `devboard-redis`. |
| `JWT_SECRET` | Same value in every service. |
| `INTERNAL_API_KEY` | Sent as `X-Service-Key` to devboard-work. |
| `DEVBOARD_WORK_URL` | Team role checks and ticket lookups. |
| `GITHUB_WEBHOOK_SECRET` | Secret for the GitHub signature. |

---

## Tables

| Table | What is in it |
|---|---|
| `team_integrations` | One row per team: webhook URLs, `enabled_triggers`. |
| `repo_links` | GitHub repo (unique) to project and team. |
| `linked_commits` | Stops duplicate commit links. |
| `notifications` | The in-app inbox. |
| `failed_events` | Events that failed 3 times. |

```bash
alembic upgrade head
alembic revision --autogenerate -m "message"
```

---

## Not done yet

- **One repo, one project.** A GitHub repo can link to only one project across all teams.
