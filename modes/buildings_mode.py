from controllers.tools import Tools, PixelSampler
from PyQt5.QtGui import QImage, QPainter, QIcon, QPixmap, QColor # type: ignore
from PyQt5.QtCore import QSize # type: ignore
from PyQt5.QtWidgets import QPushButton # type: ignore
from modes.base_mode import Mode
import math


class BuildingsMode(Mode):
    """Obsługuje tryb budynków."""

    def __init__(self, mode_manager, map_controller):
        Mode.__init__(self, map_controller)
        self.snap = False
        self.cities = []
        self.farms = []
        self.map_controller = map_controller
        self.building_icons = {
            "city": QImage("icons/city.png"),
            "farm": QImage("icons/farm.png"),
        }

        self.building_icon = self.building_icons["city"]
        self.active_icon = "city"

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
            self.active_icon = icon_type
            print(f"Ustawiono ikonę: {icon_type}")
        else:
            raise ValueError(f"Nieznany typ ikony: {icon_type}")

    def add_building_position(self, x, y, building_type):
        if building_type == "city":
            self.cities.append((x, y))
        elif building_type == "farm":
            self.farms.append((x, y))
        else:
            raise ValueError(f"Nieznany typ budynku: {building_type}")

    def remove_building_positions(self, x, y, radius=20):

        # Filtruj pozycje, które mają zostać zachowane (poza promieniem)
        self.cities = [
            (bx, by) for bx, by in self.cities
            if math.sqrt((bx - x) ** 2 + (by - y) ** 2) > radius
        ]
        self.farms = [
            (bx, by) for bx, by in self.farms
            if math.sqrt((bx - x) ** 2 + (by - y) ** 2) > radius
        ]

    def handle_event(self, event):
        if event.event_type == "click":
            Mode.start_snap(self, "buildings")

        if event.event_type == "click" and event.button == "left":
            self.add_building(event.x, event.y)
            self.add_building_position(event.x, event.y, self.active_icon)

        if event.event_type in {"move", "click"} and event.button == "right":
            self.erase_building(event)
            self.remove_building_positions(event.x, event.y)

        if event.event_type == "release":
            self.count_cities_by_state()
            Mode.end_snap(self, "buildings")


    def add_building(self, x, y):
        """Dodaje budynek do warstwy i zapisuje operację."""
        building_layer = self.map_controller.layer_manager.get_layer("buildings")
        if building_layer is None:
            print("Nie można znaleźć warstwy 'buildings'.")
            return
        self._draw_icon(building_layer, x, y)

    def erase_building(self, event):
        """Usuwa budynki w promieniu i zapisuje operację."""
        radius = 20
        Tools.erase_area(self.map_controller, self.map_controller.layer_manager, "buildings", event.x, event.y, radius)

    def _draw_icon(self, building_layer, x, y):
        """Rysuje ikonę budynku na warstwie."""
        painter = QPainter(building_layer)
        if not painter.isActive():
            print("Painter nie jest aktywny!")
            return
        painter.drawImage(x - self.building_icon.width() // 2, y - self.building_icon.height() // 2, self.building_icon)
        painter.end()

        # Odświeżenie warstwy
        self.map_controller.layer_manager.refresh_layer("buildings")

    def count_cities_by_state(self):
        """
        Próbkuje piksele w pozycjach budynków różnych typów i wyświetla liczbę budynków każdego typu dla każdego państwa.
        """
        if self.map_controller.cv_image is None:
            print("Brak obrazu bazowego (cv_image) do próbkowania budynków.")
            return
        building_types = {
            "cities": self.cities,
            "farms": self.farms,
        }

        for building_type, positions in building_types.items():
            if not positions:
                positions = [(0, 0)]  # Próbka z lewego górnego rogu obrazu

            pixel_sampler = PixelSampler(
                self.map_controller.layer_manager.layers.get("province"),
                positions,
                self.map_controller.state_controller.get_states()
            )

            for state in self.map_controller.state_controller.get_states():
                setattr(state, building_type, pixel_sampler.get(state.name, 0))
                print(f"Państwo {state.name} ma {getattr(state, building_type)} budynków typu '{building_type}'.")


    def find_cities(self):
        """
        Znajduje współrzędne ikon odpowiadających próbce na warstwie z optymalizacją.
        """
        layer = self.map_controller.layer_manager.get_layer("buildings")

        if layer is None:
            return []

        icon_data = {
            "city": self.building_icons["city"],
            "farm": self.building_icons["farm"]
        }

        layer_width, layer_height = layer.width(), layer.height()

        # Buforowanie danych pikseli warstwy
        layer_pixels = [
            [layer.pixel(x, y) for y in range(layer_height)]
            for x in range(layer_width)
        ]

        cities = []
        farms = []

        for icon_type, sample_icon in icon_data.items():
            icon_width, icon_height = sample_icon.width(), sample_icon.height()

            # Buforowanie danych pikseli ikony
            sample_pixels = [
                [sample_icon.pixel(ix, iy) for iy in range(icon_height)]
                for ix in range(icon_width)
            ]

            # Maskowanie przezroczystości
            transparency_mask = [
                [QColor(sample_pixels[ix][iy]).alpha() > 0 for iy in range(icon_height)]
                for ix in range(icon_width)
            ]

            for x in range(layer_width - icon_width + 1):
                for y in range(layer_height - icon_height + 1):
                    if self._is_icon_at_position(sample_pixels, transparency_mask, layer_pixels, x, y):
                        center_x = x + icon_width // 2
                        center_y = y + icon_height // 2
                        if icon_type == "city":
                            cities.append((center_x, center_y))
                        elif icon_type == "farm":
                            farms.append((center_x, center_y))

        self.cities = cities
        self.farms = farms

    def _is_icon_at_position(self, sample_pixels, transparency_mask, layer_pixels, x, y):
        """
        Sprawdza, czy ikona znajduje się w określonej pozycji w warstwie z optymalizacją.
        """
        icon_width, icon_height = len(sample_pixels), len(sample_pixels[0])

        for ix in range(icon_width):
            for iy in range(icon_height):
                if not transparency_mask[ix][iy]:
                    continue  # Ignoruj przezroczyste piksele
                if sample_pixels[ix][iy] != layer_pixels[x + ix][y + iy]:
                    return False  # Rozbieżność w pikselach
        return True
