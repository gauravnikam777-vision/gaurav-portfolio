"""
github_sync.py
==============
100% automatic GitHub sync.

What comes from WHERE:
  ┌─────────────────────────────────────────────────────────┐
  │  Profile (name, bio, avatar, location, followers)       │
  │  → GitHub User API — auto, no config needed             │
  │                                                         │
  │  Projects (ALL repos)                                   │
  │  → GitHub Repos API — new repo = auto shows on portfolio│
  │  → Repo description  = project description             │
  │  → Repo homepage     = live app URL                    │
  │  → Repo topics       = project tags                    │
  │  → Repo stars/forks  = shown automatically             │
  │                                                         │
  │  Skills, Education, Certifications                      │
  │  → portfolio.json in your GitHub profile repo           │
  │  → Set up ONCE, then edit on GitHub like any file       │
  └─────────────────────────────────────────────────────────┘
"""

import os, time, requests

# ─────────────────────────────────────────────────────────────────
GITHUB_USERNAME  = "gauravnikam777-vision"
PROFILE_REPO     = "gauravnikam777-vision"   # your profile repo (same name as username)
CONFIG_FILE      = "portfolio.json"           # lives inside your profile repo
GITHUB_TOKEN     = os.environ.get("GITHUB_TOKEN", "")
CACHE_SECONDS    = 600   # 10 min — or instant via webhook

# Repos to always hide from portfolio
HIDDEN_REPOS = {GITHUB_USERNAME, "cip-project"}

# ── EMOJI MAP: auto-assign emoji based on repo topics / language ──
EMOJI_MAP = {
    "machine-learning": "🤖", "ml": "🤖",
    "deep-learning": "🧠",    "neural-network": "🧠",
    "data-analysis": "📊",    "eda": "📊",
    "prediction": "📉",       "churn": "📉",
    "diabetes": "🩺",         "healthcare": "🩺",
    "power-bi": "⚡",          "dashboard": "⚡",
    "trading": "📈",           "finance": "📈",
    "ecommerce": "🛒",         "sql": "🗄️",
    "streamlit": "🚀",         "fastapi": "⚙️",
    "python": "🐍",
}

# ─────────────────────────────────────────────────────────────────
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
        print(f"[sync] ✗ {url}: {e}")
        return None

def _cached(key, fn, force=False):
    entry = _cache.get(key)
    if not force and entry and (time.time() - entry["ts"]) < CACHE_SECONDS:
        return entry["data"]
    data = fn()
    if data is not None:
        _cache[key] = {"data": data, "ts": time.time()}
    elif entry:
        return entry["data"]   # return stale rather than crash
    return data

# ─── GITHUB PROFILE ──────────────────────────────────────────────
def _fetch_profile():
    d = _get(f"https://api.github.com/users/{GITHUB_USERNAME}")
    if not d:
        return {}
    return {
        "name":       d.get("name") or "Gaurav Govind Nikam",
        "avatar_url": d.get("avatar_url", ""),
        "bio":        d.get("bio", ""),
        "location":   d.get("location", "Pune, India"),
        "blog":       d.get("blog", ""),
        "followers":  d.get("followers", 0),
        "following":  d.get("following", 0),
        "repo_count": d.get("public_repos", 0),
        "github_url": d.get("html_url", ""),
        "twitter":    d.get("twitter_username", ""),
    }

# ─── PORTFOLIO CONFIG (skills, education, certs) ─────────────────
def _fetch_config():
    """
    Fetch portfolio.json from your GitHub profile repo.
    This is the ONLY file you edit — and you edit it on GitHub, not locally.
    """
    url = (f"https://raw.githubusercontent.com/"
           f"{GITHUB_USERNAME}/{PROFILE_REPO}/main/{CONFIG_FILE}")
    try:
        r = requests.get(url, headers=_headers(), timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[sync] portfolio.json not found yet: {e}")
        return {}

# ─── REPOS → PROJECTS ────────────────────────────────────────────
def _fetch_repos():
    """
    Fetch ALL public repos. Each repo becomes a project automatically.
    - description  → project description
    - homepage     → live app URL (set in repo About → Website)
    - topics       → tech tags
    - stars        → shown on card
    - language     → primary language badge
    """
    repos = _get(
        f"https://api.github.com/users/{GITHUB_USERNAME}/repos",
        params={"type": "public", "per_page": 100, "sort": "updated"}
    )
    if not repos:
        return []

    # Get config for ordering / overrides / hidden list
    config = _cached("config", _fetch_config) or {}
    overrides = config.get("project_overrides", {})
    hidden    = set(config.get("hidden_repos", [])) | HIDDEN_REPOS

    projects = []
    for i, repo in enumerate(repos):
        name = repo.get("name", "")
        if name in hidden:
            continue

        ov = overrides.get(name, {})

        # Pick best emoji from topics
        topics = repo.get("topics", [])
        emoji = "💻"
        for t in topics:
            if t.lower() in EMOJI_MAP:
                emoji = EMOJI_MAP[t.lower()]
                break
        if emoji == "💻":
            lang = (repo.get("language") or "").lower()
            emoji = EMOJI_MAP.get(lang, "💻")

        # Format display name from repo slug
        display_name = ov.get("title") or name.replace("-", " ").replace("_", " ").title()

        project = {
            "slug":        name,
            "number":      str(i + 1).zfill(2),
            "emoji":       ov.get("emoji", emoji),
            "title":       display_name,
            "description": ov.get("description") or repo.get("description") or "",
            "live_url":    ov.get("live_url") or repo.get("homepage") or "",
            "github_url":  repo.get("html_url", ""),
            "stars":       repo.get("stargazers_count", 0),
            "forks":       repo.get("forks_count", 0),
            "language":    repo.get("language") or "",
            "tags":        topics,
            "updated_at":  (repo.get("updated_at") or "")[:10],
            "status":      ov.get("status", "Completed"),
            "key_insight": ov.get("key_insight", ""),
            "featured":    ov.get("featured", True),
            "order":       ov.get("order", 99 + i),
        }
        projects.append(project)

    # Sort: featured with explicit order first, rest by last updated
    featured   = sorted([p for p in projects if p.get("order") < 90], key=lambda x: x["order"])
    rest       = sorted([p for p in projects if p.get("order") >= 90], key=lambda x: -x["stars"])
    return featured + rest

# ─── MASTER FUNCTION ─────────────────────────────────────────────
def get_portfolio_data(force=False):
    """
    Call this in every Flask route.
    Returns everything the portfolio needs — cached 10 min.

    FLOW:
      1. GitHub User API      → profile (auto)
      2. GitHub Repos API     → projects (auto — new repo = auto appears)
      3. profile repo JSON    → skills, education, certifications
    """
    gh       = _cached("profile", _fetch_profile,  force) or {}
    config   = _cached("config",  _fetch_config,   force) or {}
    projects = _cached("repos",   _fetch_repos,    force) or []

    # Build skill groups
    skills = config.get("skills", [])
    skill_groups = {}
    for s in skills:
        cat = s.get("category", "Other")
        skill_groups.setdefault(cat, []).append(s)

    # Merge profile config with live GitHub data
    profile_cfg = config.get("profile", {})
    profile = {
        **profile_cfg,
        # GitHub live data always wins for these fields:
        "avatar_url":  gh.get("avatar_url") or profile_cfg.get("avatar_url", ""),
        "github_url":  gh.get("github_url", ""),
        "followers":   gh.get("followers", 0),
        "repo_count":  gh.get("repo_count", 0),
        "name":        gh.get("name") or profile_cfg.get("name", "Gaurav Govind Nikam"),
        "location":    gh.get("location") or profile_cfg.get("location", "Pune, India"),
    }

    return {
        "profile":        profile,
        "skills":         skills,
        "skill_groups":   skill_groups,
        "education":      config.get("education",      []),
        "certifications": config.get("certifications", []),
        "projects":       projects,
        "github":         gh,
        "last_synced":    time.strftime("%d %b %Y, %H:%M"),
        "total_projects": len(projects),
        "total_certs":    len(config.get("certifications", [])),
    }


def invalidate_cache():
    global _cache
    _cache = {}
    print("[sync] Cache cleared — next request fetches fresh GitHub data.")
