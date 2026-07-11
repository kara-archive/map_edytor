from PyQt5.QtGui import QImage, QPixmap, QColor, QPainter # type: ignore
from PyQt5.QtWidgets import QGraphicsPixmapItem # type: ignore
import os
from .layer_manager import LayerManager
from .snapshot_manager import SnapshotManager
from .mode_manager import ModeManager
from controllers.data import MapData
from controllers.archive_manager import ArchiveManager


class MapController:
    def __init__(self):
        self.cv_image = None
        self.scene = None
        self.state_controller = None
        self.button_panel = None
        self.buttons_info = []
        self.shortcuts = {}
        self.layer_manager = LayerManager(map_controller=self)
        self.snapshot_manager = SnapshotManager(map_controller=self)
        self.mode_manager = ModeManager(map_controller=self)
        self.map_data = MapData()
        self.archive_manager = ArchiveManager(map_controller=self)
        self.bg_item = None

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

    def init_modes(self):
        self.mode_manager.init_modes()

    def update_scene(self):
        """Odświeża obraz na scenie."""
        if hasattr(self, 'bg_item') and self.bg_item is not None:
            try:
                self.scene.removeItem(self.bg_item)
            except Exception:
                pass
            self.bg_item = None

        height, width = self.cv_image.height(), self.cv_image.width() if self.cv_image is not None else (600, 800)

        # Dodanie obrazu bazowego jako tła na samym dole (Z = -10)
        if self.cv_image is not None:
            bg_pixmap = QPixmap.fromImage(self.cv_image)
            self.bg_item = QGraphicsPixmapItem(bg_pixmap)
            self.bg_item.setZValue(-10)
            self.scene.addItem(self.bg_item)

        # Tworzenie pustej warstwy
        empty_layer = QImage(width, height, QImage.Format_RGBA8888)
        empty_layer.fill(QColor(0, 0, 0, 0))  # Przezroczysta warstwa

        pixmap = QPixmap.fromImage(empty_layer)
        pixmap_item = QGraphicsPixmapItem(pixmap)
        pixmap_item.setZValue(-100)  # Poniżej tła
        self.scene.addItem(pixmap_item)

    def _flatten_image(self):
        """
        Spłaszcza obraz, łącząc bazowy obraz mapy i wszystkie widoczne warstwy.
        :return: Spłaszczony obraz jako QImage.
        """
        if self.cv_image is None:
            raise ValueError("Brak obrazu bazowego do spłaszczenia.")

        # Zaczynamy od czystego obrazu bazowego
        flattened_image = self.cv_image.copy().convertToFormat(QImage.Format_RGBA8888)

        # Rysujemy wszystkie widoczne warstwy w kolejności rosnących Z-values
        for value in sorted(self.layer_manager.Z_VALUES.values()):
            layer_name = [key for key, val in self.layer_manager.Z_VALUES.items() if val == value][0]
            if layer_name in self.layer_manager.visible_layers:
                layer_data = self.layer_manager.get_layer(layer_name)
                """
                (TODO) gówniany kod rozjebał widok mapy, zamiast dodawać deseń kropek z warstwy biome, to przykrywa mi warstwę province, 
                to w ogóle nie powinno znajdować się tutaj, a w biome_mode.py

                if layer_data is not None and layer_name == "biome":
                    temp_image = layer_data.copy()
                    painter = QPainter(temp_image)
                    painter.setCompositionMode(QPainter.CompositionMode_Clear)
                    for y in range(4, temp_image.height(), 6):
                        for x in range(4, temp_image.width(), 6):
                            painter.drawPoint(x, y)
                    painter.end()
                    layer_data = temp_image
                """

                painter = QPainter(flattened_image)
                painter.drawImage(0, 0, layer_data)
                painter.end()

        return flattened_image

    def export_image(self, file_path, table_image=None):
        """
        Spłaszcza obraz i zapisuje go do pliku.
        Jeśli podano table_image (QImage), skaluje go i dokłada do mapy:
        - na dole, jeśli mapa jest szersza niż wyższa (landscape),
        - po lewej, jeśli mapa jest wyższa niż szersza (portrait).
        :param file_path: Ścieżka do zapisu obrazu.
        :param table_image: Opcjonalny QImage z tabelą danych.
        """
        try:
            flattened_image = self._flatten_image()

            if table_image is not None and not table_image.isNull():
                map_w = flattened_image.width()
                map_h = flattened_image.height()

                if map_w < map_h:
                    # Portrait — mapa wyższa, tabela na dole (dokłada do krótszego boku)
                    scaled_table = table_image.scaledToWidth(map_w)
                    combined = QImage(map_w, map_h + scaled_table.height(), QImage.Format_RGBA8888)
                    combined.fill(QColor(0, 0, 0, 255))
                    painter = QPainter(combined)
                    painter.drawImage(0, 0, flattened_image)
                    painter.drawImage(0, map_h, scaled_table)
                    painter.end()
                else:
                    # Landscape — mapa szersza, tabela po lewej (dokłada do krótszego boku)
                    scaled_table = table_image.scaledToHeight(map_h)
                    combined = QImage(map_w + scaled_table.width(), map_h, QImage.Format_RGBA8888)
                    combined.fill(QColor(0, 0, 0, 255))
                    painter = QPainter(combined)
                    painter.drawImage(scaled_table.width(), 0, flattened_image)
                    painter.drawImage(0, 0, scaled_table)
                    painter.end()

                flattened_image = combined

            if not flattened_image.save(file_path):
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
            if not self.cv_image.save(cv_image_path):
                print(f"Nie udało się zapisać obrazu bazowego jako {cv_image_path}")
            else:
                print(f"Obraz bazowy zapisany jako {cv_image_path}")

        # Zapisz wszystkie warstwy
        for layer_name, layer_data in self.layer_manager.layers.items():
            if layer_data is not None:
                layer_image_path = os.path.join(output_dir, f"{layer_name}.png")
                if not layer_data.save(layer_image_path):
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

        # Konwersja do QImage.Format_RGBA8888
        image = image.convertToFormat(QImage.Format_RGBA8888)

        if layer_name in self.layer_manager.layers:
            print(f"Nadpisywanie istniejącej warstwy '{layer_name}'")
            self.layer_manager.layers[layer_name] = image
        else:
            print(f"Tworzenie nowej warstwy '{layer_name}'")
            z_value = self.layer_manager.Z_VALUES.get(layer_name, 0)
            self.layer_manager.add_layer(layer_name, image.width(), image.height(), z_value, self.scene, self.cv_image)
            self.layer_manager.layers[layer_name] = image

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

    def get_biome_at(self, x, y):
        """Pobiera nazwę biomu na podanych współrzędnych."""
        biome_layer = self.layer_manager.get_layer("biome")
        if biome_layer is None or not (0 <= x < biome_layer.width() and 0 <= y < biome_layer.height()):
            return "plain"

        color = biome_layer.pixelColor(x, y)
        if color.alpha() == 0:
            return "plain"

        # Mapowanie kolorów na nazwy biomów
        hex_val = color.name().lower()
        if hex_val == "#4080bf":
            return "water"
        elif hex_val == "#d6b365":
            return "desert"
        elif hex_val == "#2e7d32":
            return "forest"
        elif hex_val == "#8bc34a":
            return "plain"
        elif hex_val == "#8d8d8d":
            return "mountains"
        return "plain"
