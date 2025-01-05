from PyQt5.QtGui import QImage, QPainter, QColor # type: ignore
from controllers.tools import erase_area
import numpy as np # type: ignore
from modes.base_mode import Mode

class ArmyMode:
    """Obsługuje tryb armii."""
    def __init__(self, mode_manager, map_controller):
        Mode.__init__(self, map_controller)
        self.map_controller = map_controller
        self.mode_manager = mode_manager
        self.army_icon = QImage("icons/army.png")
        if self.army_icon.isNull():
            raise ValueError("Nie udało się załadować ikony: icons/army.png")
        self.active_state = None

    def handle_event(self, event):
        if event.event_type == "click" and event.button == "left":
            Mode.start_snap(self, "army")
            self.add_army(event.x, event.y)
            Mode.end_snap(self, "army")
        elif event.button == "right":
            if event.event_type == "click":
                Mode.start_snap(self, "army")
            self.erase_army(event)
            if event.event_type == "release":
                Mode.end_snap(self, "army")

    def setup_menu(self):
        self.map_controller.button_panel.update_dynamic_menu([])

    def add_army(self, x, y):
        """Dodaje ikonę armii na warstwę z kolorem wybranego państwa."""
        army_layer = self.map_controller.layer_manager.get_layer("army")
        if army_layer is None:
            print("Nie można dodać jednostki armii: brak warstwy 'army'.")
            return

        # Pobierz aktywny kolor państwa z ModeManager
        active_state = self.mode_manager.get_active_state()
        if active_state is None or not hasattr(active_state, "color"):
            print("Brak aktywnego państwa lub koloru.")
            return
        state_color = active_state.color.getRgb()[:3]  # Pobierz RGB

        # Przekształć ikonę armii
        recolored_icon = self.recolor_icon(self.army_icon.copy(), state_color)

        # Rysowanie ikony armii
        painter = QPainter(army_layer)
        painter.drawImage(x - recolored_icon.width() // 2, y - recolored_icon.height() // 2, recolored_icon)
        painter.end()

        # Odświeżenie warstwy
        self.map_controller.layer_manager.refresh_layer("army")

    def erase_army(self, event):
        """Obsługuje zdarzenia związane z usuwaniem (prawy przycisk myszy)."""
        if event.event_type in {"click", "move"}:
            radius = 20  # Promień gumki
            x, y = event.x, event.y
            erase_area(self.map_controller.layer_manager, "army", x, y, radius)
            if event.event_type == "click":
                self.map_controller.snapshot_manager.end_snap("army")
        elif event.event_type == "release":
            pass

    def recolor_icon(self, image, target_color):
        if isinstance(target_color, tuple):
            target_color = QColor(*target_color)

        # Konwersja do formatu ARGB32 dla manipulacji pikselami
        image = image.convertToFormat(QImage.Format_ARGB32)
        for y in range(image.height()):
            for x in range(image.width()):
                pixel_color = QColor(image.pixel(x, y))  # Użycie poprawnego wywołania z x, y
                if pixel_color == QColor(255, 255, 255):  # Jeśli piksel jest biały
                    image.setPixel(x, y, target_color.rgb())  # Ustaw kolor docelowy
        return image
