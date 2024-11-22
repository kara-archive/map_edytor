from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QPainterPath, QRegion
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsPathItem
from PyQt5.QtCore import QObject, Qt, QPoint, QRect
import numpy as np
import os
from controllers.data import DATA
import copy
from collections import deque
import math
from controllers.mode_manager import ModeManager

class MapController:
    def __init__(self):
        self.cv_image = None
        self.scene = None
        self.state_controller = None
        self.button_panel = None
        self.layer_manager = LayerManager(self)
        self.mode_manager = ModeManager(self,)
        self.snapshot_manager = SnapshotManager(self)

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


class SnapshotManager:
    """Zarządza snapshotami delta stanu aplikacji."""

    def __init__(self, map_controller, max_snapshots=10):
        self.map_controller = map_controller
        self.history = []  # Lista delta snapshotów
        self.future = []  # Lista przyszłych snapshotów dla redo
        self.max_snapshots = max_snapshots

    def create_snapshot(self, changes):
        """
        Tworzy snapshot delta, który zapisuje tylko zmiany.
        :param changes: Słownik zmian (np. zmiana warstw).
        """
        delta_snapshot = {
            "layers": changes.get("layers", {})
        }
        self.history.append(delta_snapshot)
        self.future.clear()  # Po stworzeniu nowego snapshotu czyścimy przyszłą historię
        if len(self.history) > self.max_snapshots:
            self.history.pop(0)  # Usuwamy najstarszy snapshot, aby utrzymać limit
        print("Utworzono delta snapshot. Aktualna długość historii: {}".format(len(self.history)))

    def undo(self):
        print("Undoing last snapshot...")
        """Cofa ostatnie zmiany, przywracając poprzedni snapshot delta."""
        if not self.history:
            print("Brak snapshotów do cofnięcia.")
            return

        last_snapshot = self.history.pop()
        self.future.append(last_snapshot)
        self._apply_delta(last_snapshot, undo=True)
        print("Cofnięto do poprzedniego snapshotu. Dane zostały przywrócone.")

    def redo(self):
        print("Redoing last snapshot...")
        """Przywraca cofnięty snapshot, jeśli istnieje."""
        if not self.future:
            print("Brak snapshotów do przywrócenia.")
            return

        next_snapshot = self.future.pop()
        self.history.append(next_snapshot)
        self._apply_delta(next_snapshot, undo=False)
        print("Przywrócono cofnięty snapshot. Dane zostały przywrócone.")

    def _apply_delta(self, delta_snapshot, undo):
        print(f"Applying delta, undo: {undo}")
        print(f"Delta snapshot: {delta_snapshot}")
        """
        Aplikuje zmiany zapisane w snapshot delta.
        :param delta_snapshot: Delta snapshot do zastosowania.
        :param undo: Czy wykonujemy operację cofnięcia (True) czy przywrócenia (False).
        """
        # Przywróć warstwy
        layers_delta = delta_snapshot["layers"]
        for layer_name, layer_data in layers_delta.items():
            if undo:
                self.map_controller.layer_manager.layers[layer_name] = layer_data["before"]
            else:
                self.map_controller.layer_manager.layers[layer_name] = layer_data["after"]
            self.map_controller.layer_manager.refresh_layer(layer_name)
