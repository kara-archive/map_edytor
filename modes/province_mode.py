from controllers.tools import flood_fill, PixelSampler
from controllers.data import DATA
from PyQt5.QtGui import QColor
from modes.base_mode import Mode
from PyQt5.QtWidgets import QPushButton, QButtonGroup # type: ignore
from PyQt5.QtCore import QSize # type: ignore

class ProvinceMode(Mode):
    """Obsługuje tryb prowincji."""
    def __init__(self, mode_manager, map_controller):
        self.name = "province"
        super().__init__(map_controller)
        self.mode_manager = mode_manager
        self.register_mode(z=0,label="Prowincje")
        self.layer = self.layer_manager.get_layer(self.name)
        self.fill_color = None
        self.map_colors = ['#000000','#446ba3','#343434']

    def handle_event(self, event):
        """Obsługuje zdarzenia w trybie prowincji."""
        if event.event_type == "click" and event.button == "right":
             self.get_color_at(event.x, event.y)
             self.setup_menu()
        elif event.button == "left":
            if event.event_type == "click":
                self.start_snap(self.name)

            self.color_fill(event.x, event.y, self.fill_color)

            if event.event_type == "release":
                self.end_snap(self.name)
                self.sample_provinces()
                self.mode_manager.buildings_mode.count_cities_by_state()

    def setup_menu(self):
        # Tworzenie QButtonGroup
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)  # Tylko jeden przycisk może być zaznaczony w danym momencie

        buttons = []

        color_preview = QPushButton()
        color_preview.setFixedSize(QSize(40, 40))
        color_preview.setCheckable(True)
        lighter_color_preview = QPushButton()
        lighter_color_preview.setFixedSize(QSize(40, 40))
        lighter_color_preview.setCheckable(True)


        if self.active_state and hasattr(self.active_state, 'color'):
            self.fill_color = self.active_state.color

        if self.fill_color:
            color = self.fill_color

            color_preview.setStyleSheet(f"background-color: {color.name()}")
            self.button_group.addButton(color_preview)
            buttons.append(color_preview)
            color_preview.clicked.connect(lambda: self.set_color(color))

            lighter_color = self.fill_color.lighter(150).toHsv()
            lighter_color.setHsv(lighter_color.hue(), int(lighter_color.saturation() * 0.5), lighter_color.value())
            lighter_color = lighter_color.toRgb()
            lighter_color_preview.setStyleSheet(f"background-color: {lighter_color.name()}")
            self.button_group.addButton(lighter_color_preview)
            buttons.append(lighter_color_preview)
            lighter_color_preview.clicked.connect(lambda: self.set_color(lighter_color))

        self.map_controller.button_panel.update_dynamic_menu(buttons)

    def set_color(self, color):
        """Ustawia self.sampled_color na podany kolor."""
        self.fill_color = color

    def color_fill(self, x, y, color):
        layer = self.map_controller.layer_manager.get_layer(self.name)
        #color = QColor(color)
        if color.name() not in self.map_colors and QColor(layer.pixel(x, y)).name() not in self.map_colors:
            layer = flood_fill(layer, x, y, color)
            self.map_controller.layer_manager.refresh_layer(self.name)


    def sample_provinces(self):
        states = self.map_controller.state_controller.get_states()
        image = self.mode_manager.layer_manager.layers.get(self.name)
        province_counts = PixelSampler(image, DATA.provinces, states)
        for state in states:
            state.provinces = province_counts.get(state.name, 0)

    def get_color_at(self, x, y):
        layer = self.map_controller.layer_manager.get_layer(self.name)
        if layer is None:
            return None
        self.fill_color = QColor(layer.pixel(x, y))
        self.active_state = None
        self.setup_menu()
