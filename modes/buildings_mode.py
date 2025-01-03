from controllers.tools import Tools, PixelSampler
from PyQt5.QtGui import QImage, QPainter, QIcon, QPixmap, QColor # type: ignore
from PyQt5.QtCore import QSize # type: ignore
from PyQt5.QtWidgets import QPushButton # type: ignore
from modes.base_mode import Mode


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
        self.cities = self.find_cities(self.building_icons["city"], self.map_controller.layer_manager.layers.get("buildings"))
        self.farms = self.find_cities(self.building_icons["farm"], self.map_controller.layer_manager.layers.get("buildings"))
        building_types = {
            "cities": self.cities,
            "farms": self.farms,
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


    def find_cities(self, sample_icon, layer):
        if layer is None:
            return []

        icon_width, icon_height = sample_icon.width(), sample_icon.height()
        layer_width, layer_height = layer.width(), layer.height()

        cities = []

        for x in range(layer_width - icon_width + 1):
            for y in range(layer_height - icon_height + 1):
                if self._is_icon_at_position(sample_icon, layer, x, y):
                    cities.append((x, y))
        return cities

    def _is_icon_at_position(self, sample_icon, layer, x, y):
        icon_width, icon_height = sample_icon.width(), sample_icon.height()
        for ix in range(icon_width):
            for iy in range(icon_height):
                if sample_icon.pixel(ix, iy) != layer.pixel(x + ix, y + iy):
                    return False
        return True
