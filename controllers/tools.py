from PyQt5.QtGui import QPainter, QColor, QPainter, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor
from PyQt5.QtWidgets import QGraphicsPathItem
import cv2 as cv
import numpy as np

def flood_fill(layer, x, y, color):
    # Pobranie wymiarów obrazu
    height, width = layer.height(), layer.width()

    fill_color = (color[0], color[1], color[2])  # RGB
    start_color = QColor(layer.pixel(x, y)).getRgb()[:3]
    if start_color in [(0, 0, 0), (47, 74, 113), fill_color]:
        return

    # BFS z liniowym przetwarzaniem
    queue = [(x, y)]
    visited = set()

    while queue:
        current_x, current_y = queue.pop(0)
        if (current_x, current_y) in visited:
            continue
        visited.add((current_x, current_y))

        # Zabezpieczenie przed przekroczeniem granic
        if current_x < 0 or current_y < 0 or current_x >= width or current_y >= height:
            continue

        # Sprawdź kolor bieżącego piksela
        current_pixel = QColor(layer.pixel(current_x, current_y)).getRgb()[:3]
        if current_pixel != start_color:
            continue

        # Wypełnij linię w prawo
        left_x, right_x = current_x, current_x
        while left_x > 0 and QColor(layer.pixel(left_x - 1, current_y)).getRgb()[:3] == start_color:
            left_x -= 1
        while right_x < width - 1 and QColor(layer.pixel(right_x + 1, current_y)).getRgb()[:3] == start_color:
            right_x += 1

        # Wypełnij linię i dodaj sąsiadów do kolejki
        for fill_x in range(left_x, right_x + 1):
            layer.setPixel(fill_x, current_y, QColor(*fill_color).rgba())
            if current_y > 0:  # Dodaj linię powyżej
                queue.append((fill_x, current_y - 1))
            if current_y < height - 1:  # Dodaj linię poniżej
                queue.append((fill_x, current_y + 1))

    return layer

def erase_area(layer, x, y, radius=5):
    # Usuwanie (rysowanie przezroczystości)
    painter = QPainter(layer)
    painter.setCompositionMode(QPainter.CompositionMode_Clear)  # Ustaw tryb usuwania
    painter.setBrush(Qt.transparent)
    painter.drawRect(x - radius, y - radius, radius * 2, radius * 2)
    painter.end()
    return layer

def draw_icon(layer, icon, x, y):
    """Rysuje ikonę budynku na warstwie."""

    painter = QPainter(layer)
    painter.drawImage(x - icon.width() // 2, y - icon.height() // 2, icon)
    painter.end()
    return layer

def find_icons(sample_icon, image):
    """
    Wyszukuje współrzędne ikon w obrazie za pomocą dopasowywania szablonu.

    :param sample_icon: QImage ikony do wyszukiwania (np. "city" lub "farm").
    :param image: Obraz warstwy "buildings" jako macierz NumPy.
    :return: Lista współrzędnych (x, y) dopasowanych ikon (środek).
    """
    # Konwersja QImage na macierz NumPy
    icon = _convert_qimage_to_numpy(sample_icon)
    image = _convert_qimage_to_numpy(image)

    # Przekształcenie obrazu do skali szarości
    icon_gray = cvtColor(icon, COLOR_BGRA2GRAY)
    image_gray = cvtColor(image, COLOR_BGRA2GRAY)

    # Wykonanie dopasowania szablonu
    result = matchTemplate(image_gray, icon_gray, TM_CCOEFF_NORMED)

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



def _convert_qimage_to_numpy(qimage):
    """
    Konwertuje QImage na macierz NumPy bez wymuszania formatu.
    Zakłada, że obraz jest w formacie RGBA8888.
    """
    width = qimage.width()
    height = qimage.height()
    ptr = qimage.bits()
    ptr.setsize(height * width * 4)  # 4 kanały (R, G, B, A)
    return np.frombuffer(ptr, dtype=np.uint8).reshape((height, width, 4))


class PixelSampler(dict):
    """Klasa odpowiedzialna za próbkowanie pikseli na mapie."""

    def __init__(self, image, sample_positions, states, tolerance=5):
        self.image = image
        self.sample_positions = sample_positions
        self.states = states
        self.tolerance = tolerance
        # Zapisanie wyników próbkowania bezpośrednio w self (dziedziczenie po dict)
        super().__init__(self._sample_pixels())

    def _sample_pixels(self):
        if self.image is None:
            return {}

        # Pobierz wymiary obrazu
        height, width = self.image.height(), self.image.width()

        # Inicjalizuj słownik do zliczania prowincji
        counts = {state.name: 0 for state in self.states}

        # Próbkuj piksele na podstawie pozycji
        for x, y in self.sample_positions:
            if 0 <= x < width and 0 <= y < height:
                color = QColor(self.image.pixel(x, y)).getRgb()[:3]  # Pobierz kolor w formacie RGB

                # Znajdź państwo odpowiadające kolorowi
                for state in self.states:
                    if self._is_similar_color(color, state.color.getRgb()[:3], self.tolerance):
                        counts[state.name] += 1  # Zlicz prowincję
                        break
        return counts

    @staticmethod
    def _is_similar_color(color1, color2, tolerance):
        """Porównuje dwa kolory z uwzględnieniem tolerancji."""
        return all(abs(int(c1) - int(c2)) <= tolerance for c1, c2 in zip(color1, color2))



class IconFinder(list):
    def __init__(self, sample_icon, layer):
        super().__init__()
        self.sample_icon = sample_icon
        self.layer = layer
        self.layer_width, self.layer_height = layer.width(), layer.height()
        self.icon_width, self.icon_height = sample_icon.width(), sample_icon.height()

        # Buforowanie danych pikseli warstwy
        self.layer_pixels = [
            [layer.pixel(x, y) for y in range(self.layer_height)]
            for x in range(self.layer_width)
        ]

        # Buforowanie danych pikseli ikony
        self.sample_pixels = [
            [sample_icon.pixel(ix, iy) for iy in range(self.icon_height)]
            for ix in range(self.icon_width)
        ]

        # Maskowanie przezroczystości
        self.transparency_mask = [
            [QColor(self.sample_pixels[ix][iy]).alpha() > 0 for iy in range(self.icon_height)]
            for ix in range(self.icon_width)
        ]
        self.extend(self.find_icon_positions())

    def find_icon_positions(self):
        positions = []

        for x in range(self.layer_width - self.icon_width + 1):
            for y in range(self.layer_height - self.icon_height + 1):
                if self._is_icon_at_position(x, y):
                    center_x = x + self.icon_width // 2
                    center_y = y + self.icon_height // 2
                    positions.append((center_x, center_y))

        return positions

    def _is_icon_at_position(self, x, y):
        for ix in range(self.icon_width):
            for iy in range(self.icon_height):
                if not self.transparency_mask[ix][iy]:
                    continue  # Ignoruj przezroczyste piksele
                if self.sample_pixels[ix][iy] != self.layer_pixels[x + ix][y + iy]:
                    return False  # Rozbieżność w pikselach
        return True


class DrawPath:
    def __init__(self, layer, color=QColor(128, 128, 128, 255), width=2):
        self.layer = layer
        self.color = color
        self.width = width
        self.path = QPainterPath()
        self.preview_item = None

    def start_path(self, x, y, scene):
        self.path.moveTo(x, y)
        if self.preview_item is None:
            self.preview_item = QGraphicsPathItem()
            self.preview_item.setPen(QPen(self.color, self.width))
            scene.addItem(self.preview_item)
        self.preview_item.setPath(self.path)

    def update_path(self, x, y):
        self.path.lineTo(x, y)
        if self.preview_item:
            self.preview_item.setPath(self.path)

    def end_path(self, scene):
        painter = QPainter(self.layer)
        pen = QPen(self.color)
        pen.setWidth(self.width)
        painter.setPen(pen)
        painter.drawPath(self.path)
        painter.end()
        if self.preview_item:
            scene.removeItem(self.preview_item)
            self.preview_item = None
