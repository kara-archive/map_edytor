from PyQt5.QtGui import QImage, QPixmap, QColor, QPainterPath, QRegion
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsPathItem
from PyQt5.QtCore import QObject, Qt, QPoint, QRect
import numpy as np
import os
from controllers.map_controller.layer_manager import LayerManager
from controllers.map_controller.snapshot_manager import SnapshotManager
from controllers.map_controller.mode_manager import ModeManager


class MapController:
    def __init__(self):
        self.cv_image = None
        self.scene = None
        self.state_controller = None
        self.button_panel = None
        self.layer_manager = LayerManager(self)
        self.snapshot_manager = SnapshotManager(self)
        self.mode_manager = ModeManager(self)

    def set_scene(self, scene):
        """Ustawia scenę dla kontrolera."""
        self.scene = scene

    def load_map(self, file_path):
        """Wczytuje mapę z pliku i inicjalizuje warstwy."""
        image = QImage(file_path)
        if image.isNull():
            self.button_panel.load_data()
            self.export_image("Tury/0.Tura.png")
        else:
            # Konwertujemy obraz na format RGBA8888
            image = image.convertToFormat(QImage.Format_RGBA8888)
            width, height = image.width(), image.height()
            bytes_per_line = image.bytesPerLine()
            data = image.bits().asstring(bytes_per_line * height)
            array = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 4))

            # Upewnij się, że obraz ma 4 kanały
            if array.shape[2] != 4:
                print(f"Uwaga: Obraz nie jest w formacie RGBA! Zmieniam format.")
                alpha_channel = np.full((height, width, 1), 255, dtype=np.uint8)  # Pełna przezroczystość
                array = np.concatenate((array, alpha_channel), axis=2)  # Dodanie kanału alfa

            self.cv_image = array.copy()  # Zachowujemy obraz z kanałem alfa

            # Aktualizuj scenę - wyświetl pustą warstwę (jeśli taka istnieje)
            self.update_scene()

            # Inicjalizuj elementy warstw
            self.layer_manager.initialize_layer_items(self.scene, self.cv_image)

    def update_scene(self):
        """Odświeża obraz na scenie."""
        # Tworzenie pustej warstwy, aby odświeżyć scenę
        height, width, _ = self.cv_image.shape if self.cv_image is not None else (600, 800, 4)  # Domyślne wymiary
        bytes_per_line = 4 * width
        empty_layer = np.zeros((height, width, 4), dtype=np.uint8)  # Pusta warstwa RGBA

        # Tworzenie QImage na podstawie pustej warstwy
        q_image = QImage(empty_layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(q_image)

        # Dodanie pustej warstwy do sceny
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(pixmap_item)

    def _flatten_image(self):
        """
        Spłaszcza obraz, łącząc bazowy obraz mapy i wszystkie widoczne warstwy.
        :return: Spłaszczony obraz jako numpy.ndarray.
        """
        if self.cv_image is None:
            raise ValueError("Brak obrazu bazowego (cv_image).")

        # Rozpocznij od obrazu bazowego
        flattened_image = self.cv_image.copy()

        # Nakładanie widocznych warstw
        for layer_name in self.layer_manager.visible_layers:
            layer_data = self.layer_manager.get_layer(layer_name)
            if layer_data is not None:
                alpha_channel = layer_data[:, :, 3] / 255.0  # Normalizuj kanał alfa
                for c in range(3):  # RGB
                    flattened_image[:, :, c] = (
                        alpha_channel * layer_data[:, :, c] +
                        (1 - alpha_channel) * flattened_image[:, :, c]
                    )

        return flattened_image

    def export_image(self, file_path):
        """
        Spłaszcza obraz i zapisuje go do pliku.
        :param file_path: Ścieżka do zapisu obrazu.
        """
        try:
            # Spłaszcz obraz
            flattened_image = self._flatten_image()

            # Konwertuj do QImage
            height, width, _ = flattened_image.shape
            bytes_per_line = 4 * width
            q_image = QImage(flattened_image.data, width, height, bytes_per_line, QImage.Format_RGBA8888)

            # Zapisz do pliku
            if not q_image.save(file_path):
                raise IOError(f"Nie udało się zapisać obrazu do pliku: {file_path}")

            print(f"Obraz został zapisany do: {file_path}")
        except Exception as e:
            print(f"Błąd podczas eksportu obrazu: {e}")

    def save_layers_to_png(self, output_dir):
        """
        Zapisuje cv_image oraz wszystkie warstwy jako pliki PNG w podanym katalogu.
        :param output_dir: Ścieżka do katalogu, w którym zostaną zapisane pliki.
        """
        os.makedirs(output_dir, exist_ok=True)

        # Zapisz cv_image
        if self.cv_image is not None:
            cv_image_path = os.path.join(output_dir, "base_image.png")
            height, width, _ = self.cv_image.shape
            bytes_per_line = 3 * width
            contiguous_image = np.ascontiguousarray(self.cv_image)  # Zapewnij ciągłość pamięci
            q_image = QImage(contiguous_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            if not q_image.save(cv_image_path):
                print(f"Nie udało się zapisać obrazu bazowego jako {cv_image_path}")
            else:
                print(f"Obraz bazowy zapisany jako {cv_image_path}")

        # Zapisz wszystkie warstwy
        for layer_name, layer_data in self.layer_manager.layers.items():
            if layer_data is not None:
                layer_image_path = os.path.join(output_dir, f"{layer_name}.png")
                height, width, _ = layer_data.shape
                bytes_per_line = 4 * width
                contiguous_layer = np.ascontiguousarray(layer_data)  # Zapewnij ciągłość pamięci
                q_image = QImage(contiguous_layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)
                if not q_image.save(layer_image_path):
                    print(f"Nie udało się zapisać warstwy '{layer_name}' jako {layer_image_path}")
                else:
                    print(f"Warstwa '{layer_name}' zapisana jako {layer_image_path}")

    def load_layer_from_png(self, layer_name, image_path):
        """
        Ładuje warstwę z pliku PNG i zapisuje ją w LayerManager.
        :param layer_name: Nazwa warstwy.
        :param image_path: Ścieżka do pliku PNG.
        """
        image = QImage(image_path)
        if image.isNull():
            raise FileNotFoundError(f"Nie znaleziono pliku {image_path}")

        # Konwersja do numpy array
        image = image.convertToFormat(QImage.Format_RGBA8888)
        width, height = image.width(), image.height()
        bytes_per_line = image.bytesPerLine()
        data = image.bits().asstring(bytes_per_line * height)
        array = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 4)

        if layer_name in self.layer_manager.layers:
            print(f"Nadpisywanie istniejącej warstwy '{layer_name}'")
            self.layer_manager.layers[layer_name] = array
        else:
            print(f"Tworzenie nowej warstwy '{layer_name}'")
            z_value = self.Z_VALUES.get(layer_name, 0)
            self.layer_manager.add_layer(layer_name, width, height, z_value, self.scene)
            self.layer_manager.layers[layer_name] = array

        # Odśwież QGraphicsPixmapItem dla tej warstwy
        pixmap_item = self.layer_manager.layer_items.get(layer_name)
        if pixmap_item:
            pixmap = QPixmap.fromImage(image)
            pixmap_item.setPixmap(pixmap)
            print(f"Warstwa '{layer_name}' została odświeżona.")

        self.layer_manager.set_visibility(layer_name, True)
        print(f"Warstwa '{layer_name}' załadowana z {image_path}")

    def get_scene(self):
        return self.scene

    def get_image(self):
        return self.cv_image
