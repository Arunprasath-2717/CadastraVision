import requests
from typing import List, Dict, Any
from app.providers.base import GeoDataProvider
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class OvertureProvider(GeoDataProvider):
    def __init__(self):
        self.api_key = settings.OVERTURE_API_KEY
        self.base_url = "https://api.overturemapsapi.com"
        self.headers = {"x-api-key": self.api_key} if self.api_key else {}

    def _fetch_theme(self, theme: str, bbox: tuple[float, float, float, float]) -> List[Dict[str, Any]]:
        if not self.api_key:
            logger.warning("No Overture API key configured.")
            return []

        minLon, minLat, maxLon, maxLat = bbox
        
        # Overture API typically accepts bbox or lat/lng/radius. We use bbox if supported.
        url = f"{self.base_url}/{theme}"
        params = {
            "bbox": f"{minLon},{minLat},{maxLon},{maxLat}",
            "limit": 1000
        }

        try:
            res = requests.get(
                url, 
                headers=self.headers, 
                params=params, 
                timeout=settings.OVERTURE_TIMEOUT_SECONDS
            )
            res.raise_for_status()
            data = res.json()
            # Assuming GeoJSON response
            if "features" in data:
                return data["features"]
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {theme} from Overture: {e}")
            return []

    def get_buildings(self, bbox: tuple[float, float, float, float]) -> List[Dict[str, Any]]:
        return self._fetch_theme("buildings", bbox)

    def get_roads(self, bbox: tuple[float, float, float, float]) -> List[Dict[str, Any]]:
        return self._fetch_theme("transportation", bbox)

    def get_fields(self, bbox: tuple[float, float, float, float]) -> List[Dict[str, Any]]:
        return self._fetch_theme("base", bbox)
