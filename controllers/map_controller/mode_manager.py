from PyQt5.QtCore import QObject, QThread, pyqtSignal # type: ignore
from modes.buildings_mode import BuildingsMode
from modes.province_mode import ProvinceMode
from modes.biome_mode import BiomeMode
from modes.army_mode import ArmyMode
from modes.roads_mode import RoadsMode
from modes.new_mode  import NewMode

class ModeManager(QObject):
    """Zarządza aktywnym trybem i deleguje zdarzenia do aktywnego modu."""
    menu_update_requested = pyqtSignal(list)

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
        # Inicjalizacja domyślnych trybów
        self.register_mode(RoadsMode(self, self.map_controller))
        self.register_mode(ArmyMode(self, self.map_controller))
        self.register_mode(BiomeMode(self, self.map_controller))
        self.register_mode(ProvinceMode(self, self.map_controller))
        self.register_mode(BuildingsMode(self, self.map_controller))
        
        # Dla wstecznej kompatybilności w innych miejscach kodu (update_snap, init_modes)
        self.roads_mode = self.modes.get("roads")
        self.army_mode = self.modes.get("army")
        self.biome_mode = self.modes.get("biome")
        self.province_mode = self.modes.get("province")
        self.buildings_mode = self.modes.get("buildings")

    def register_mode(self, mode_instance):
        """Dynamicznie rejestruje tryb edycji."""
        mode_name = mode_instance.name
        self.modes[mode_name] = mode_instance
        self.map_controller.layer_manager.Z_VALUES[mode_name] = mode_instance.z_value
        if mode_instance.label:
            self.map_controller.buttons_info.append((mode_instance.label, mode_name))
        if mode_instance.short:
            self.map_controller.shortcuts[mode_instance.short] = mode_name
            
        # Połącz sygnał od modu
        mode_instance.request_menu_update.connect(self.menu_update_requested.emit)


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
