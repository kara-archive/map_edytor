from controllers.tools import flood_fill
from modes.base_mode import Mode
from PyQt5.QtCore import QSize  # type: ignore
from PyQt5.QtGui import QColor  # type: ignore
from PyQt5.QtWidgets import QPushButton, QButtonGroup  # type: ignore


class BiomeMode(Mode):
    """Obsługuje kolorowanie biomów na warstwie pod prowincjami."""

    BIOMES = {
        "Woda": QColor(64, 128, 191),
        "Pustynia": QColor(214, 179, 101),
        "Las": QColor(46, 125, 50),
        "Plain": QColor(139, 195, 74),
        "Góry": QColor(141, 141, 141),
    }

    def __init__(self, mode_manager, map_controller):
        self.name = "biome"
        super().__init__(map_controller)
        self.mode_manager = mode_manager
        self.register_mode(z=0, label="Biomy", short="b")
        self.fill_color = self.BIOMES["Woda"]

    def handle_event(self, event):
        if event.button != "left":
            return

        if event.event_type == "click":
            self.start_snap(self.name)

        if event.event_type in {"click", "move"}:
            self.color_fill(event.x, event.y, self.fill_color)

        if event.event_type == "release":
            self.end_snap(self.name)

    def setup_menu(self):
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)

        buttons = []
        for label, color in self.BIOMES.items():
            button = QPushButton(label[0])
            button.setFixedSize(QSize(44, 44))
            button.setCheckable(True)
            button.setStyleSheet(f"background-color: {color.name()}; color: black")
            button.clicked.connect(lambda _, selected_color=color: self.set_color(selected_color))
            self.button_group.addButton(button)
            buttons.append(button)
            if color == self.fill_color:
                button.setChecked(True)

        self.request_menu_update.emit(buttons)

    def set_color(self, color):
        self.fill_color = color

    def color_fill(self, x, y, color):
        layer = self.layer_manager.get_layer(self.name)
        if layer is None:
            return
        if not (0 <= x < layer.width() and 0 <= y < layer.height()):
            return
        if layer.pixelColor(x, y).alpha() == 0 and self.map_controller.cv_image is not None:
            layer = self.map_controller.cv_image.copy()

        self.layer_manager.layers[self.name] = flood_fill(layer, x, y, color)
        self.layer_manager.refresh_layer(self.name)
