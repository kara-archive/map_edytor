import copy

class MapData(object):
    """Hierarchical database storing coordinates of different types of objects."""
    def __init__(self):
        self.buildings = self.Buildings()
        self.army = self.Army()
        self.provinces = self.Provinces()
        self.province_mode = None  # Add province_mode for easier restoration

    class Buildings:
        """Przechowuje różne typy budynków."""
        def __init__(self):
            self.cities = []
            self.towns = []
            self.farms = []

    class Army:
        """Przechowuje współrzędne jednostek wojskowych."""
        def __init__(self):
            self.units = []

    class Provinces(list):
        """Przechowuje współrzędne prowincji."""
        def __init__(self, *args):
            super().__init__(*args)
            self.extend([])
