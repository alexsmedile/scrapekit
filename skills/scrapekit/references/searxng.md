# searxng — free local web search

Local Docker on port 8080. Free, unlimited, no tracking.

**One-time setup:**
```bash
mkdir searxng && cd searxng
curl -fsSL -O https://raw.githubusercontent.com/searxng/searxng/master/container/docker-compose.yml \
    -O https://raw.githubusercontent.com/searxng/searxng/master/container/.env.example
cp .env.example .env
docker compose up -d
```

Use this when: the selected search route uses an existing local SearXNG instance.

**Reuse a configured service; start only when needed:**
Resolve `SEARXNG_COMPOSE_FILE` from project configuration if startup is needed.
Use an explicit existing file; do not assume a personal home directory. This
bounded example shuts down only a new stack owned by this invocation:

```bash
set -euo pipefail
umask 077
SEARXNG_URL="${SEARXNG_URL:-http://localhost:8080}"
started_here=false
cleanup() {
  if "$started_here"; then docker compose -f "$SEARXNG_COMPOSE_FILE" down; fi
}
trap cleanup EXIT
if ! curl -fsS --max-time 3 "$SEARXNG_URL/search?q=test&format=json" >/dev/null; then
  : "${SEARXNG_COMPOSE_FILE:?Set the configured existing compose file}"
  test -f "$SEARXNG_COMPOSE_FILE"
  existing=$(docker compose -f "$SEARXNG_COMPOSE_FILE" ps -aq)
  if [ -z "$existing" ]; then started_here=true; fi
  docker compose -f "$SEARXNG_COMPOSE_FILE" up -d
  ready=false
  for attempt in {1..15}; do
    if curl -fsS --max-time 2 "$SEARXNG_URL/search?q=test&format=json" >/dev/null; then
      ready=true; break
    fi
    sleep 1
  done
  "$ready" || { echo 'SearXNG startup timed out' >&2; exit 1; }
fi
mkdir -p .scrapekit
curl -fsS --max-time 15 --get --data-urlencode 'q=YOUR QUERY' \
  --data-urlencode 'format=json' "$SEARXNG_URL/search" -o .scrapekit/search.json
```

**Extract results:**
```bash
jq -r '.results[].url' .scrapekit/search.json
jq -r '.results[] | "\(.title)\n\(.url)"' .scrapekit/search.json | head -30
```

**Parallel queries:**
```bash
curl -fsS --max-time 15 "http://localhost:8080/search?q=ONE&format=json" -o .scrapekit/s1.json &
curl -fsS --max-time 15 "http://localhost:8080/search?q=TWO&format=json" -o .scrapekit/s2.json &
wait

# Reuse the ownership-aware cleanup above; never stop an existing service.
```
