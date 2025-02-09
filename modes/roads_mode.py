from controllers.tools import erase_area, DrawPath
from .base_mode import Mode
from PyQt5.QtWidgets import QPushButton, QButtonGroup # type: ignore
from PyQt5.QtGui import QColor

class RoadsMode(Mode):
    """Obsługuje tryb rysowania dróg z podglądem na żywo."""

    def __init__(self, mode_manager, map_controller):
        self.name = "roads"
        super().__init__(map_controller)
        self.mode_manager = mode_manager
        self.register_mode(z=1,label="Drogi", short="r")
        self.size = 2 #domyślna grubość
        self.colors = ["gray","dimgray", "lightgrey", "saddlebrown"] #kolory
        self.color = QColor(self.colors[0]) #domyślny kolor
        self.i=0

    def handle_event(self, event):
        """Obsługuje zdarzenia myszy."""
        if event.event_type == "click":
            self.start_snap(self.name)
        if event.button == "right" and event.event_type in {"click", "move"}:
            self._zmazuj(event)
        elif event.button == "left":
            self._rysuj(event)
        if event.event_type == "release":
            self.layer_manager.refresh_layer(self.name)
            self.end_snap(self.name)


    def _zmazuj(self, event):
        """Obsługuje zdarzenia związane z usuwaniem (prawy przycisk myszy)."""
        roads_layer = self.layer_manager.get_layer(self.name)
        a, b = 4, 4
        if event.event_type == 'move':
            if self.i >= 5:
                a=8
                b=8
            else:
                self.i += 1
        else:
            a=4
            b=4
            self.i=0

        erase_area(roads_layer, event.x, event.y, a, b)
        self.layer_manager.refresh_layer(self.name)

    def setup_menu(self):
        state_colors = self.map_controller.state_controller.get_states_colors()
        state_names = self.map_controller.state_controller.get_states_names()
        # Tworzenie QButtonGroup
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)  # Tylko jeden przycisk może być zaznaczony w danym momencie

        buttons = []

        for i in [1, 2, 4, 8,]:
            button = QPushButton(str(i))
            button.setFixedSize(40, 40)  # Przyciski są kwadratowe
            button.setCheckable(True)
            button.clicked.connect(lambda _, size=i: self.set_size(size))
            self.button_group.addButton(button)
            buttons.append(button)
            if button.text() == '2':
                button.setChecked(True)

        colors = self.colors
        # Tworzenie QButtonGroup
        self.button_group2 = QButtonGroup()
        self.button_group2.setExclusive(True)  # Tylko jeden przycisk może być zaznaczony w danym momencie
        buttons2 = []

        for i in colors:
            button = QPushButton()
            button.setStyleSheet(f"background-color: {i}")
            button.setFixedSize(40, 40)  # Przyciski są kwadratowe
            button.setCheckable(True)
            button.clicked.connect(lambda _, color=i: self.set_color(color))
            self.button_group2.addButton(button)
            buttons.append(button)
            if i == self.colors[0]:
                button.setChecked(True)

        for i in range(len(state_names)):
            name = state_names[i]
            button = QPushButton(name[0])
            button.setStyleSheet(f"background-color: {state_colors[i]}")
            button.setFixedSize(40, 40)  # Przyciski są kwadratowe
            button.setCheckable(True)
            button.clicked.connect(lambda _, color=state_colors[i]: self.set_color(color))
            self.button_group2.addButton(button)
            buttons.append(button)
            if i == self.colors[0]:
                button.setChecked(True)


        self.map_controller.button_panel.update_dynamic_menu(buttons)

    def set_size(self, size):
        self.size = size

    def set_color(self, color):
        self.color = QColor(color)

    def _rysuj(self, event):
        """Obsługuje zdarzenia związane z rysowaniem (lewy przycisk myszy)."""
        if not hasattr(self, 'draw_path'):
            self.draw_path = DrawPath(self.layer_manager.get_layer(self.name), color=self.color, width=self.size, scene=self.map_controller.scene, z_value=1)

        self.draw_path.draw_path(event)

        if event.event_type == "release":
            delattr(self, 'draw_path')
