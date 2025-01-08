from controllers.tools import erase_area, draw_icon, PixelSampler, IconFinder, find_icons
from PyQt5.QtGui import QImage, QIcon, QPixmap # type: ignore
from PyQt5.QtCore import QSize, QTimer # type: ignore
from PyQt5.QtWidgets import QPushButton # type: ignore
from modes.base_mode import Mode
from threading import Thread
import time

class BuildingsMode(Mode):
    """Obsługuje tryb budynków."""

    def __init__(self, mode_manager, map_controller):
        super().__init__(map_controller)
        self.mode_manager = mode_manager
        self.snap = False
        self.cities = []
        self.farms = []
        self.building_icons = {
            "city": QImage("icons/city.png"),
            "farm": QImage("icons/farm.png"),
            'capital': QImage("icons/capital.png"),
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

        c_button = QPushButton()
        c_button.setIcon(self.get_icon_from_image(self.building_icons["capital"]))  # Konwertuj QImage na QIcon
        c_button.setIconSize(QSize(40, 40))
        c_button.setFixedSize(50, 50)
        c_button.clicked.connect(lambda: self.set_capital())

        # Aktualizacja dynamicznego menu
        self.map_controller.button_panel.update_dynamic_menu([m_button, f_button, c_button])

    def set_capital(self):
        self.set_icon_type("capital")
        #self.state_controller.set_capital(event.x, event.y)

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
        elif building_type == "capital":
            print(f"Dodano stolicę ({x}, {y}) #TODO")
        else:
            raise ValueError(f"Nieznany typ budynku: {building_type}")

    def remove_building_positions(self, x, y, size=20):
        # Filtruj pozycje, które mają zostać zachowane (poza kwadratem)
        self.cities = [
            (bx, by) for bx, by in self.cities
            if not (x - size <= bx <= x + size and y - size <= by <= y + size)
        ]
        self.farms = [
            (bx, by) for bx, by in self.farms
            if not (x - size <= bx <= x + size and y - size <= by <= y + size)
        ]

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

    def start_buildings_timer(self):
        if not hasattr(self, '_buildings_timer'):
            self._buildings_timer = QTimer()
            self._buildings_timer.setSingleShot(True)
            self._buildings_timer.timeout.connect(self._process_buildings)

        self._buildings_timer.start(1000)

    def _process_buildings(self):

        def process():
            self.find_cities()
            self.count_cities_by_state()

        thread = Thread(target=process)
        thread.start()
        thread.join()

    def add_building(self, x, y):
        """Dodaje budynek do warstwy i zapisuje operację."""
        building_layer = self.map_controller.layer_manager.get_layer("buildings")
        building_layer = draw_icon(building_layer, self.building_icon, x, y)
        self.map_controller.layer_manager.refresh_layer("buildings")
        self.add_building_position(x, y, self.active_icon)

    def erase_building(self, event):
        """Usuwa budynki w promieniu i zapisuje operację."""
        building_layer = self.map_controller.layer_manager.get_layer("buildings")
        radius = 15
        building_layer = erase_area(building_layer, event.x, event.y, radius)
        self.map_controller.layer_manager.refresh_layer("buildings")
        self.remove_building_positions(event.x, event.y)


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
                positions = [(0, 0)]  # bug, że gdy nie ma budynków to nie odświerza liczby

            pixel_sampler = PixelSampler(
                self.map_controller.layer_manager.layers.get("province"),
                positions,
                self.map_controller.state_controller.get_states()
            )

            for state in self.map_controller.state_controller.get_states():
                setattr(state, building_type, pixel_sampler.get(state.name, 0))


    def find_cities(self):
        """
        Znajduje współrzędne ikon odpowiadających próbce na warstwie z optymalizacją.
        """

        layer = self.map_controller.layer_manager.get_layer("buildings")

        if layer is None:
            return []
        start_time = time.time()
        self.cities = IconFinder(self.building_icons["city"], layer)
        mid_time = time.time()
        self.farms = IconFinder(self.building_icons["farm"], layer)
        end_time = time.time()
        print(f"Czas środkowy {mid_time - start_time}, Czas końcowy {end_time - start_time}")
