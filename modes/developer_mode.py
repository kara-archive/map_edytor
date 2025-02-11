from PyQt5.QtGui import QImage, QColor
from controllers.tools import flood_fill
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QPainterPath
from PyQt5.QtWidgets import QGraphicsPathItem
from controllers.data import DATA
import copy
import numpy as np
from modes.base_mode import Mode
import math
class DevelopMode(Mode):
    """Obsługuje tryb prowincji."""
    def __init__(self, mode_manager, map_controller):
        self.name = "province"
        super().__init__(map_controller)
        self.map_controller = map_controller
        self.sampled_color = (np.uint8(68), np.uint8(107), np.uint8(163))
        self.active_state = None
        self.mode_manager = mode_manager
        self.register_mode(5, label="Develop")
        self.layer = self.map_controller.layer_manager.layers.get("develop")

    def handle_event(self, event):
        """Obsługuje zdarzenia w trybie prowincji."""

        if event.button == "left" and event.event_type == "click":
                fill_color = self.sampled_color
                DATA.provinces.append((event.x, event.y))
                self.draw_province_dots((np.uint8(0), np.uint8(255), np.uint8(0)))
        if event.button == "right" and event.event_type == "click":
                fill_color = (np.uint8(255), np.uint8(255), np.uint8(255))
                #self.color_fill(event.x, event.y, fill_color)
                self.remove_building_positions(event, 10)
                self._zmazuj(event)

    def setup_menu(self):
        self.map_controller.button_panel.update_dynamic_menu([])


    def copy_image(self, cv_image):
        # Jeśli warstwa ma być zainicjalizowana obrazem bazowym
        if cv_image is not None:
            if cv_image.shape[2] == 3:  # RGB bez kanału alfa
                alpha_channel = np.full((height, width, 1), 255, dtype=np.uint8)  # Pełna przezroczystość
                cv_image = np.concatenate((cv_image, alpha_channel), axis=2)  # Dodanie kanału alfa
                print("Dodano kanał alfa do obrazu bazowego.")

            self.mode_manager.layer_manager.layers["province"] = cv_image.copy()
            print(f"Skopiowano cv_image do warstwy '{layer_name}' (z_value = 1)")
        else:
            print("provincemode: cv_image jest None")

    def color_fill(self, x, y, color):
        layer = self.map_controller.layer_manager.layers.get(self.name)
        self.map_controller.layer_manager.layers[self.name] = flood_fill(layer, x, y, color)
        self.map_controller.layer_manager.refresh_layer(self.name)

    def draw_province_dots(self, color, dot_size=1):
        """
        Rysuje czerwone kropki na podstawie danych z DATA.provinces.

        :param dot_size: int, średnica kropek w pikselach.
        :return: None
        """
        #self.map_controller.layer_manager.add_layer("province")
        roads_layer = self.map_controller.layer_manager.get_layer("develop")
        if roads_layer is None:
            print("Brak warstwy 'roads' do rysowania.")
            return


        painter = QPainter(roads_layer)
        pen = QPen(QColor(255, 0, 0, 255))  # Czerwony kolor
        pen.setWidth(dot_size)
        painter.setPen(pen)


        for (x, y) in DATA.provinces:
            if 0 <= x < width and 0 <= y < height:
                painter.drawPoint(x, y)
                self.flood_fill(x, y, color)
            else:
                print(f"Punkt dla prowincji '{province}' ({x}, {y}) jest poza granicami warstwy.")

        painter.end()


        # Odświeżenie warstwy
        self.map_controller.layer_manager.refresh_layer("develop")
    def find_cities(self):
        pass
    def count_cities_by_state(self):
        pass
    def _zmazuj(self, event):
        """Obsługuje zdarzenia związane z usuwaniem (prawy przycisk myszy)."""
        if event.event_type in {"click", "move"}:
            radius = 10  # Promień gumki
            Tools.erase_area(self.map_controller, self.map_controller.layer_manager, "roads", event.x, event.y, radius)

    def remove_building_positions(self, event, radius):
        print(f"Removing building positions around: ({event.x}, {event.y}), radius: {radius}")
        """
        Usuwa pozycje budynków w zadanym promieniu.
        Zwraca listę usuniętych pozycji.
        """
        x, y = event.x, event.y
        removed_positions = [
            (bx, by) for bx, by in DATA.provinces
            if math.sqrt((bx - x) ** 2 + (by - y) ** 2) <= radius
        ]

        # Usuwanie budynków z bazy danych w dokładnym promieniu
        for pos in removed_positions:
            DATA.provinces.remove(pos)

        print(f"Usunięto {len(removed_positions)} budynków w promieniu {radius} od punktu ({x}, {y}).")
        return removed_positions
