from controllers.tools import flood_fill, PixelSampler
from controllers.data import DATA
from PyQt5.QtGui import QColor
from modes.base_mode import Mode
from PyQt5.QtWidgets import QPushButton # type: ignore
from PyQt5.QtCore import QSize # type: ignore

class ProvinceMode(Mode):
    """Obsługuje tryb prowincji."""
    def __init__(self, mode_manager, map_controller):
        super().__init__(map_controller)
        self.mode_manager = mode_manager
        self.sampled_color = None
        self.active_state = None
        self.layer = self.layer_manager.get_layer("province")
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
        color_preview.setFixedSize(QSize(60, 60))
        lighter_color_preview = QPushButton()
        lighter_color_preview.setFixedSize(QSize(40, 40))


        color = None
        if self.active_state != self.mode_manager.active_state:
            self.active_state = self.mode_manager.active_state
            color = self.active_state.color
            self.sampled_color = None
        if self.active_state and hasattr(self.active_state, 'color'):
            color = self.active_state.color
        if self.sampled_color:
            color = self.sampled_color

        if color:
            color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
            lighter_color = color.lighter(200).toHsv()
            lighter_color.setHsv(lighter_color.hue(), int(lighter_color.saturation() * 0.5), lighter_color.value())
            lighter_color = lighter_color.toRgb()
            lighter_color_preview.setStyleSheet(f"background-color: {lighter_color.name()}; border: 1px solid black;")
        else:
            color_preview.setStyleSheet(f"border: 1px solid black;")
            lighter_color_preview.setStyleSheet(f"border: 1px solid black;")

        # Connect buttons to set sampled color
        color_preview.clicked.connect(lambda: self.set_sampled_color(color))
        lighter_color_preview.clicked.connect(lambda: self.set_sampled_color(lighter_color))

        self.map_controller.button_panel.update_dynamic_menu([color_preview, lighter_color_preview])

    def set_sampled_color(self, color):
        """Ustawia self.sampled_color na podany kolor."""
        self.sampled_color = color

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
