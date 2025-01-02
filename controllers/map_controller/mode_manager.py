from PyQt5.QtCore import QObject
from modes.province_mode import ProvinceMode



class ModeManager(QObject):
    """Zarządza aktywnym trybem i deleguje zdarzenia do aktywnego modu."""

    def __init__(self, map_controller,):
        super().__init__()
        self.map_controller = map_controller
        self.layer_manager = self.map_controller.layer_manager
        self.snapshot_manager = self.map_controller.snapshot_manager
        # Inicjalizacja trybów
        self.province_mode = ProvinceMode(self, map_controller)
        self.active_state = None
        self.active_mode = None
        self.active_mode_name = None
        self.modes = {
            "province": self.province_mode,
        }
        self.layer_manager.Z_VALUES = {
            "province": 0,
            "roads": 1,

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
