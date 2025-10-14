# file: backend/profile_service.py
import os
from typing import Dict, List, Optional

import requests
from logging_config import get_logger

logger = get_logger(__name__)

API_KEY = os.getenv("API_KEY")


def _create_error_profile_info(profile_id: str, name_suffix: str, error: str) -> Dict:
    """Helper function to create error profile information."""
    return {
        "id": profile_id,
        "name": f"Profile {profile_id} {name_suffix}",
        "error": error,
    }


def _handle_api_response(response: requests.Response, profile_id: str) -> Dict:
    """Helper function to handle API response based on status code."""
    if response.status_code == 200:
        profile_data = response.json().get("data", {})
        logger.debug(f"✅ Profile {profile_id}: {profile_data.get('name', 'Unknown')}")
        return {
            "id": profile_id,
            "name": profile_data.get("name", f"Profile {profile_id}"),
            "fingerprint": profile_data.get("fingerprint"),
            "created": profile_data.get("created"),
            "updated": profile_data.get("updated"),
        }

    if response.status_code == 404:
        logger.warning(f"⚠️  Profile {profile_id} not found (404)")
        return _create_error_profile_info(
            profile_id, "(Not Found)", "Profile not found"
        )

    if response.status_code == 403:
        logger.warning(f"⚠️  Access denied to profile {profile_id} (403)")
        return _create_error_profile_info(
            profile_id, "(Access Denied)", "Access denied"
        )

    # Handle all other status codes
    logger.error(
        f"❌ Profile {profile_id}: API returned {response.status_code}: {response.text}"
    )
    return _create_error_profile_info(
        profile_id, "(Error)", f"HTTP {response.status_code}"
    )


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
        return _handle_api_response(response, profile_id)

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Profile {profile_id}: Request error: {e}")
        return _create_error_profile_info(profile_id, "(Network Error)", str(e))
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"❌ Profile {profile_id}: Unexpected error: {e}")
        return _create_error_profile_info(profile_id, "(Error)", str(e))


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
