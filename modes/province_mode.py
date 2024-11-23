from PyQt5.QtGui import QImage, QColor
from controllers.tools import Tools, PixelSampler
from controllers.data import DATA
import copy
import numpy as np

class ProvinceMode:
    """Obsługuje tryb prowincji."""
    def __init__(self, mode_manager, map_controller):
        self.map_controller = map_controller
        self.sampled_color = None
        self.active_state = None
        self.provinces = DATA.provinces
        self.mode_manager = mode_manager
        self.layer = self.mode_manager.layer_manager.layers.get("province")

    def handle_event(self, event):
        """Obsługuje zdarzenia w trybie prowincji."""
        if self.active_state != self.mode_manager.active_state:
            self.active_state = self.mode_manager.active_state
            self.sampled_color = None
        if event.event_type == "click" and event.button == "right":
            self.sampled_color = self.get_color_at(event.x, event.y)
        elif event.event_type == "click" and event.button == "left":
            if self.sampled_color:
                fill_color = self.sampled_color
            elif self.active_state and hasattr(self.active_state, 'color'):
                fill_color = self.active_state.color.getRgb()[:3]
            else:
                print("ProvinceMode: Brak aktywnego państwa lub koloru próbki.")
                return
            self.flood_fill(event.x, event.y, fill_color)

    def flood_fill(self, x, y, color):
        """
        Flood fill dla warstwy 'province' z tworzeniem snapshotów.

        Args:
            x (int): Współrzędna X punktu startowego.
            y (int): Współrzędna Y punktu startowego.
            color (tuple): Kolor docelowy w RGB.
        """
        if color == (0, 0, 0):
            return  # Ignoruj kolor czarny jako wypełnienie
                # Utwórz snapshot przed operacją

        layer = self.mode_manager.layer_manager.get_layer("province")
        before_layer = copy.deepcopy(layer)
        if layer is None:
            print("Warstwa 'province' nie istnieje.")
            return
        updated_layer = self._fill(layer, x, y, color)
        if updated_layer is not None:
            self.mode_manager.layer_manager.layers["province"] = updated_layer
            self.mode_manager.layer_manager.refresh_layer("province")
        self.sample_provinces()
        # Utwórz snapshot po operacji
        after_layer = copy.deepcopy(self.mode_manager.layer_manager.layers["province"])
        self.map_controller.snapshot_manager.create_snapshot({
            "layers": {
                "province": {
                    "before": before_layer,
                    "after": after_layer
                }
            }
        })

    def _fill(self, layer, x, y, color):

        # Pobranie wymiarów obrazu
        height, width, channels = layer.shape
        bytes_per_line = channels * width

        # Konwersja numpy array na QImage
        image = QImage(layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)

        fill_color = (color[0], color[1], color[2])  # RGB
        start_color = QColor(image.pixel(x, y)).getRgb()[:3]
        if start_color == fill_color or start_color == (0, 0, 0):
            print("Debug: Kolor startowy i docelowy są takie same lub czarny.")
            return

        # Pobranie rozmiarów obrazu
        pixels = image.bits()
        pixels.setsize(height * width * 4)  # 4 kanały (RGBA)
        pixel_array = np.frombuffer(pixels, dtype=np.uint8).reshape((height, width, 4))

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
            current_pixel = pixel_array[current_y, current_x][:3]  # Tylko RGB
            if not np.array_equal(current_pixel, start_color):
                continue

            # Wypełnij linię w prawo
            left_x, right_x = current_x, current_x
            while left_x > 0 and np.array_equal(pixel_array[current_y, left_x - 1][:3], start_color):
                left_x -= 1
            while right_x < width - 1 and np.array_equal(pixel_array[current_y, right_x + 1][:3], start_color):
                right_x += 1

            # Wypełnij linię i dodaj sąsiadów do kolejki
            for fill_x in range(left_x, right_x + 1):
                pixel_array[current_y, fill_x][:3] = fill_color  # Ustaw RGB
                if current_y > 0:  # Dodaj linię powyżej
                    queue.append((fill_x, current_y - 1))
                if current_y < height - 1:  # Dodaj linię poniżej
                    queue.append((fill_x, current_y + 1))

        # Aktualizacja obrazu
        updated_layer = np.copy(pixel_array)
        return updated_layer

    def sample_provinces(self):
        """
        Próbkuje piksele na mapie i przypisuje liczbę prowincji do odpowiednich państw.
        """
        print("Rozpoczynanie próbkowania prowincji...")
        states = self.map_controller.state_controller.get_states()
        image = self.mode_manager.layer_manager.layers.get("province")
        province_counts = PixelSampler(image, self.provinces, states)

        # Przypisanie liczby prowincji do obiektów State
        for state in states:
            state.provinces = province_counts.get(state.name, 0)
            print(f"Państwo {state.name} ma {state.provinces} prowincji")

    def get_color_at(self, x, y):
        print(f"Pobieranie koloru w punkcie ({x}, {y})")

        # Pobierz warstwę
        self.layer = self.mode_manager.layer_manager.get_layer("province")
        if self.layer is None:
            print("Warstwa 'province' nie istnieje.")
            return None

        # Upewnij się, że współrzędne są w granicach obrazu
        height, width, _ = self.layer.shape
        if not (0 <= x < width and 0 <= y < height):
            print(f"Punkt ({x}, {y}) znajduje się poza granicami obrazu.")
            return None

        # Pobierz kolor z warstwy
        self.sampled_color = tuple(self.layer[y, x][:3])  # Ignorujemy kanał alfa
        print(f"Pobrano kolor: {self.sampled_color}")
        return self.sampled_color
