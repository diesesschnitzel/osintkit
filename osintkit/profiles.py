"""Profile management for saving and rerunning scans."""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class ScanHistory(BaseModel):
    """Record of a single scan run."""
    scan_id: str
    timestamp: str
    inputs: Dict[str, Optional[str]]
    risk_score: int
    findings_count: int
    findings_file: Optional[str] = None
    html_file: Optional[str] = None


class Profile(BaseModel):
    """A saved target profile with scan history."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    scan_history: List[ScanHistory] = Field(default_factory=list)


class ProfileStore:
    """Manages profile storage in JSON file."""
    
    def __init__(self, store_path: Path = None):
        if store_path is None:
            store_path = Path.home() / ".osintkit" / "profiles.json"
        self.store_path = store_path
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _load(self) -> Dict[str, Dict]:
        """Load all profiles from store."""
        if not self.store_path.exists():
            return {}
        with open(self.store_path) as f:
            return json.load(f)
    
    def _save(self, profiles: Dict[str, Dict]):
        """Save all profiles to store."""
        with open(self.store_path, "w") as f:
            json.dump(profiles, f, indent=2, default=str)
    
    def create(self, profile: Profile) -> Profile:
        """Create a new profile."""
        profiles = self._load()
        profiles[profile.id] = profile.model_dump()
        self._save(profiles)
        return profile
    
    def get(self, profile_id: str) -> Optional[Profile]:
        """Get a profile by ID."""
        profiles = self._load()
        if profile_id in profiles:
            return Profile(**profiles[profile_id])
        return None
    
    def list(self, tag: str = None) -> List[Profile]:
        """List all profiles, optionally filtered by tag."""
        profiles = self._load()
        result = [Profile(**p) for p in profiles.values()]
        if tag:
            result = [p for p in result if tag in p.tags]
        return sorted(result, key=lambda p: p.updated_at, reverse=True)
    
    def update(self, profile: Profile) -> Profile:
        """Update an existing profile."""
        profile.updated_at = datetime.now().isoformat()
        profiles = self._load()
        profiles[profile.id] = profile.model_dump()
        self._save(profiles)
        return profile
    
    def delete(self, profile_id: str) -> bool:
        """Delete a profile."""
        profiles = self._load()
        if profile_id in profiles:
            del profiles[profile_id]
            self._save(profiles)
            return True
        return False
    
    def add_scan_result(self, profile_id: str, scan: ScanHistory) -> bool:
        """Add a scan result to a profile's history."""
        profile = self.get(profile_id)
        if not profile:
            return False
        profile.scan_history.append(scan)
        self.update(profile)
        return True
    
    def search(self, query: str) -> List[Profile]:
        """Search profiles by name, email, username, or notes."""
        profiles = self._load()
        query_lower = query.lower()
        result = []
        for p in profiles.values():
            if (query_lower in (p.get("name") or "").lower() or
                query_lower in (p.get("email") or "").lower() or
                query_lower in (p.get("username") or "").lower() or
                query_lower in (p.get("notes") or "").lower()):
                result.append(Profile(**p))
        return result
