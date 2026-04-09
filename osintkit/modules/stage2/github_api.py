"""GitHub user lookup via GitHub API (Stage 2 — requires API token)."""

from typing import Dict, List

import httpx


async def run(inputs: dict, api_key: str) -> List[Dict]:
    """Look up a GitHub user profile via the GitHub REST API.

    Args:
        inputs: dict with at least 'username' key (handle)
        api_key: GitHub personal access token

    Returns:
        List with a single GitHub profile finding or [] if not found.

    Raises:
        Exception: on rate limiting (429) or invalid key (401/403).
    """
    username = inputs.get("username")
    if not username:
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            response = await client.get(
                f"https://api.github.com/users/{username}",
                headers={
                    "Authorization": f"token {api_key}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

        if response.status_code == 429:
            raise Exception("429 rate limited")
        if response.status_code in (401, 403):
            raise Exception("401 invalid key")
        if response.status_code == 404:
            return []

        data = response.json()

        return [{
            "source": "github_api",
            "type": "social_profile",
            "data": {
                "login": data.get("login"),
                "name": data.get("name"),
                "bio": data.get("bio"),
                "company": data.get("company"),
                "location": data.get("location"),
                "email": data.get("email"),
                "public_repos": data.get("public_repos"),
                "followers": data.get("followers"),
                "following": data.get("following"),
                "created_at": data.get("created_at"),
            },
            "url": data.get("html_url"),
        }]

    except Exception as e:
        if "429" in str(e) or "401" in str(e):
            raise
        return []
