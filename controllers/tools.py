from PyQt5.QtGui import QPainter, QColor, QPainter, QColor, QPainterPath, QPen, QImage
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsPathItem
import cv2 as cv
import numpy as np
import copy

def flood_fill(layer, x, y, color):

    img_array = _convert_qimage_to_numpy(layer)
    width, height = layer.width(), layer.height()
    bytes_per_line = layer.bytesPerLine()
    image_format = layer.format()
    # OpenCV wymaga BGR, QImage jest w RGBA, więc konwersja
    img_bgr = cv.cvtColor(img_array, cv.COLOR_RGBA2BGR)

    # Pobranie koloru startowego
    start_color = img_bgr[y, x].tolist()
    fill_color = [color.blue(), color.green(), color.red()]
    # Jeśli kolor docelowy jest taki sam, nie rób nic
    if start_color == fill_color:
        return layer

    # Tworzenie maski dla floodFill (musi być większa o 2 px w każdą stronę)
    mask = np.zeros((height + 2, width + 2), np.uint8)

    # Flood fill w OpenCV
    cv.floodFill(img_bgr, mask, (x, y), fill_color, loDiff=(10, 10, 10), upDiff=(10, 10, 10), flags=cv.FLOODFILL_FIXED_RANGE)

    # Konwersja z powrotem do RGBA
    img_rgba = cv.cvtColor(img_bgr, cv.COLOR_BGR2RGBA)

    # Tworzenie nowego QImage z przetworzonej tablicy
    result_image = QImage(img_rgba.data, width, height, bytes_per_line, image_format)

    return result_image

def erase_area(layer, x, y, a=5,b=5):
    # Usuwanie (rysowanie przezroczystości)
    painter = QPainter(layer)
    painter.setCompositionMode(QPainter.CompositionMode_Clear)  # Ustaw tryb usuwania
    painter.setBrush(Qt.transparent)
    painter.drawRect(x - a, y - b, a * 2, b * 2)
    painter.end()
    return layer

def draw_icon(layer, icon, x, y):
    """Rysuje ikonę na warstwie."""
    painter = QPainter(layer)
    painter.drawImage(x - icon.width() // 2, y - icon.height() // 2, icon)
    painter.end()
    return layer

def find_icons(sample_icon, image, thresh = -1, exact = 0.9):
    """
    Wyszukuje współrzędne ikon w obrazie za pomocą dopasowywania szablonu.

    :param sample_icon: QImage ikony do wyszukiwania (np. "city" lub "farm").
    :param image: Obraz warstwy "buildings" jako macierz NumPy.
    :param thresh: Zamienia obraz na czarno biały o ustalonym progu 0-255, jeśli -1 wyłączone.
                   Przydaje się gdy ikony mają różne kolory np w army_mode.
    :param exact: Wymagany poziom dopasowania.
    :return: Lista współrzędnych (x, y) dopasowanych ikon (środek).
    """
    # Konwersja QImage na macierz NumPy
    icon = _convert_qimage_to_numpy(sample_icon)
    image = _convert_qimage_to_numpy(image)



    # Przekształcenie obrazu do skali szarości
    icon_gray = cv.cvtColor(icon, cv.COLOR_BGRA2GRAY)
    image_gray = cv.cvtColor(image, cv.COLOR_BGRA2GRAY)

    if thresh != -1:
        image_gray = cv.threshold(image_gray, thresh, 255, cv.THRESH_BINARY)[1]

    # Wykonanie dopasowania szablonu
    result = cv.matchTemplate(image_gray, icon_gray, cv.TM_CCOEFF_NORMED)

    # Ustal próg wykrywania (np. 0.8 dla wysokiego dopasowania)

    locations = np.where(result >= exact)

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
    bytes_per_line = qimage.bytesPerLine()
    ptr.setsize(height * bytes_per_line)  # 4 kanały (R, G, B, A)
    return np.frombuffer(ptr, dtype=np.uint8).reshape((height, width, 4))

def recolor_icon(image, target_color):
    if isinstance(target_color, tuple):
        target_color = QColor(*target_color)
    image = image.convertToFormat(QImage.Format_ARGB32)
    for y in range(image.height()):
        for x in range(image.width()):
            pixel_color = QColor(image.pixel(x, y))
            if pixel_color == QColor(255, 255, 255):
                image.setPixel(x, y, target_color.rgb())
    return image

class PixelSampler(dict):
    """Klasa odpowiedzialna za próbkowanie pikseli na mapie.
        Zwraca słownik państw i liczby współrzędnych, króre są na pikselu o kolorze państwa.
    """

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



class DrawPath:
    def __init__(self, layer, scene, color=QColor(128, 128, 128, 255), width=2, z_value=10):
        self.z_value = z_value
        self.layer = layer
        self.color = color
        self.width = width
        self.scene = scene
        self.path = QPainterPath()
        self.preview_item = None
        self.last_position = None

    def draw_path(self, event):
        if event.event_type == "click":
            self.start_path(event.x, event.y, self.scene)
            self.last_position = (event.x, event.y)

        elif event.event_type == "move" and self.last_position is not None:
            self.update_path(event.x, event.y)

        elif event.event_type == "release":
            self.end_path(self.scene)
            self.last_position = None

    def start_path(self, x, y, scene):
        self.path.moveTo(x, y)
        if self.preview_item is None:
            self.preview_item = QGraphicsPathItem()
            self.preview_item.setPen(QPen(self.color, self.width))
            self.preview_item.setZValue(self.z_value)
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
