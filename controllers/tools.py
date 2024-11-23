from PyQt5.QtGui import QPainter, QImage, QColor, QPen
from PyQt5.QtCore import Qt
import numpy as np
import math
class Tools:

    @staticmethod
    def erase_area(map_controller, layer_manager, layer_name, x, y, radius=5):
        """
        Usuwa obszar z podanej warstwy, ustawiając piksele w obszarze na przezroczyste.

        :param layer_manager: Obiekt LayerManager odpowiedzialny za warstwy.
        :param layer_name: Nazwa warstwy, na której działa gumka.
        :param x: Współrzędna X środka gumki.
        :param y: Współrzędna Y środka gumki.
        :param radius: Promień gumki.
        """
        # Pobierz warstwę z LayerManager
        layer = layer_manager.get_layer(layer_name)
        if layer is None:
            print(f"Brak warstwy '{layer_name}' do usuwania.")
            return

        # Pobranie wymiarów obrazu warstwy
        height, width, _ = layer.shape
        bytes_per_line = 4 * width
        layer_image = QImage(layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)

        # Usuwanie (rysowanie przezroczystości)
        painter = QPainter(layer_image)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)  # Ustaw tryb usuwania
        painter.setBrush(Qt.transparent)
        painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
        painter.end()

        # Aktualizacja danych warstwy
        layer_data = layer_image.bits().asstring(bytes_per_line * height)
        layer_manager.layers[layer_name] = np.frombuffer(layer_data, dtype=np.uint8).reshape(height, width, 4)

        # Odświeżenie graficznej reprezentacji warstwy
        layer_manager.refresh_layer(layer_name)  # Zamiana z refresh_layer_item

    @staticmethod
    def draw_shape(layer_manager, layer_name, shape, *args, **kwargs):
        """
        Rysuje kształt na podanej warstwie.
        :param shape: Typ kształtu (np. 'ellipse', 'rectangle', 'line').
        :param args: Argumenty definiujące położenie i wymiary kształtu.
        :param kwargs: Opcjonalne argumenty, np. kolor, szerokość linii.
        """
        layer = layer_manager.get_layer(layer_name)
        if layer is None:
            raise ValueError(f"Warstwa '{layer_name}' nie istnieje.")

        # Tworzenie obrazu warstwy
        height, width, _ = layer.shape
        bytes_per_line = 4 * width
        layer_image = QImage(layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)

        painter = QPainter(layer_image)
        pen = QPen(kwargs.get("color", Qt.black))
        pen.setWidth(kwargs.get("width", 1))
        painter.setPen(pen)

        if shape == "ellipse":
            x, y, w, h = args
            painter.drawEllipse(x, y, w, h)
        elif shape == "rectangle":
            x, y, w, h = args
            painter.drawRect(x, y, w, h)
        elif shape == "line":
            x1, y1, x2, y2 = args
            painter.drawLine(x1, y1, x2, y2)

        painter.end()
        layer_data = layer_image.bits().asstring(bytes_per_line * height)
        layer_manager.layers[layer_name] = np.frombuffer(layer_data, dtype=np.uint8).reshape(height, width, 4)
        layer_manager.refresh_layer(layer_name)

class PixelSampler(dict):
    """Klasa odpowiedzialna za próbkowanie pikseli na mapie."""

    def __init__(self, image, sample_positions, states, tolerance=5):
        self.image = image
        self.sample_positions = sample_positions
        self.states = states
        self.tolerance = tolerance
        print(self.image)
        # Zapisanie wyników próbkowania bezpośrednio w self (dziedziczenie po dict)
        super().__init__(self._sample_pixels())

    def _sample_pixels(self):
        if self.image is None:
            return {}

        # Pobierz wymiary obrazu
        height, width, _ = self.image.shape

        # Inicjalizuj słownik do zliczania prowincji
        counts = {state.name: 0 for state in self.states}

        # Próbkuj piksele na podstawie pozycji
        for x, y in self.sample_positions:
            if 0 <= x < width and 0 <= y < height:
                color = tuple(self.image[y, x])  # Pobierz kolor w formacie RGB

                # Znajdź państwo odpowiadające kolorowi
                for state in self.states:
                    if self.is_similar_color(color, state.color.getRgb()[:3], self.tolerance):
                        counts[state.name] += 1  # Zlicz prowincję
                        break
        return counts

    @staticmethod
    def is_similar_color(color1, color2, tolerance):
        """Porównuje dwa kolory z uwzględnieniem tolerancji."""
        return all(abs(int(c1) - int(c2)) <= tolerance for c1, c2 in zip(color1, color2))
