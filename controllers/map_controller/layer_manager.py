from PyQt5.QtGui import QImage, QPixmap, QColor # type: ignore
from PyQt5.QtWidgets import QGraphicsPixmapItem # type: ignore # type: ignore

class LayerManager:
    def __init__(self, map_controller):
        self.layers = {}  # Przechowuje dane warstw w formie QImage
        self.layer_items = {}  # QGraphicsPixmapItem dla każdej warstwy
        self.visible_layers = set()  # Nazwy widocznych warstw
        self.Z_VALUES = {}
        self.map_controller = map_controller

    def get_map_controller(self):
        return self.map_controller

    def add_layer(self, layer_name, width, height, z_value, scene, cv_image):
        if layer_name not in self.layers:
            # Tworzenie brakującej warstwy jako QImage
            self.layers[layer_name] = QImage(width, height, QImage.Format_RGBA8888)
            self.layers[layer_name].fill(QColor(0, 0, 0, 0))  # Przezroczysta warstwa
            print(f"Warstwa '{layer_name}' dodana: {width}x{height}")

        # Tworzenie QGraphicsPixmapItem
        pixmap_item = QGraphicsPixmapItem()
        pixmap_item.setZValue(z_value)
        scene.addItem(pixmap_item)
        self.layer_items[layer_name] = pixmap_item
        self.set_visibility(layer_name, True)

        # Jeśli warstwa ma być zainicjalizowana obrazem bazowym
        if z_value == 0 and cv_image is not None:
            self.layers[layer_name] = cv_image.copy()
            print(f"Skopiowano cv_image do warstwy '{layer_name}' (z_value = 1)")

    def initialize_layer_items(self, scene, cv_image):
        height, width = cv_image.height(), cv_image.width()
        self.layer_items.clear()
        for layer_name, z_value in self.Z_VALUES.items():
            self.add_layer(layer_name, width, height, z_value, scene, cv_image)
            self.refresh_layer(layer_name)

    def refresh_layer(self, layer_name):
        if layer_name not in self.layers:
            print(f"Warstwa '{layer_name}' nie istnieje.")
            return

        layer_data = self.layers[layer_name]

        pixmap = QPixmap.fromImage(layer_data)

        if layer_name in self.layer_items:
            pixmap_item = self.layer_items[layer_name]
            pixmap_item.setPixmap(pixmap)
        else:
            print(f"Warstwa '{layer_name}' nie posiada przypisanego QGraphicsPixmapItem")

        # Dodatkowa kontrola widoczności warstwy
        if layer_name not in self.visible_layers:
            print(f"Warstwa '{layer_name}' nie jest widoczna. Ustawiam widoczność na True.")

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
        """Zwraca obraz warstwy jako QImage."""
        return self.layers.get(name)
