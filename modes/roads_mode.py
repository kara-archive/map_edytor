from controllers.tools import erase_area, DrawPath
from .base_mode import Mode
from PyQt5.QtWidgets import QPushButton, QButtonGroup # type: ignore
from PyQt5.QtGui import QColor

class RoadsMode(Mode):
    """Obsługuje tryb rysowania dróg z podglądem na żywo."""

    def __init__(self, mode_manager, map_controller):
        super().__init__(map_controller)
        self.mode_manager = mode_manager
        self.path = None
        self.preview_item = None
        self.size = 2
        self.color = QColor(128, 128, 128, 255)

    def handle_event(self, event):
        """Obsługuje zdarzenia myszy."""
        if event.event_type == "click":
            self.start_snap("roads")
        if event.button == "right" and event.event_type in {"click", "move"}:
            self._zmazuj(event)
        elif event.button == "left":
            self._rysuj(event)
        if event.event_type == "release":
            self.layer_manager.refresh_layer("roads")
            self.mode_manager.buildings_mode.count_cities_by_state()
            self.end_snap("roads")


    def _zmazuj(self, event):
        """Obsługuje zdarzenia związane z usuwaniem (prawy przycisk myszy)."""
        roads_layer = self.layer_manager.get_layer("roads")
        radius = 15  # Promień gumki
        erase_area(roads_layer, event.x, event.y, radius, radius)
        self.layer_manager.refresh_layer("roads")

    def setup_menu(self):

        # Tworzenie QButtonGroup
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)  # Tylko jeden przycisk może być zaznaczony w danym momencie

        buttons = []

        for i in range(1, 5):
            button = QPushButton(str(i))
            button.setFixedSize(40, 40)  # Przyciski są kwadratowe
            button.setCheckable(True)
            button.clicked.connect(lambda _, size=i: self.set_size(size))
            self.button_group.addButton(button)
            buttons.append(button)
            if button.text() == self.size:
                button.setChecked(True)

        colors = ["gray","dimgray", "lightgrey", "saddlebrown"]

        for i in colors:
            button = QPushButton()
            button.setStyleSheet(f"background-color: {i}")
            button.setFixedSize(40, 40)  # Przyciski są kwadratowe
            button.setCheckable(True)
            button.clicked.connect(lambda _, color=i: self.set_color(color))
            self.button_group.addButton(button)
            buttons.append(button)
            if button.text() == self.size:
                button.setChecked(True)

        self.map_controller.button_panel.update_dynamic_menu(buttons)

    def set_size(self, size):
        self.size = size

    def set_color(self, color):
        self.color = QColor(color)
    # Usage in RoadsMode
    def _rysuj(self, event):
        """Obsługuje zdarzenia związane z rysowaniem (lewy przycisk myszy)."""
        if not hasattr(self, 'draw_path'):
            self.draw_path = DrawPath(self.layer_manager.get_layer("roads"), color=self.color, width=self.size, scene=self.map_controller.scene)

        self.draw_path.draw_path(event)

        if event.event_type == "release":
            delattr(self, 'draw_path')
