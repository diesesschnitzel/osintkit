"""GitHub user lookup via GitHub API (Stage 2 — requires API token)."""

from typing import Dict, List

import httpx

from osintkit.modules import RateLimitError, InvalidKeyError


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
        headers = {"Accept": "application/vnd.github.v3+json"}
        if api_key:
            headers["Authorization"] = f"token {api_key}"

        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            response = await client.get(
                f"https://api.github.com/users/{username}",
                headers=headers,
            )

        if response.status_code == 429:
            raise RateLimitError("GitHub API rate limit reached")
        if response.status_code in (401, 403):
            raise InvalidKeyError("GitHub token invalid or unauthorized")
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

    except (RateLimitError, InvalidKeyError):
        raise
    except Exception:
        return []
