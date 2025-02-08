from PyQt5.QtGui import QImage, QColor, QPixmap, QIcon # type: ignore
from PyQt5.QtWidgets import QPushButton, QButtonGroup # type: ignore
from PyQt5.QtCore import QSize, QTimer
from controllers.tools import erase_area, draw_icon, find_icons, PixelSampler, recolor_icon
from modes.base_mode import Mode
import os
from threading import Thread

class ArmyMode(Mode):
    """Obsługuje tryb armii."""
    def __init__(self, mode_manager, map_controller):
        self.name = "army"
        super().__init__(map_controller)
        self.mode_manager = mode_manager
        self.register_mode(3)
        self.army_icons = self.load_army_icons("icons")
        self.active_icon = next(iter(self.army_icons.values()))
        self.active_icon_name = next(iter(self.army_icons.keys()))
        self.army_positions = {}
        self.i = 0

        if self.active_icon.isNull():
            raise ValueError("Nie udało się załadować ikony: icons/a_army.png")
        self.active_state = None

    def load_army_icons(self, folder):
        """Ładuje ikony budynków z folderu."""
        building_icons = {}
        for filename in sorted(os.listdir(folder)):
            if "a_" in filename and filename.endswith(".png"):
                icon_name = filename.split("a_")[1][:-4]  # Usuwa wszystko przed "a_" i ".png" z końca
                icon_path = os.path.join(folder, filename)
                building_icons[icon_name] = QImage(icon_path)
        return building_icons

    def get_icon_from_image(self, image):
        pixmap = QPixmap.fromImage(image)
        return QIcon(pixmap)

    def handle_event(self, event):
        if event.event_type == "click":
            self.start_snap("army")
        if event.event_type == "click" and event.button == "left":
            self.add_army(event.x, event.y)
        elif event.button == "right":
            self.erase_army(event)
        if event.event_type == "release":
            self.end_snap("army")
            self.count_armies_by_state()

    def add_army(self, x, y):
        """Dodaje ikonę armii na warstwę z kolorem wybranego państwa."""
        army_layer = self.map_controller.layer_manager.get_layer("army")

        # Pobierz aktywny kolor państwa z ModeManager
        active_state = self.active_state
        if active_state is None or not hasattr(active_state, "color"):
            print("Brak aktywnego państwa lub koloru.")
            return
        state_color = active_state.color.getRgb()[:3]  # Pobierz RGB

        # Przekształć ikonę armii
        recolored_icon = recolor_icon(self.active_icon.copy(), state_color)

        army_layer = draw_icon(army_layer, recolored_icon, x, y)
        self.map_controller.layer_manager.refresh_layer("army")
        self.add_army_position(x, y, self.active_icon_name)

    def erase_army(self, event):
        """Obsługuje zdarzenia związane z usuwaniem (prawy przycisk myszy)."""
        army_layer = self.map_controller.layer_manager.get_layer("army")
        a, b = 2, 4
        if event.event_type == 'move':
            if self.i >= 10:
                a=8
                b=8
            else:
                self.i += 1
        else:
            a=2
            b=4
            self.i=0
        army_layer = erase_area(army_layer, event.x, event.y, a, b)
        self.map_controller.layer_manager.refresh_layer("army")
        self.remove_army_positions(event.x, event.y, size=b)


    def setup_menu(self):

        # Tworzenie QButtonGroup
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)  # Tylko jeden przycisk może być zaznaczony w danym momencie

        buttons = []

        for icon_name, icon in self.army_icons.items():
            button = QPushButton()
            button.setIcon(self.get_icon_from_image(icon))  # Konwertuj QImage na QIcon
            button.setIconSize(QSize(40, 40))  # Rozmiar ikony wewnątrz przycisku
            button.setFixedSize(40, 40)  # Przyciski są kwadratowe
            button.setCheckable(True)
            button.clicked.connect(lambda _, name=icon_name: self.set_icon_type(name))
            self.button_group.addButton(button)
            buttons.append(button)
            if icon_name == self.active_icon_name:
                button.setChecked(True)

        self.map_controller.button_panel.update_dynamic_menu(buttons)



    def count_armies_by_state(self):
        """
        Próbkuje piksele w pozycjach budynków różnych typów i wyświetla liczbę budynków każdego typu dla każdego państwa.
        """
        self.set_colors_in_color_label()
        for army_type, positions in self.army_positions.items():
            if not positions:
                positions = [(0, 0)]  # bug, że gdy nie ma budynków to nie odświerza liczby
            i = 0
            pixel_sampler = PixelSampler(
                self.map_controller.layer_manager.layers.get("army"),
                positions,
                self.map_controller.state_controller.get_states()
            )

            for state in self.map_controller.state_controller.get_states():
                setattr(state, army_type, pixel_sampler.get(state.name, 0))

    def add_army_position(self, x, y, army_type):
        if army_type not in self.army_positions:
            self.army_positions[army_type] = []
        self.army_positions[army_type].append((x, y))
    def remove_army_positions(self, x, y, size=10):
        for positions in self.army_positions.values():
            positions[:] = [
                (bx, by) for bx, by in positions
                if not (x - size <= bx <= x + size and y - size <= by <= y + size)
            ]

    def find_army(self):
        """
        Znajduje współrzędne ikon odpowiadających próbce na warstwie z optymalizacją.
        """
        layer = self.map_controller.layer_manager.get_layer("army")

        if layer is None:
            return []

        for army_type, icon in self.army_icons.items():
            self.army_positions[army_type] = find_icons(icon, layer, thresh=10)
    def start_army_timer(self):
        if not hasattr(self, '_army_timer'):
            self._army_timer = QTimer()
            self._army_timer.setSingleShot(True)
            self._army_timer.timeout.connect(self._process_army)

        self._army_timer.start(1000)

    def _process_army(self):
        def process():
            self.find_army()
            self.count_armies_by_state()

        thread = Thread(target=process)
        thread.start()
        thread.join()

    def set_colors_in_color_label(self):
        """Ustawia kolory w label w state, które odpowiadają kolorowi ikony na jej środkowym pixelu"""
        colors = ["crimson", "mediumvioletred", "orangered"]
        i = 0
        for icon in self.army_icons.values():
            if i == len(colors):
                i = 0
            self.map_controller.state_controller.label_colors.append(colors[i])
            i += 1

    def set_icon_type(self, icon_type):
        if icon_type in self.army_icons:
            self.active_icon = self.army_icons[icon_type]
            self.active_icon_name = icon_type
        else:
            raise ValueError(f"Nieznany typ ikony: {icon_type}")
