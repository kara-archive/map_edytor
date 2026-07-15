from controllers.tools import erase_area, draw_icon, PixelSampler, find_icons
from PyQt5.QtGui import QImage, QIcon, QPixmap, QColor # type: ignore
from PyQt5.QtCore import QSize, QTimer # type: ignore
from PyQt5.QtWidgets import QPushButton, QButtonGroup # type: ignore
from modes.base_mode import Mode
from modes.biome_mode import BiomeMode
import os
import time

class BuildingsMode(Mode):
    """Obsługuje tryb budynków."""

    BIOME_NAMES = {
        "Woda": "water",
        "Pustynia": "desert",
        "Las": "forest",
        "Plain": "plain",
        "Góry": "mountains",
    }

    def __init__(self, mode_manager, map_controller):
        self.name = "buildings"
        super().__init__(map_controller)
        self.mode_manager = mode_manager
        self.register_mode(z=3, label="Budynki", short="e")
        self.building_positions = {}  # Słownik przechowujący pozycje budynków
        self.building_icons = self.load_building_icons("icons")
        self.roads = self.mode_manager.roads
        self.active_icon = next(iter(self.building_icons.values()))
        self.active_icon_name = next(iter(self.building_icons.keys()))

        if self.active_icon.isNull():
            raise ValueError("Nie udało się załadować ikony budynku.")

    def load_building_icons(self, folder):
        """Ładuje ikony budynków z folderu."""
        building_icons = {}
        for filename in sorted(os.listdir(folder)):
            if "b_" in filename and filename.endswith(".png"):
                icon_name = filename.split("b_")[1][:-4]  # Usuwa wszystko przed "b_" i ".png" z końca
                icon_path = os.path.join(folder, filename)
                building_icons[icon_name] = QImage(icon_path)
        return building_icons

    def handle_event(self, event):
        if event.event_type == "click":
            self.start_snap("buildings")

        if event.event_type == "click" and event.button == "left":
            self.add_building(event.x, event.y)

        if event.event_type in {"move", "click"} and event.button == "right":
            self.erase_building(event)

        if event.event_type == "release":
            self.count_cities_by_state()
            self.end_snap("buildings")

    def setup_menu(self):

        # Tworzenie QButtonGroup
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)  # Tylko jeden przycisk może być zaznaczony w danym momencie

        buttons = []
        for icon_name, icon in self.building_icons.items():
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

        # Aktualizacja dynamicznego menu
        self.request_menu_update.emit(buttons)

        # Ustawienie pierwszego przycisku jako domyślnie zaznaczonego


    def set_capital(self, x, y):
        print(f"Tutaj ma być więcej kodu ({x},{y}) #TODO")

    def get_icon_from_image(self, image):
        pixmap = QPixmap.fromImage(image)
        return QIcon(pixmap)

    def set_icon_type(self, icon_type):
        if icon_type in self.building_icons:
            self.active_icon = self.building_icons[icon_type]  # Ustaw ikonę z mapy
            self.active_icon_name = icon_type
            print(f"Ustawiono ikonę: {icon_type}")
        else:
            raise ValueError(f"Nieznany typ ikony: {icon_type}")

    def add_building_position(self, x, y, building_type):
        if building_type not in self.building_positions:
            self.building_positions[building_type] = []
        self.building_positions[building_type].append((x, y))

    def remove_building_positions(self, x, y, size=10):
        for positions in self.building_positions.values():
            positions[:] = [
                (bx, by) for bx, by in positions
                if not (x - size <= bx <= x + size and y - size <= by <= y + size)
            ]

    def start_buildings_timer(self):
        if not hasattr(self, '_buildings_timer'):
            self._buildings_timer = QTimer()
            self._buildings_timer.setSingleShot(True)
            self._buildings_timer.timeout.connect(self._process_buildings)

        self._buildings_timer.start(1000)

    def _process_buildings(self):
        self.find_cities()
        self.count_cities_by_state()

    def add_building(self, x, y):
        """Dodaje budynek do warstwy i zapisuje operację."""
        if self.get_biome_at(x, y) == "water":
            print("Nie można budować na wodzie.")
            return

        building_layer = self.map_controller.layer_manager.get_layer("buildings")
        building_layer = draw_icon(building_layer, self.active_icon, x, y)
        self.map_controller.layer_manager.refresh_layer("buildings")
        self.add_building_position(x, y, self.active_icon_name)

    def erase_building(self, event):
        """Usuwa budynki w promieniu i zapisuje operację."""
        building_layer = self.map_controller.layer_manager.get_layer("buildings")
        radius = 5
        building_layer = erase_area(building_layer, event.x, event.y, radius, radius)
        self.map_controller.layer_manager.refresh_layer("buildings")
        self.remove_building_positions(event.x, event.y)

    def count_cities_by_state(self):
        """
        Próbkuje piksele w pozycjach budynków i liczy ich wartość z uwzględnieniem biomu.
        """
        self.set_colors_in_color_label()
        roads_layer = self.map_controller.layer_manager.get_layer("roads")
        province_layer = self.map_controller.layer_manager.get_layer("province")
        states = self.map_controller.state_controller.get_states()

        for building_type, positions in self.building_positions.items():
            positions_road = self._get_positions_connected_to_roads(positions, roads_layer)
            counts = {state.name: 0 for state in states}

            for x, y in positions_road:
                biome = self.get_biome_at(x, y)
                if biome == "water":
                    continue

                state = self._get_state_at(province_layer, x, y, states)
                if state is None:
                    continue

                counts[state.name] += self.get_building_value(building_type, biome)

            for state in states:
                setattr(state, building_type, counts.get(state.name, 0))
        self.map_controller.state_controller.recalculate_all_stats()

    def get_building_value(self, building_type, biome):
        #building_type = self._normalize_building_type(building_type)
        biome = (biome or "plain").lower()
        #(TODO) na razie i tak nie działają biomy

        if biome == "water":
            return 0
        if building_type == "town" and biome == "mountains":
            return 0
        if building_type == "rancho":
            # Zmiana z 3 na 1, ponieważ mnożenie następuje w state_controller.py
            return 0 if biome == "desert" else 1
        return 1

    def _get_positions_connected_to_roads(self, positions, roads_layer):
        if not positions:
            return []
        if not self.roads:
            return list(positions)
        if roads_layer is None:
            return []

        positions_road = []
        for x, y in positions:
            if 0 <= x < roads_layer.width() and 0 <= y < roads_layer.height():
                if QColor(roads_layer.pixel(x, y)) == QColor(128, 128, 128, 255):
                    positions_road.append((x, y))
        return positions_road

    def get_biome_at(self, x, y):
        return self.map_controller.get_biome_at(x, y)

    def _get_state_at(self, province_layer, x, y, states):
        if province_layer is None or not (0 <= x < province_layer.width() and 0 <= y < province_layer.height()):
            return None

        color = QColor(province_layer.pixel(x, y)).getRgb()[:3]
        for state in states:
            if self._is_similar_color(color, QColor(state.color).getRgb()[:3]):
                return state
        return None

    def _is_similar_color(self, color1, color2, tolerance=5):
        return all(abs(int(c1) - int(c2)) <= tolerance for c1, c2 in zip(color1, color2))

    def find_cities(self):
        """
        Znajduje współrzędne ikon odpowiadających próbce na warstwie z optymalizacją.
        """
        layer = self.map_controller.layer_manager.get_layer("buildings")

        if layer is None:
            return []

        start_time = time.time()
        for building_type, icon in self.building_icons.items():
            print(f"\n[DEBUG] Przetwarzanie typu budowli: '{building_type}'")
        end_time = time.time()
        print(f"Znaleziono budynki w czasie: {end_time - start_time:.2f} s")

    def set_colors_in_color_label(self):
        """Ustawia kolory w label w state, które odpowiadają kolorowi ikony na jej środkowym pixelu"""
        for icon in self.building_icons.values():
            color = icon.pixelColor(icon.width() // 2, icon.height() // 2)
            if icon != self.building_icons.get("capital"):
                self.map_controller.state_controller.label_colors.append(color.name())
