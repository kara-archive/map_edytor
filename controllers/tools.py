from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt

def fill(layer, x, y, color):
    # Pobranie wymiarów obrazu
    height, width = layer.height(), layer.width()

    fill_color = (color[0], color[1], color[2])  # RGB
    start_color = QColor(layer.pixel(x, y)).getRgb()[:3]
    if start_color == fill_color or start_color in [(0, 0, 0), (47, 74, 113)]:
        print("Debug: Kolor startowy i docelowy są takie same lub czarny.")
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
    return(layer)

def draw_icon(layer_manager, layer, icon, x, y):
    """Rysuje ikonę budynku na warstwie."""

    painter = QPainter(layer)
    painter.drawImage(x - icon.width() // 2, y - icon.height() // 2, icon)
    painter.end()
    return layer

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
                    if self.is_similar_color(color, state.color.getRgb()[:3], self.tolerance):
                        counts[state.name] += 1  # Zlicz prowincję
                        break
        return counts

    @staticmethod
    def is_similar_color(color1, color2, tolerance):
        """Porównuje dwa kolory z uwzględnieniem tolerancji."""
        return all(abs(int(c1) - int(c2)) <= tolerance for c1, c2 in zip(color1, color2))
