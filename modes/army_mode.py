from PyQt5.QtGui import QImage, QPainter, QColor
from PyQt5.QtCore import Qt
from controllers.tools import Tools
import numpy as np
import copy 
class ArmyMode:
    """Obsługuje tryb armii."""
    def __init__(self, mode_manager, map_controller):
        self.map_controller = map_controller
        self.mode_manager = mode_manager
        self.army_icon = QImage("icons/army.png")
        if self.army_icon.isNull():
            raise ValueError("Nie udało się załadować ikony: icons/army.png")
        self.active_state = None

    def handle_event(self, event):
        if event.event_type == "click" and event.button == "left":
            self.add_army(event.x, event.y)
        elif event.button == "right":
            self.erase_army(event)

    def add_army(self, x, y):
        """Dodaje ikonę armii na warstwę z kolorem wybranego państwa."""
        army_layer = self.map_controller.layer_manager.get_layer("army")
        if army_layer is None:
            print("Nie można dodać jednostki armii: brak warstwy 'army'.")
            return

        # Pobierz aktywny kolor państwa z ModeManager
        active_state = self.mode_manager.get_active_state()
        if active_state is None or not hasattr(active_state, "color"):
            print("Brak aktywnego państwa lub koloru.")
            return
        state_color = active_state.color.getRgb()[:3]  # Pobierz RGB

        # Przekształć ikonę armii
        recolored_icon = self.recolor_icon(self.army_icon.copy(), state_color)

        # Pobranie wymiarów obrazu warstwy
        height, width, _ = army_layer.shape
        bytes_per_line = 4 * width

        # Tworzenie obrazu warstwy na bazie istniejących danych
        layer_image = QImage(army_layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)

        # Rysowanie ikony armii
        painter = QPainter(layer_image)
        painter.drawImage(x - recolored_icon.width() // 2, y - recolored_icon.height() // 2, recolored_icon)
        painter.end()

        # Aktualizacja danych warstwy
        data = layer_image.bits().asstring(bytes_per_line * height)
        self.map_controller.layer_manager.layers["army"] = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 4)

        # Odświeżenie warstwy
        self.map_controller.layer_manager.refresh_layer("army")
        self.map_controller.snapshot_manager.create_snapshot({
            "layers": {
                "army": {
                    "before": copy.deepcopy(army_layer),
                    "after": copy.deepcopy(self.map_controller.layer_manager.layers["army"])
                }
            }
        })

    def erase_army(self, event):
        army_layer = self.map_controller.layer_manager.get_layer("army")
        """Obsługuje zdarzenia związane z usuwaniem (prawy przycisk myszy)."""
        if event.event_type in {"click", "move"}:
            radius = 10  # Promień gumki
            x, y = event.x, event.y
            Tools.erase_area(self.map_controller, self.map_controller.layer_manager, "army", x, y, radius)
            if event.event_type =="click":
                layer = self.map_controller.layer_manager.get_layer("army")
                self.map_controller.snapshot_manager.create_snapshot({
                    "layers": {
                        "army": {
                            "before": copy.deepcopy(layer),
                            "after": copy.deepcopy(self.map_controller.layer_manager.layers["army"])
                        }
                    }
                })
        elif event.event_type == "release":
            pass

    def recolor_icon(self, image, target_color):
        """
        Zmienia białe piksele w ikonie na wybrany kolor.
        :param image: QImage ikony.
        :param target_color: QColor lub (R, G, B) reprezentujący kolor wybranego państwa.
        :return: Zmieniona QImage.
        """
        if isinstance(target_color, tuple):
            target_color = QColor(*target_color)

        # Konwersja do formatu ARGB32 dla manipulacji pikselami
        image = image.convertToFormat(QImage.Format_ARGB32)
        for y in range(image.height()):
            for x in range(image.width()):
                pixel_color = QColor(image.pixel(x, y))  # Użycie poprawnego wywołania z x, y
                if pixel_color == QColor(255, 255, 255):  # Jeśli piksel jest biały
                    image.setPixel(x, y, target_color.rgb())  # Ustaw kolor docelowy
        return image
