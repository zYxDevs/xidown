import os
from typing import Optional
from xidown.core.config import DATA_DIR

class DomainManager:
    """Centralized domain detection and cookie mapping manager."""
    
    DOMAIN_PATTERNS = {
        "facebook.com": "facebook_com",
        "bilibili.com": "bilibili_com",
        "tiktok.com": "tiktok_com",
        "youtube.com": "youtube_com",
        "x.com": "x_com",
        "twitter.com": "x_com",
    }

    @classmethod
    def detect_domain(cls, url: str) -> str:
        """Extract a normalized domain key from a given URL."""
        if not url:
            return "unknown"
        url_lower = url.lower()
        for pattern, domain_key in cls.DOMAIN_PATTERNS.items():
            if pattern in url_lower:
                return domain_key
        return "unknown"

    @classmethod
    def get_domain_cookie_path(cls, url: str, fallback_cookie_path: Optional[str] = None) -> Optional[str]:
        """
        Return site-specific cookie path if it exists, otherwise fall back to global cookie path.
        """
        domain_key = cls.detect_domain(url)
        specific_cookie = os.path.join(DATA_DIR, f"cookies_{domain_key}.txt")
        if os.path.exists(specific_cookie):
            return specific_cookie
        return fallback_cookie_path
