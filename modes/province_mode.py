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
        self.layer = self.layer_manager.get_layer("province")
        self.fill_color = None

    def handle_event(self, event):
        """Obsługuje zdarzenia w trybie prowincji."""
        if event.event_type == "click" and event.button == "right":
             self.get_color_at(event.x, event.y)
             self.setup_menu()
        elif event.button == "left":
            if event.event_type == "click":
                self.start_snap("province")

            self.color_fill(event.x, event.y, self.fill_color)

            if event.event_type == "release":
                self.end_snap("province")
                self.sample_provinces()

    def setup_menu(self):
        color_preview = QPushButton()
        color_preview.setFixedSize(QSize(40, 40))
        lighter_color_preview = QPushButton()
        lighter_color_preview.setFixedSize(QSize(40, 40))


        if self.active_state and hasattr(self.active_state, 'color'):
            self.fill_color = self.active_state.color

        if self.fill_color:
            color_preview.setStyleSheet(f"background-color: {self.fill_color.name()}; border: 1px solid white;")
            lighter_color = self.fill_color.lighter(150).toHsv()
            lighter_color.setHsv(lighter_color.hue(), int(lighter_color.saturation() * 0.5), lighter_color.value())
            lighter_color = lighter_color.toRgb()
            lighter_color_preview.setStyleSheet(f"background-color: {lighter_color.name()}; border: 1px solid black;")

            # Connect buttons to set sampled color
            color_preview.clicked.connect(lambda: self.set_sampled_color(self.fill_color))
            lighter_color_preview.clicked.connect(lambda: self.set_sampled_color(lighter_color))

            self.map_controller.button_panel.update_dynamic_menu([color_preview, lighter_color_preview])

    def set_sampled_color(self, color):
        """Ustawia self.sampled_color na podany kolor."""
        self.fill_color = color

    def color_fill(self, x, y, color):
        layer = self.map_controller.layer_manager.get_layer("province")
        color = QColor(color)
        if color.getRgb() != (0, 0, 0, 255) and QColor(layer.pixel(x, y)) not in [QColor(0, 0, 0, 255), QColor(68, 107, 163, 255), QColor(52, 52, 52, 255)]:
            layer = flood_fill(layer, x, y, color)
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
        self.fill_color = QColor(layer.pixel(x, y))
        self.active_state = None
        self.setup_menu()
