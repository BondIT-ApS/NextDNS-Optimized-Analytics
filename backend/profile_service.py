# file: backend/profile_service.py
import os
from typing import Dict, List, Optional

import requests
from logging_config import get_logger

logger = get_logger(__name__)

API_KEY = os.getenv("API_KEY")


def get_profile_info(profile_id: str) -> Optional[Dict]:
    """Get profile information from NextDNS API.

    Args:
        profile_id (str): NextDNS profile ID

    Returns:
        dict: Profile information or None if error occurs
    """
    if not API_KEY:
        logger.warning("⚠️  No API_KEY available for profile fetching")
        return None

    try:
        url = f"https://api.nextdns.io/profiles/{profile_id}"
        headers = {"X-Api-Key": API_KEY}

        logger.debug(f"🌐 Fetching profile info for: {profile_id}")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            profile_data = response.json().get("data", {})
            logger.debug(
                f"✅ Profile {profile_id}: {profile_data.get('name', 'Unknown')}"
            )
            return {
                "id": profile_id,
                "name": profile_data.get("name", f"Profile {profile_id}"),
                "fingerprint": profile_data.get("fingerprint"),
                "created": profile_data.get("created"),
                "updated": profile_data.get("updated"),
            }

        if response.status_code == 404:
            logger.warning(f"⚠️  Profile {profile_id} not found (404)")
            return {
                "id": profile_id,
                "name": f"Profile {profile_id} (Not Found)",
                "error": "Profile not found",
            }

        if response.status_code == 403:
            logger.warning(f"⚠️  Access denied to profile {profile_id} (403)")
            return {
                "id": profile_id,
                "name": f"Profile {profile_id} (Access Denied)",
                "error": "Access denied",
            }
        else:
            logger.error(
                f"❌ Profile {profile_id}: API returned {response.status_code}: {response.text}"
            )
            return {
                "id": profile_id,
                "name": f"Profile {profile_id} (Error)",
                "error": f"HTTP {response.status_code}",
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Profile {profile_id}: Request error: {e}")
        return {
            "id": profile_id,
            "name": f"Profile {profile_id} (Network Error)",
            "error": str(e),
        }
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"❌ Profile {profile_id}: Unexpected error: {e}")
        return {
            "id": profile_id,
            "name": f"Profile {profile_id} (Error)",
            "error": str(e),
        }


def get_multiple_profiles_info(profile_ids: List[str]) -> Dict[str, Dict]:
    """Get information for multiple profiles from NextDNS API.

    Args:
        profile_ids (list): List of NextDNS profile IDs

    Returns:
        dict: Dictionary mapping profile_id to profile information
    """
    profiles = {}

    for profile_id in profile_ids:
        profile_info = get_profile_info(profile_id)
        if profile_info:
            profiles[profile_id] = profile_info
        else:
            # Fallback info if API call fails
            profiles[profile_id] = {
                "id": profile_id,
                "name": f"Profile {profile_id}",
                "error": "Failed to fetch profile information",
            }

    logger.info(f"🧱 Fetched information for {len(profiles)} profiles")
    return profiles


def get_configured_profile_ids() -> List[str]:
    """Get the list of configured profile IDs from environment.

    Returns:
        list: List of configured profile IDs
    """
    profile_ids_env = os.getenv("PROFILE_IDS", "")
    if not profile_ids_env:
        return []

    profile_ids = [pid.strip() for pid in profile_ids_env.split(",") if pid.strip()]
    logger.debug(f"🧱 Configured profiles from env: {profile_ids}")
    return profile_ids
