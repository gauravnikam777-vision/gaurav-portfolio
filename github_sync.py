import os, time, requests

GITHUB_USERNAME = "gauravnikam777-vision"
GITHUB_TOKEN    = os.environ.get("GITHUB_TOKEN", "")
CACHE_SECONDS   = 600

HIDDEN_REPOS = {"gauravnikam777-vision", "cip-project"}

EMOJI_MAP = {
    "machine-learning": "🤖", "ml": "🤖",
    "deep-learning": "🧠",
    "data-analysis": "📊", "eda": "📊",
    "prediction": "📉", "churn": "📉",
    "diabetes": "🩺", "healthcare": "🩺",
    "power-bi": "⚡", "dashboard": "⚡",
    "trading": "📈", "finance": "📈",
    "ecommerce": "🛒", "sql": "🗄️",
    "streamlit": "🚀", "fastapi": "⚙️",
    "python": "🐍",
}

_cache = {}

def _headers():
    h = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"token {GITHUB_TOKEN}"
    return h

def _get(url, params=None):
    try:
        r = requests.get(url, headers=_headers(), params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[github_sync] Error {url}: {e}")
        return None

def _fresh(key):
    e = _cache.get(key)
    return e and (time.time() - e["ts"]) < CACHE_SECONDS

def _store(key, data):
    _cache[key] = {"data": data, "ts": time.time()}

def _cached(key):
    return _cache.get(key, {}).get("data")


def fetch_github_profile():
    """Returns live GitHub data: avatar_url, followers, repo_count."""
    if _fresh("profile"):
        return _cached("profile")

    d = _get(f"https://api.github.com/users/{GITHUB_USERNAME}")
    if not d:
        return _cached("profile") or {}

    data = {
        "avatar_url": d.get("avatar_url", ""),
        "followers":  d.get("followers", 0),
        "repo_count": d.get("public_repos", 0),
        "github_url": d.get("html_url", ""),
        "location":   d.get("location", ""),
        "bio":        d.get("bio", ""),
    }
    _store("profile", data)
    return data


def merge_projects(db_projects):
    """
    Merges GitHub repos with DB projects.
    - DB fields always win if set
    - GitHub fills missing fields automatically
    - New GitHub repos not in DB appear on portfolio automatically
    """
    if _fresh("repos"):
        gh_repos = _cached("repos")
    else:
        raw = _get(
            f"https://api.github.com/users/{GITHUB_USERNAME}/repos",
            params={"type": "public", "per_page": 100, "sort": "updated"}
        )
        gh_repos = []
        if raw:
            for repo in raw:
                name = repo.get("name", "")
                if name in HIDDEN_REPOS:
                    continue
                topics = repo.get("topics", [])
                emoji = "💻"
                for t in topics:
                    if t.lower() in EMOJI_MAP:
                        emoji = EMOJI_MAP[t.lower()]
                        break
                if emoji == "💻":
                    lang = (repo.get("language") or "").lower()
                    emoji = EMOJI_MAP.get(lang, "💻")

                gh_repos.append({
                    "gh_name":        name,
                    "gh_title":       name.replace("-", " ").replace("_", " ").title(),
                    "gh_description": repo.get("description") or "",
                    "gh_live_url":    repo.get("homepage") or "",
                    "gh_github_url":  repo.get("html_url", ""),
                    "gh_stars":       repo.get("stargazers_count", 0),
                    "gh_language":    repo.get("language") or "",
                    "gh_topics":      topics,
                    "gh_updated":     (repo.get("updated_at") or "")[:10],
                    "gh_emoji":       emoji,
                })
        _store("repos", gh_repos)

    gh_by_name = {r["gh_name"]: r for r in gh_repos}

    db_by_slug = {}
    for p in db_projects:
        gh_url = p["github_link"] or ""
        slug = gh_url.rstrip("/").split("/")[-1] if gh_url else p["title"]
        db_by_slug[slug] = dict(p)

    merged = []
    gh_seen = set()

    for slug, db_proj in db_by_slug.items():
        gh = gh_by_name.get(slug)
        gh_seen.add(slug)

        merged.append({
            "id":          db_proj["id"],
            "title":       db_proj["title"],
            "description": db_proj["description"] or (gh["gh_description"] if gh else ""),
            "details":     db_proj["details"] or "",
            "tools":       db_proj["tools"] or "",
            "github_link": db_proj["github_link"] or (gh["gh_github_url"] if gh else ""),
            "kaggle_link": db_proj["kaggle_link"] or "",
            "demo_link":   db_proj["demo_link"] or (gh["gh_live_url"] if gh else ""),
            "status":      db_proj["status"] or "Completed",
            "emoji":       db_proj["emoji"] or (gh["gh_emoji"] if gh else "💻"),
            "sort_order":  db_proj["sort_order"] or 99,
            "stars":       gh["gh_stars"] if gh else 0,
            "language":    gh["gh_language"] if gh else "",
            "topics":      gh["gh_topics"] if gh else [],
            "gh_updated":  gh["gh_updated"] if gh else "",
            "is_from_db":  True,
        })

    next_order = max((p["sort_order"] for p in merged), default=0) + 1
    for gh in gh_repos:
        if gh["gh_name"] in gh_seen:
            continue
        merged.append({
            "id":          None,
            "title":       gh["gh_title"],
            "description": gh["gh_description"],
            "details":     "",
            "tools":       ", ".join(filter(None, [gh["gh_language"]] + gh["gh_topics"][:3])),
            "github_link": gh["gh_github_url"],
            "kaggle_link": "",
            "demo_link":   gh["gh_live_url"],
            "status":      "Completed",
            "emoji":       gh["gh_emoji"],
            "sort_order":  next_order,
            "stars":       gh["gh_stars"],
            "language":    gh["gh_language"],
            "topics":      gh["gh_topics"],
            "gh_updated":  gh["gh_updated"],
            "is_from_db":  False,
        })
        next_order += 1

    return sorted(merged, key=lambda x: x["sort_order"])


def invalidate_cache():
    global _cache
    _cache = {}
    print("[github_sync] Cache cleared.")
