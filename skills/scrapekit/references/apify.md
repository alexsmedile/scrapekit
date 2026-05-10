# apify — platform-specific scraping

Purpose-built actors for social media, e-commerce, maps. Generous free tier per actor.
Requires `APIFY_TOKEN` env var.

**Install:** `npm install -g apify-cli && apify login`
Get token: https://console.apify.com/settings/integrations

**Workflow:**
```bash
# Find actor
apify actors search "instagram scraper" --json 2>/dev/null | jq '.items[:3] | .[] | {id: .username, title}'

# Run (blocking)
apify actors call "apify/instagram-scraper" \
  -i '{"directUrls":["https://www.instagram.com/natgeo/"],"resultsType":"posts","resultsLimit":20}' \
  --json 2>/dev/null | tee .scrapekit/run.json

# Fetch results
DATASET_ID=$(jq -r '.defaultDatasetId' .scrapekit/run.json)
apify datasets get-items "$DATASET_ID" --format json > .scrapekit/results.json

# Long-running: async
apify actors start "ACTOR_ID" -i 'JSON' --json 2>/dev/null | tee .scrapekit/run.json
RUN_ID=$(jq -r '.id' .scrapekit/run.json)
apify runs info "$RUN_ID" --json 2>/dev/null | jq '.status'
```

Always add `--json 2>/dev/null` — stderr breaks JSON parsers.

## Actor catalog

| Platform | What | Actor ID |
|---|---|---|
| **Google** | Maps reviews | `compass/google-maps-reviews-scraper` |
| **Google** | Places | `compass/crawler-google-places` |
| **Google** | Ads | `silva95gustavo/google-ads-scraper` |
| **YouTube** | Videos / channel | `streamers/youtube-scraper` |
| **YouTube** | Comments | `streamers/youtube-comments-scraper` |
| **YouTube** | Shorts | `streamers/youtube-shorts-scraper` |
| **YouTube** | Transcripts | `pintostudio/youtube-transcript-scraper` |
| **YouTube** | Business emails | `dataovercoffee/youtube-channel-business-email-scraper` |
| **Instagram** | Posts | `apify/instagram-scraper` |
| **Instagram** | Post detail | `apify/instagram-post-scraper` |
| **Instagram** | Profile | `apify/instagram-profile-scraper` |
| **Instagram** | Reels | `apify/instagram-reel-scraper` |
| **Instagram** | Comments | `apify/instagram-comment-scraper` |
| **Instagram** | Hashtags | `apify/instagram-hashtag-scraper` |
| **TikTok** | Videos | `clockworks/tiktok-scraper` |
| **TikTok** | Profile | `clockworks/tiktok-profile-scraper` |
| **TikTok** | Comments | `clockworks/tiktok-comments-scraper` |
| **TikTok** | Hashtags | `clockworks/tiktok-hashtag-scraper` |
| **Facebook** | Posts | `apify/facebook-posts-scraper` |
| **Facebook** | Pages | `apify/facebook-pages-scraper` |
| **Facebook** | Groups | `apify/facebook-groups-scraper` |
| **Facebook** | Comments | `apify/facebook-comments-scraper` |
| **Facebook** | Reviews | `apify/facebook-reviews-scraper` |
| **Facebook** | Marketplace | `apify/facebook-marketplace-scraper` |
| **Facebook** | Ads Library | `curious_coder/facebook-ads-library-scraper` |
| **LinkedIn** | Profile | `dev_fusion/linkedin-profile-scraper` |
| **LinkedIn** | Profile search | `harvestapi/linkedin-profile-search` |
| **LinkedIn** | Profile posts | `harvestapi/linkedin-profile-posts` |
| **LinkedIn** | Jobs | `bebity/linkedin-jobs-scraper` |
| **X / Twitter** | Tweets | `apidojo/tweet-scraper` |
| **Reddit** | Posts / comments | `trudax/reddit-scraper-lite` |
| **Amazon** | Products | `junglee/amazon-crawler` |
| **E-commerce** | Generic | `apify/e-commerce-scraping-tool` |
| **Airbnb** | Listings | `tri_angle/airbnb-scraper` |
| **TripAdvisor** | Reviews | `maxcopell/tripadvisor-reviews` |

Check credits: https://console.apify.com/billing
