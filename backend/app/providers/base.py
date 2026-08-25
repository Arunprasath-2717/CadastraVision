from abc import ABC, abstractmethod
from typing import List, Dict, Any

class GeoDataProvider(ABC):
    @abstractmethod
    def get_buildings(self, bbox: tuple[float, float, float, float]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_roads(self, bbox: tuple[float, float, float, float]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_fields(self, bbox: tuple[float, float, float, float]) -> List[Dict[str, Any]]:
        pass

    def get_features(self, bbox: tuple[float, float, float, float]) -> List[Dict[str, Any]]:
        """Fetch all feature types and return a combined list."""
        buildings = self.get_buildings(bbox)
        roads = self.get_roads(bbox)
        fields = self.get_fields(bbox)
        return buildings + roads + fields
