from PyQt5.QtGui import QImage, QColor # type: ignore
from controllers.tools import erase_area, draw_icon
from modes.base_mode import Mode

class ArmyMode(Mode):
    """Obsługuje tryb armii."""
    def __init__(self, mode_manager, map_controller):
        super().__init__(map_controller)
        self.mode_manager = mode_manager
        self.army_icon = QImage("icons/army.png")
        if self.army_icon.isNull():
            raise ValueError("Nie udało się załadować ikony: icons/army.png")
        self.active_state = None

    def handle_event(self, event):
        if event.event_type == "click":
            self.start_snap("army")
        if event.event_type == "click" and event.button == "left":
            self.add_army(event.x, event.y)
        elif event.button == "right":
            self.erase_army(event)
        if event.event_type == "release":
            self.end_snap("army")

    def add_army(self, x, y):
        """Dodaje ikonę armii na warstwę z kolorem wybranego państwa."""
        army_layer = self.map_controller.layer_manager.get_layer("army")

        # Pobierz aktywny kolor państwa z ModeManager
        active_state = self.mode_manager.get_active_state()
        if active_state is None or not hasattr(active_state, "color"):
            print("Brak aktywnego państwa lub koloru.")
            return
        state_color = active_state.color.getRgb()[:3]  # Pobierz RGB

        # Przekształć ikonę armii
        recolored_icon = self.recolor_icon(self.army_icon.copy(), state_color)

        army_layer = draw_icon(army_layer, recolored_icon, x, y)
        self.map_controller.layer_manager.refresh_layer("army")

    def erase_army(self, event):
        """Obsługuje zdarzenia związane z usuwaniem (prawy przycisk myszy)."""
        army_layer = self.map_controller.layer_manager.get_layer("army")
        radius = 20  # Promień gumki
        army_layer = erase_area(army_layer, event.x, event.y, radius)
        self.map_controller.layer_manager.refresh_layer("army")


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
