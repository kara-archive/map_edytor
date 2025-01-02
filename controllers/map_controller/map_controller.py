from PyQt5.QtGui import QImage, QPixmap, QColor # type: ignore
from PyQt5.QtWidgets import QGraphicsPixmapItem # type: ignore
import numpy as np # type: ignore
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
        self.snapshot_manager = SnapshotManager(map_controller=self)
        self.mode_manager = ModeManager(map_controller=self)

    def set_scene(self, scene):
        """Ustawia scenę dla kontrolera."""
        self.scene = scene

    def load_map(self, file_path):
        """Wczytuje mapę z pliku i inicjalizuje warstwy."""
        image = QImage(file_path)
        if image.isNull():
            self.button_panel.load_data()
            #self.export_image("Tury/0.Tura.png")
        else:
            # Konwertujemy obraz na format RGBA8888
            image = image.convertToFormat(QImage.Format_RGBA8888)
            self.cv_image = image.copy()  # Zachowujemy obraz jako QImage

            # Aktualizuj scenę - wyświetl pustą warstwę (jeśli taka istnieje)
            self.update_scene()

            # Inicjalizuj elementy warstw
            self.layer_manager.initialize_layer_items(self.scene, self.cv_image)

    def update_scene(self):
        """Odświeża obraz na scenie."""
        # Tworzenie pustej warstwy, aby odświeżyć scenę
        height, width = self.cv_image.height(), self.cv_image.width() if self.cv_image is not None else (600, 800)
        empty_layer = QImage(width, height, QImage.Format_RGBA8888)
        empty_layer.fill(QColor(0, 0, 0, 0))  # Przezroczysta warstwa

        # Tworzenie QPixmap na podstawie pustej warstwy
        pixmap = QPixmap.fromImage(empty_layer)

        # Dodanie pustej warstwy do sceny
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(pixmap_item)

    def _flatten_image(self):
        """
        Spłaszcza obraz, łącząc bazowy obraz mapy i wszystkie widoczne warstwy.
        :return: Spłaszczony obraz jako numpy.ndarray.
        """
        base_layer_name = next((name for name, z in self.layer_manager.Z_VALUES.items() if z == 0), None)
        if base_layer_name is None:
            raise ValueError("Nie znaleziono warstwy bazowej z z_value równym 0.")

        flattened_image = self.layer_manager.get_layer(base_layer_name)
        if flattened_image is None:
            raise ValueError(f"Warstwa bazowa '{base_layer_name}' nie została znaleziona.")

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
            bytes_per_line = 4 * width
            contiguous_image = self.cv_image if self.cv_image.flags['C_CONTIGUOUS'] else np.ascontiguousarray(self.cv_image)  # Zapewnij ciągłość pamięci
            q_image = QImage(contiguous_image.data, width, height, bytes_per_line, QImage.Format_RGBA8888)
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
                if not layer_data.flags['C_CONTIGUOUS']:
                    layer_data = np.ascontiguousarray(layer_data)  # Zapewnij ciągłość pamięci
                contiguous_layer = layer_data
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

        self.layer_manager.set_visibility(layer_name, True)
        print(f"Warstwa '{layer_name}' załadowana z {image_path}")

    def get_scene(self):
        return self.scene

    def get_image(self):
        return self.cv_image
