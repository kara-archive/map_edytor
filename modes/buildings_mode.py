from controllers.tools import Tools, PixelSampler
from PyQt5.QtGui import QImage, QPainter, QColor, QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
from controllers.data import DATA
import copy
import numpy as np
import cv2
import math
from PyQt5.QtWidgets import QPushButton
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
            Mode.end_snap(self, "buildings")
            self.count_cities_by_state()

    def add_building(self, x, y):
        """Dodaje budynek do warstwy i zapisuje operację."""
        building_layer = self.map_controller.layer_manager.get_layer("buildings")
        if building_layer is None:
            print("Nie można znaleźć warstwy 'buildings'.")
            return
        self._draw_icon(building_layer, x, y)

    def erase_building(self, event):
        #print(f"Erasing buildings around: ({event.x}, {event.y}), radius: 20")
        """Usuwa budynki w promieniu i zapisuje operację."""
        radius = 20
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

    def count_cities_by_state(self):
        """
        Próbkuje piksele w pozycjach budynków różnych typów i wyświetla liczbę budynków każdego typu dla każdego państwa.
        """
        if self.map_controller.cv_image is None:
            print("Brak obrazu bazowego (cv_image) do próbkowania budynków.")
            return
        self.cities = self.find_cities(self.building_icons["city"], copy.deepcopy(self.map_controller.layer_manager.layers.get("buildings")))
        self.farms = self.find_cities(self.building_icons["farm"], copy.deepcopy(self.map_controller.layer_manager.layers.get("buildings")))
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

    def find_cities(self, sample_icon, image):
        """
        Wyszukuje współrzędne ikon w obrazie za pomocą dopasowywania szablonu.

        :param sample_icon: QImage ikony do wyszukiwania (np. "city" lub "farm").
        :param image: Obraz warstwy "buildings" jako macierz NumPy.
        :return: Lista współrzędnych (x, y) dopasowanych ikon (środek).
        """
        # Konwersja QImage na macierz NumPy
        icon = self._convert_qimage_to_numpy(sample_icon)

        # Przekształcenie obrazu do skali szarości
        icon_gray = cv2.cvtColor(icon, cv2.COLOR_BGRA2GRAY)
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)

        # Wykonanie dopasowania szablonu
        result = cv2.matchTemplate(image_gray, icon_gray, cv2.TM_CCOEFF_NORMED)

        # Ustal próg wykrywania (np. 0.8 dla wysokiego dopasowania)
        threshold = 0.7
        locations = np.where(result >= threshold)

        # Wymiary ikony
        icon_height, icon_width = icon_gray.shape

        # Konwersja współrzędnych do listy punktów (x, y)
        coordinates = [
            (int(pt[0] + icon_width / 2), int(pt[1] + icon_height / 2))  # Środek ikony
            for pt in zip(*locations[::-1])
        ]

        return coordinates



    def _convert_qimage_to_numpy(self, qimage):
        """
        Konwertuje QImage na macierz NumPy bez wymuszania formatu.
        Zakłada, że obraz jest w formacie RGBA8888.
        """
        width = qimage.width()
        height = qimage.height()
        ptr = qimage.bits()
        ptr.setsize(height * width * 4)  # 4 kanały (R, G, B, A)
        return np.frombuffer(ptr, dtype=np.uint8).reshape((height, width, 4))
