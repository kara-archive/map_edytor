from controllers.tools import flood_fill, PixelSampler
from controllers.data import DATA
from PyQt5.QtGui import QImage, QColor, QPainter, QPixmap
from modes.base_mode import Mode

class ProvinceMode(Mode):
    """Obsługuje tryb prowincji."""
    def __init__(self, mode_manager, map_controller):
        super().__init__(map_controller)
        self.map_controller = map_controller
        self.sampled_color = None
        self.active_state = None
        self.mode_manager = mode_manager
        self.layer = self.map_controller.layer_manager.get_layer("province")

    def handle_event(self, event):
        """Obsługuje zdarzenia w trybie prowincji."""
        if self.active_state != self.mode_manager.active_state:
            self.active_state = self.mode_manager.active_state
            self.sampled_color = None
        if event.event_type == "click":
            self.start_snap("province")
        if event.event_type == "click" and event.button == "right":
             self.get_color_at(event.x, event.y)
        elif event.button == "left":
            if self.sampled_color:
                fill_color = self.sampled_color
            elif self.active_state and hasattr(self.active_state, 'color'):
                fill_color = self.active_state.color
            else:
                print("ProvinceMode: Brak aktywnego państwa lub koloru próbki.")
                return
            self.color_fill(event.x, event.y, fill_color)
        if event.event_type == "release":
            self.end_snap("province")
            self.sample_provinces()

    def setup_menu(self):
        self.map_controller.button_panel.update_dynamic_menu([])


    def color_fill(self, x, y, color):
        layer = self.map_controller.layer_manager.get_layer("province")
        fill_color = QColor(color)
        layer = flood_fill(layer, x, y, fill_color.getRgb()[:3])
        self.map_controller.layer_manager.refresh_layer("province")


    def sample_provinces(self):
        states = self.map_controller.state_controller.get_states()
        image = self.mode_manager.layer_manager.layers.get("province")
        province_counts = PixelSampler(image, DATA.provinces, states)

        # Przypisanie liczby prowincji do obiektów State
        for state in states:
            state.provinces = province_counts.get(state.name, 0)

    def get_color_at(self, x, y):
        layer = self.map_controller.layer_manager.get_layer("province")
        if layer is None:
            return None
        self.sampled_color = QColor(layer.pixel(x, y))
