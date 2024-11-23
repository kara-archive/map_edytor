from controllers.tools import Tools, PixelSampler
from PyQt5.QtGui import QImage, QPainter, QColor
from PyQt5.QtCore import Qt
from controllers.data import DATA
import copy
import numpy as np
import math
class BuildingsMode:
    """Obsługuje tryb budynków."""
    MAX_RECENT_OPERATIONS = 5  # Limit zapisanych operacji

    def __init__(self, mode_manager, map_controller):
        self.snap = False
        self.map_controller = map_controller
        self.building_positions = {}  # Pozycje budynków
        self.building_icon = QImage("icons/city.png")
        self.before_layer = None

        if self.building_icon.isNull():
            raise ValueError("Nie udało się załadować ikony budynku: icons/city.png")

    def handle_event(self, event):
        if event.event_type == "click":
            self.before_layer = copy.deepcopy(self.map_controller.layer_manager.get_layer("buildings"))
        if event.event_type == "click" and event.button == "left":
            self.add_building(event.x, event.y)
            self.count_cities_by_state()

        elif event.event_type in {"move", "click"} and event.button == "right":
            self.erase_building(event)
            self.count_cities_by_state()

        elif event.event_type == "release":
            after_layer = copy.deepcopy(self.map_controller.layer_manager.get_layer("buildings"))
            self.do_snap(self.before_layer, after_layer)

    def add_building(self, x, y):
        print(f"Adding building at: ({x}, {y})")
        """Dodaje budynek do warstwy i zapisuje operację."""
        self.building_positions[(x, y)] = "city"
        building_layer = self.map_controller.layer_manager.get_layer("buildings")
        if building_layer is None:
            print("Nie można znaleźć warstwy 'buildings'.")
            return
        self._draw_icon(building_layer, x, y)
        self.add_building_position(x, y)

    def do_snap(self, before, after):
        self.map_controller.snapshot_manager.create_snapshot({
            "layers": {
                "buildings": {
                    "before": before,
                    "after": after
                }
            }
        })

    def erase_building(self, event):
        print(f"Erasing buildings around: ({event.x}, {event.y}), radius: 20")
        """Usuwa budynki w promieniu i zapisuje operację."""
        radius = 20
        removed_positions = self.remove_building_positions(event, radius)
        Tools.erase_area(self.map_controller, self.map_controller.layer_manager, "buildings", event.x, event.y, radius)

    def _draw_icon(self, building_layer, x, y):
        """Rysuje ikonę budynku na warstwie."""
        height, width, _ = building_layer.shape
        bytes_per_line = 4 * width

        # Tworzenie obrazu warstwy
        layer_image = QImage(building_layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)
        painter = QPainter(layer_image)
        if not painter.isActive():
            print("Painter nie jest aktywny!")
            return
        painter.drawImage(x - self.building_icon.width() // 2, y - self.building_icon.height() // 2, self.building_icon)
        painter.end()

        # Aktualizacja danych warstwy
        data = layer_image.bits().asstring(bytes_per_line * height)
        self.map_controller.layer_manager.layers["buildings"] = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 4)
        self.map_controller.layer_manager.refresh_layer("buildings")

    def add_building_position(self, x, y):
        print(f"Adding building position to DATA: ({x}, {y})")
        """Dodaje pozycję budynku i zapisuje operację."""
        DATA.buildings.cities.append((x, y))
        print(f"Dodano budynek w pozycji: ({x}, {y})")

    def remove_building_positions(self, event, radius):
        print(f"Removing building positions around: ({event.x}, {event.y}), radius: {radius}")
        """
        Usuwa pozycje budynków w zadanym promieniu.
        Zwraca listę usuniętych pozycji.
        """
        x, y = event.x, event.y
        removed_positions = [
            (bx, by) for bx, by in DATA.buildings.cities
            if math.sqrt((bx - x) ** 2 + (by - y) ** 2) <= radius
        ]

        # Usuwanie budynków z bazy danych w dokładnym promieniu
        for pos in removed_positions:
            DATA.buildings.cities.remove(pos)

        print(f"Usunięto {len(removed_positions)} budynków w promieniu {radius} od punktu ({x}, {y}).")
        return removed_positions

    def restore_operation(self, type, x, y):
        print(type, x, y)

    def count_cities_by_state(self):
        """
        Próbkuje piksele w pozycjach budynków (miast) i wyświetla liczbę miast dla każdego państwa.
        """
        if self.map_controller.cv_image is None:
            print("Brak obrazu bazowego (cv_image) do próbkowania miast.")
            return

        if not DATA.buildings.cities:
            print("Brak zapisanych pozycji miast w DATA.buildings.cities.")
            return

        # Użycie PixelSampler
        pixel_sampler = PixelSampler(
            self.map_controller.layer_manager.layers.get("province"),
            DATA.buildings.cities,
            self.map_controller.state_controller.get_states()
        )
        for state in self.map_controller.state_controller.get_states():
            state.cities = pixel_sampler.get(state.name, 0)
