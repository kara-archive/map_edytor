from controllers.tools import Tools, PixelSampler
from controllers.data import DATA
from PyQt5.QtGui import QImage, QColor, QPainter, QPixmap
from modes.base_mode import Mode

class ProvinceMode(Mode):
    """Obsługuje tryb prowincji."""
    def __init__(self, mode_manager, map_controller):
        super().__init__(map_controller)
        self.map_controller = map_controller
        self.sampled_color = None
        self.active_state = None
        self.mode_manager = mode_manager
        self.layer = self.map_controller.layer_manager.layers.get("province")

    def handle_event(self, event):
        """Obsługuje zdarzenia w trybie prowincji."""
        if self.active_state != self.mode_manager.active_state:
            self.active_state = self.mode_manager.active_state
            self.sampled_color = None
        if event.event_type == "click":
            self.start_snap("province")
        if event.event_type == "click" and event.button == "right":
            self.sampled_color = self.get_color_at(event.x, event.y)
        elif event.button == "left":
            if self.sampled_color:
                fill_color = self.sampled_color
            elif self.active_state and hasattr(self.active_state, 'color'):
                fill_color = self.active_state.color
            else:
                print("ProvinceMode: Brak aktywnego państwa lub koloru próbki.")
                return
            self.flood_fill(event.x, event.y, fill_color)
        if event.event_type == "release":
            self.end_snap("province")
            self.sample_provinces()

    def setup_menu(self):
        self.map_controller.button_panel.update_dynamic_menu([])

    def copy_image(self, cv_image):
        # Jeśli warstwa ma być zainicjalizowana obrazem bazowym
        if cv_image is not None:
            if cv_image.format() != QImage.Format_RGBA8888:
                cv_image = cv_image.convertToFormat(QImage.Format_RGBA8888)
                print("Dodano kanał alfa do obrazu bazowego.")

            self.map_controller.layer_manager.layers["province"] = cv_image.copy()
            print(f"Skopiowano cv_image do warstwy 'province' (z_value = 1)")
        else:
            print("ProvinceMode: cv_image jest None")

    def flood_fill(self, x, y, color):
        layer = self.map_controller.layer_manager.get_layer("province")
        if layer is None:
            print("ProvinceMode: Warstwa 'province' nie została znaleziona.")
            return

        target_color = QColor(layer.pixel(x, y))
        fill_color = QColor(color)

        if target_color == fill_color:
            return

        painter = QPainter(layer)
        painter.setPen(fill_color)
        painter.setBrush(fill_color)

        # Implementacja algorytmu flood fill
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if layer.pixel(cx, cy) == target_color.rgb():
                painter.drawPoint(cx, cy)
                stack.extend([(cx + dx, cy + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]])
        painter.end()

        # Odśwież QGraphicsPixmapItem dla tej warstwy
        pixmap_item = self.map_controller.layer_manager.layer_items.get("province")
        if pixmap_item:
            pixmap = QPixmap.fromImage(layer)
            pixmap_item.setPixmap(pixmap)

        self.map_controller.layer_manager.set_visibility("province", True)
        print(f"Warstwa 'province' została zaktualizowana.")

    def sample_provinces(self):
        states = self.map_controller.state_controller.get_states()
        image = self.mode_manager.layer_manager.layers.get("province")
        province_counts = PixelSampler(image, DATA.provinces, states)

        # Przypisanie liczby prowincji do obiektów State
        for state in states:
            state.provinces = province_counts.get(state.name, 0)
            print(f"Państwo {state.name} ma {state.provinces} prowincji")

    def get_color_at(self, x, y):
        layer = self.map_controller.layer_manager.get_layer("province")
        if layer is None:
            return None
        return QColor(layer.pixel(x, y))
