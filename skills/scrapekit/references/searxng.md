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

**Always start → search → stop:**
```bash
docker compose -f ~/searxng/docker-compose.yml up -d
until curl -sf "http://localhost:8080/search?q=test&format=json" > /dev/null; do sleep 1; done

curl -s "http://localhost:8080/search?q=YOUR+QUERY&format=json" -o .scrapekit/search.json

docker compose -f ~/searxng/docker-compose.yml down
```

**Extract results:**
```bash
jq -r '.results[].url' .scrapekit/search.json
jq -r '.results[] | "\(.title)\n\(.url)"' .scrapekit/search.json | head -30
```

**Parallel queries:**
```bash
curl -s "http://localhost:8080/search?q=ONE&format=json" -o .scrapekit/s1.json &
curl -s "http://localhost:8080/search?q=TWO&format=json" -o .scrapekit/s2.json &
wait
docker compose -f ~/searxng/docker-compose.yml down
```
