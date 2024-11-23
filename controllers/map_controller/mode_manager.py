from PyQt5.QtCore import QObject
from modes.buildings_mode import BuildingsMode
from modes.province_mode import ProvinceMode
from modes.army_mode import ArmyMode
from modes.roads_mode import RoadsMode


class ModeManager(QObject):
    """Zarządza aktywnym trybem i deleguje zdarzenia do aktywnego modu."""

    def __init__(self, map_controller,):
        super().__init__()
        self.map_controller = map_controller
        self.layer_manager = self.map_controller.layer_manager
        self.snapshot_manager = self.map_controller.snapshot_manager
        # Inicjalizacja trybów
        self.buildings_mode = BuildingsMode(self, map_controller)
        self.province_mode = ProvinceMode(self, map_controller)
        self.army_mode = ArmyMode(self, map_controller)
        self.roads_mode = RoadsMode(self, map_controller)
        self.active_state = None
        self.active_mode = None
        self.active_mode_name = None
        self.modes = {
            "buildings": self.buildings_mode,
            "province": self.province_mode,
            "army": self.army_mode,
            "roads": self.roads_mode,
        }

    def set_mode(self, mode_name=None):
        """Ustawia aktywny tryb."""
        self.active_mode = self.modes.get(mode_name)
        self.active_mode_name = mode_name

    def get_mode(self):
        return self.active_mode_name

    def handle_event(self, event):
        """Przekazuje zdarzenie do aktywnego trybu."""
        if self.active_mode:
            self.active_mode.handle_event(event)

    def update_active_state(self, state):
        """Aktualizuje aktywny stan w trybie prowincji."""
        if state is None:
            print("ProvinceMode: Ustawiony stan jest None!")
        else:
            self.active_state = state

    def get_active_state(self,):
        return self.active_state

class Mode:
    """
    Klasa bazowa dla trybów zarządzania mapą.
    """
    def __init__(self, map_controller, name, z_value=0):
        self.name = name
        self.z_value = z_value
        self.map_controller = map_controller
        self.layer_manager = map_controller.layer_manager

    def initialize_layer(self, cv_image, scene):
        """
        Inicjalizuje warstwę specyficzną dla tego trybu.
        """
        height, width, _ = cv_image.shape
        self.layer_manager.add_layer(self.name, width, height, self.z_value, scene)
        print(f"Zainicjalizowano warstwę '{self.name}' z Z_VALUE: {self.z_value}")

    def handle_event(self, event):
        """
        Obsługuje zdarzenia. Wymagane do zaimplementowania w podklasach.
        """
        raise NotImplementedError

    def activate(self):
        """Wywoływana przy aktywacji trybu."""
        print(f"Tryb '{self.name}' aktywowany.")

    def deactivate(self):
        """Wywoływana przy dezaktywacji trybu."""
        print(f"Tryb '{self.name}' dezaktywowany.")
