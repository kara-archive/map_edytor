from controllers.tools import Tools, PixelSampler
from PyQt5.QtGui import QImage, QPainter, QColor, QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
from controllers.data import DATA
import copy
import numpy as np
import math
from PyQt5.QtWidgets import QPushButton
from modes.base_mode import Mode

class BuildingsMode(Mode):
    """Obsługuje tryb budynków."""

    def __init__(self, mode_manager, map_controller):
        Mode.__init__(self, map_controller)
        self.snap = False
        self.map_controller = map_controller
        self.before_layer = None
        self.building_icons = {
            "city": QImage("icons/city.png"),
            "farm": QImage("icons/farm.png"),
        }

        self.building_icon = self.building_icons["city"]

        if self.building_icon.isNull():
            raise ValueError("Nie udało się załadować ikony budynku: icons/city.png")

    def setup_menu(self):
        print("Setup menu dla BuildingsMode")

        # Tworzenie przycisków z ikonami
        m_button = QPushButton()
        m_button.setIcon(self.get_icon_from_image(self.building_icons["city"]))  # Konwertuj QImage na QIcon
        m_button.setIconSize(QSize(40, 40))  # Rozmiar ikony wewnątrz przycisku
        m_button.setFixedSize(50, 50)  # Przyciski są kwadratowe
        m_button.clicked.connect(lambda: self.set_icon_type("city"))

        f_button = QPushButton()
        f_button.setIcon(self.get_icon_from_image(self.building_icons["farm"]))  # Konwertuj QImage na QIcon
        f_button.setIconSize(QSize(40, 40))
        f_button.setFixedSize(50, 50)
        f_button.clicked.connect(lambda: self.set_icon_type("farm"))

        # Aktualizacja dynamicznego menu
        self.map_controller.button_panel.update_dynamic_menu([m_button, f_button])

    def get_icon_from_image(self, image):
        pixmap = QPixmap.fromImage(image)
        return QIcon(pixmap)

    def set_icon_type(self, icon_type):
        if icon_type in self.building_icons:
            self.building_icon = self.building_icons[icon_type]  # Ustaw ikonę z mapy
            print(f"Ustawiono ikonę: {icon_type}")
        else:
            raise ValueError(f"Nieznany typ ikony: {icon_type}")

    def handle_event(self, event):
        if event.event_type == "click":
            Mode.start_snap(self, "buildings")
        if event.event_type == "click" and event.button == "left":
            self.add_building(event.x, event.y)

        elif event.event_type in {"move", "click"} and event.button == "right":
            self.erase_building(event)

        elif event.event_type == "release":
            Mode.end_snap(self, "buildings")
            self.count_cities_by_state()

    def add_building(self, x, y):
        print(f"Adding building at: ({x}, {y})")
        """Dodaje budynek do warstwy i zapisuje operację."""
        building_layer = self.map_controller.layer_manager.get_layer("buildings")
        if building_layer is None:
            print("Nie można znaleźć warstwy 'buildings'.")
            return
        self._draw_icon(building_layer, x, y)
        self.add_building_position(x, y)

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
        # Pobierz typ aktywnej ikony
        active_icon_type = next((key for key, value in self.building_icons.items() if value == self.building_icon), None)

        if not active_icon_type:
            print(f"Nieznany typ ikony: {self.building_icon}.")
            return

        # Dodaj pozycję do odpowiedniej listy w DATA.buildings
        if active_icon_type == "city":
            DATA.buildings.cities.append((x, y))
        elif active_icon_type == "farm":
            DATA.buildings.farms.append((x, y))
        else:
            print(f"Typ '{active_icon_type}' nieobsługiwany. Pozycja nie została dodana.")
            return

        # Informacja o dodaniu
        print(f"Dodano budynek typu '{active_icon_type}' w pozycji: ({x}, {y})")

    def remove_building_positions(self, event, radius):
        print(f"Removing building positions around: ({event.x}, {event.y}), radius: {radius}")
        """
        Usuwa pozycje budynków wszystkich typów w zadanym promieniu.
        Zwraca listę usuniętych pozycji wraz z ich typami.
        """
        x, y = event.x, event.y

        # Słownik do przechowywania usuniętych pozycji według typu
        removed_positions = {
            "cities": [],
            "farms": [],
            "towns": [],
        }

        # Iteruj przez wszystkie listy budynków w DATA.buildings
        for building_type, positions in vars(DATA.buildings).items():
            if isinstance(positions, list):  # Sprawdź, czy to lista pozycji
                # Znajdź pozycje do usunięcia w promieniu
                to_remove = [
                    (bx, by) for bx, by in positions
                    if math.sqrt((bx - x) ** 2 + (by - y) ** 2) <= radius
                ]
                # Usuń znalezione pozycje
                for pos in to_remove:
                    positions.remove(pos)
                removed_positions[building_type].extend(to_remove)

        # Logowanie usuniętych pozycji
        for building_type, positions in removed_positions.items():
            if positions:
                print(f"Usunięto {len(positions)} budynków typu '{building_type}' w promieniu {radius} od ({x}, {y}).")

        return removed_positions

    def count_cities_by_state(self):
        """
        Próbkuje piksele w pozycjach budynków różnych typów i wyświetla liczbę budynków każdego typu dla każdego państwa.
        """
        if self.map_controller.cv_image is None:
            print("Brak obrazu bazowego (cv_image) do próbkowania budynków.")
            return

        building_types = {
            "cities": DATA.buildings.cities,
            "farms": DATA.buildings.farms,
        }

        for building_type, positions in building_types.items():
            if not positions:
                print(f"Brak zapisanych pozycji budynków w DATA.buildings.{building_type}.")
                continue

            pixel_sampler = PixelSampler(
                self.map_controller.layer_manager.layers.get("province"),
                positions,
                self.map_controller.state_controller.get_states()
            )

            for state in self.map_controller.state_controller.get_states():
                setattr(state, building_type, pixel_sampler.get(state.name, 0))
                print(f"Państwo {state.name} ma {getattr(state, building_type)} budynków typu '{building_type}'.")
