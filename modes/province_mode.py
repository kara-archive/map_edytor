from PyQt5.QtGui import QImage, QColor
from controllers.tools import Tools, PixelSampler
from controllers.data import DATA
import copy
import numpy as np
from controllers.state_controller import State
class ProvinceMode:
    """Obsługuje tryb prowincji."""
    def __init__(self, mode_manager, map_controller):
        self.map_controller = map_controller
        self.sampled_color = None
        self.active_state = None
        self.mode_manager = mode_manager
        self.layer = self.mode_manager.layer_manager.layers.get("province")
        self.copy_image(self.map_controller.cv_image)

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

    def copy_image(self, cv_image):
        # Jeśli warstwa ma być zainicjalizowana obrazem bazowym
        if cv_image is not None:
            if cv_image.shape[2] == 3:  # RGB bez kanału alfa
                alpha_channel = np.full((height, width, 1), 255, dtype=np.uint8)  # Pełna przezroczystość
                cv_image = np.concatenate((cv_image, alpha_channel), axis=2)  # Dodanie kanału alfa
                print("Dodano kanał alfa do obrazu bazowego.")

            self.mode_manager.layer_manager.layers["province"] = cv_image.copy()
            print(f"Skopiowano cv_image do warstwy '{layer_name}' (z_value = 1)")

    def flood_fill(self, x, y, color):
        """
        Flood fill dla warstwy 'province' z tworzeniem snapshotów.

        Args:
            x (int): Współrzędna X punktu startowego.
            y (int): Współrzędna Y punktu startowego.
            color (tuple): Kolor docelowy w RGB.
        """


        layer = self.mode_manager.layer_manager.get_layer("province")
        before_layer = copy.deepcopy(layer)
        if layer is None:
            print("Warstwa 'province' nie istnieje.")
            return
        updated_layer = Tools.fill(layer, x, y, color)
        if updated_layer is not None:
            self.mode_manager.layer_manager.layers["province"] = updated_layer
            self.mode_manager.layer_manager.refresh_layer("province")
            self.sample_provinces()
            # Utwórz snapshot po operacji
            after_layer = copy.deepcopy(self.mode_manager.layer_manager.get_layer("province"))
            self.map_controller.snapshot_manager.create_snapshot({"layers": {"province": {"before": before_layer,"after": after_layer}}})

    def sample_provinces(self):
        """
        Próbkuje piksele na mapie i przypisuje liczbę prowincji do odpowiednich państw.
        """
        print("Rozpoczynanie próbkowania prowincji...")
        states = self.map_controller.state_controller.get_states()
        image = self.mode_manager.layer_manager.layers.get("province")
        province_counts = PixelSampler(image, DATA.provinces, states)

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
