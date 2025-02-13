from PyQt5.QtCore import QObject, QThread # type: ignore
from modes.buildings_mode import BuildingsMode
from modes.province_mode import ProvinceMode
from modes.army_mode import ArmyMode
from modes.roads_mode import RoadsMode
from modes.new_mode  import NewMode


class ModeManager(QObject):
    """Zarządza aktywnym trybem i deleguje zdarzenia do aktywnego modu."""

    def __init__(self, map_controller):
        super().__init__()
        self.map_controller = map_controller
        self.layer_manager = self.map_controller.layer_manager
        self.snapshot_manager = self.map_controller.snapshot_manager
        self.roads = True
        # Inicjalizacja trybów
        self.active_state = None
        self.active_mode = None
        self.active_mode_name = None
        self.modes = {}
        self._init_modes()

    def _init_modes(self):
        self.roads_mode = RoadsMode(self, self.map_controller)
        self.army_mode = ArmyMode(self, self.map_controller)
        self.province_mode = ProvinceMode(self, self.map_controller)
        self.buildings_mode = BuildingsMode(self, self.map_controller)
        #self.new_mode = NewMode(self, map_controller)


    def set_mode(self, mode_name=None):
        """Ustawia aktywny tryb."""
        self.active_mode = self.modes.get(mode_name)
        self.active_mode_name = mode_name
        self.active_mode.active_state = self.active_state
        self.active_mode.setup_menu()

    def update_snap(self, layer_name):
        def run():
            if layer_name == "buildings":
                self.map_controller.mode_manager.buildings_mode.start_buildings_timer()
            if layer_name == "army":
                self.map_controller.mode_manager.army_mode.start_army_timer()
        QThread(run())

    def count_cities_by_state(self):
        if hasattr(self, 'buildings_mode'):
            self.buildings_mode.count_cities_by_state()

    def init_modes(self):
        def process():
            self.province_mode.sample_provinces()
            self.buildings_mode.find_cities()
            self.buildings_mode.count_cities_by_state()
            self.army_mode.find_army()
            self.army_mode.count_armies_by_state()
        thread = QThread(process())

    def get_mode(self):
        return self.active_mode_name

    def handle_event(self, event):
        """Przekazuje zdarzenie do aktywnego trybu."""
        if self.active_mode:
            self.active_mode.handle_event(event)

    def update_active_state(self, state):
        """Aktualizuje aktywny stan w trybie prowincji."""
        if state is None:
            return
        else:
            self.active_state = state
            if self.active_mode:
                self.active_mode.active_state = state
                self.active_mode.setup_menu()
