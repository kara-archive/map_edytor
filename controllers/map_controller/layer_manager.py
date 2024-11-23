from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QGraphicsPixmapItem
import numpy as np

class LayerManager:
    def __init__(self, map_controller):
        self.layers = {}  # Przechowuje dane warstw w formie numpy.ndarray
        self.layer_items = {}  # QGraphicsPixmapItem dla każdej warstwy
        self.visible_layers = set()  # Nazwy widocznych warstw
        self.Z_VALUES = {
            "province": 0,
            "roads": 1,
            "buildings": 2,
            "army": 3
        }
        self.map_controller = map_controller

    def get_map_controller(self):
        return self.map_controller

    def add_layer(self, layer_name, width, height, z_value, scene, cv_image):
        if layer_name not in self.layers:
            # Tworzenie brakującej warstwy z kanałem alfa
            self.layers[layer_name] = np.full((height, width, 4), 0, dtype=np.uint8)  # RGBA
            print(f"Warstwa '{layer_name}' dodana: {width}x{height}")

        # Tworzenie QGraphicsPixmapItem
        pixmap_item = QGraphicsPixmapItem()
        pixmap_item.setZValue(z_value)
        scene.addItem(pixmap_item)
        self.layer_items[layer_name] = pixmap_item
        self.set_visibility(layer_name, True)

        # Jeśli warstwa ma być zainicjalizowana obrazem bazowym
        if z_value == 0 and cv_image is not None:
            # Konwertujemy cv_image do RGBA, jeśli nie jest w tym formacie
            if cv_image.shape[2] == 3:  # RGB bez kanału alfa
                alpha_channel = np.full((height, width, 1), 255, dtype=np.uint8)  # Pełna przezroczystość
                cv_image = np.concatenate((cv_image, alpha_channel), axis=2)  # Dodanie kanału alfa
                print("Dodano kanał alfa do obrazu bazowego.")

            self.layers[layer_name] = cv_image.copy()
            print(f"Skopiowano cv_image do warstwy '{layer_name}' (z_value = 1)")

    def initialize_layer_items(self, scene, cv_image):

            height, width, _ = cv_image.shape
            self.layer_items.clear()
            for layer_name, z_value in self.Z_VALUES.items():
                self.add_layer(layer_name, width, height, z_value, scene, cv_image)
                self.refresh_layer(layer_name)

    def refresh_layer(self, layer_name):
        if layer_name not in self.layers:
            print(f"Warstwa '{layer_name}' nie istnieje.")
            return

        layer_data = self.layers[layer_name]
        print(f"Odświeżanie warstwy '{layer_name}', wymiary: {layer_data.shape}")

        height, width, channels = layer_data.shape
        if channels != 4:
            print(f"Warstwa '{layer_name}' nie ma odpowiedniego formatu RGBA (liczba kanałów: {channels})")
            return

        bytes_per_line = 4 * width
        q_image = QImage(layer_data.data, width, height, bytes_per_line, QImage.Format_RGBA8888)
        if q_image.isNull():
            print(f"Nie udało się utworzyć QImage dla warstwy '{layer_name}'")
            return

        pixmap = QPixmap.fromImage(q_image)

        if layer_name in self.layer_items:
            pixmap_item = self.layer_items[layer_name]
            pixmap_item.setPixmap(pixmap)
            print(f"Zaktualizowano pixmapę dla warstwy '{layer_name}'")
        else:
            print(f"Warstwa '{layer_name}' nie posiada przypisanego QGraphicsPixmapItem")

        # Dodatkowa kontrola widoczności warstwy
        if layer_name not in self.visible_layers:
            print(f"Warstwa '{layer_name}' nie jest widoczna. Ustawiam widoczność na True.")
            self.set_visibility(layer_name, True)

    def refresh_all_layers(self):
        for layer_name in self.visible_layers:
            self.refresh_layer(layer_name)

    def set_visibility(self, layer_name, visible):
        if layer_name in self.layer_items:
            self.layer_items[layer_name].setVisible(visible)
            if visible:
                self.visible_layers.add(layer_name)
            else:
                self.visible_layers.discard(layer_name)

        else:
            print(f"Warstwa '{layer_name}' nie istnieje.")

    def get_layer(self, name):
        """Zwraca obraz warstwy i upewnia się, że jest w formacie RGBA."""
        layer = self.layers.get(name)
        if layer is not None and layer.shape[2] != 4:
            # Dodaj kanał alfa, jeśli go brakuje
            height, width = layer.shape[:2]
            alpha_channel = np.full((height, width, 1), 255, dtype=np.uint8)
            layer = np.concatenate((layer, alpha_channel), axis=2)
            self.layers[name] = layer
            print(f"Naprawiono warstwę '{name}' do formatu RGBA")
        return layer
