from controllers.tools import flood_fill, PixelSampler
from controllers.data import DATA
from PyQt5.QtGui import QImage, QColor, QPainter, QPixmap
from modes.base_mode import Mode
from PyQt5.QtWidgets import QPushButton # type: ignore
from PyQt5.QtCore import QSize

class ProvinceMode(Mode):
    """Obsługuje tryb prowincji."""
    def __init__(self, mode_manager, map_controller):
        super().__init__(map_controller)
        self.map_controller = map_controller
        self.sampled_color = None
        self.active_state = None
        self.mode_manager = mode_manager
        self.layer = self.map_controller.layer_manager.get_layer("province")
        self.fill_color = None

    def handle_event(self, event):
        """Obsługuje zdarzenia w trybie prowincji."""
        if self.active_state != self.mode_manager.active_state:
            self.active_state = self.mode_manager.active_state
            self.sampled_color = None
            self.setup_menu()

        if event.event_type == "click" and event.button == "right":
             self.get_color_at(event.x, event.y)
             self.setup_menu()
        elif event.button == "left":
            if self.sampled_color:
                self.fill_color = self.sampled_color
            elif self.active_state and hasattr(self.active_state, 'color'):
                self.fill_color = self.active_state.color
            else:
                print("ProvinceMode: Brak aktywnego państwa lub koloru próbki.")
                return
            
            if event.event_type == "click":
                self.start_snap("province")
            self.color_fill(event.x, event.y, self.fill_color)
            if event.event_type == "release":
                self.end_snap("province")
                self.sample_provinces()

    def setup_menu(self):
        color_preview = QPushButton()
        color_preview.setFixedSize(QSize(20, 20))
        color = None
        if self.active_state != self.mode_manager.active_state:
            self.active_state = self.mode_manager.active_state
            color = self.active_state.color
        if self.active_state and hasattr(self.active_state, 'color'):
            color = self.active_state.color
        if self.sampled_color:
            color = self.sampled_color
        if color:
            color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")

        self.map_controller.button_panel.update_dynamic_menu([color_preview])

    def color_fill(self, x, y, color):
        layer = self.map_controller.layer_manager.get_layer("province")
        color = QColor(color)
        layer = flood_fill(layer, x, y, self.fill_color.getRgb()[:3])
        self.map_controller.layer_manager.refresh_layer("province")


    def sample_provinces(self):
        states = self.map_controller.state_controller.get_states()
        image = self.mode_manager.layer_manager.layers.get("province")
        province_counts = PixelSampler(image, DATA.provinces, states)
        for state in states:
            state.provinces = province_counts.get(state.name, 0)

    def get_color_at(self, x, y):
        layer = self.map_controller.layer_manager.get_layer("province")
        if layer is None:
            return None
        self.sampled_color = QColor(layer.pixel(x, y))
