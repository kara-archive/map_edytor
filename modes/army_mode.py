from PyQt5.QtGui import QImage, QColor, QPixmap, QIcon # type: ignore
from PyQt5.QtWidgets import QPushButton, QButtonGroup # type: ignore
from PyQt5.QtCore import QSize
from controllers.tools import erase_area, draw_icon
from modes.base_mode import Mode
import os

class ArmyMode(Mode):
    """Obsługuje tryb armii."""
    def __init__(self, mode_manager, map_controller):
        super().__init__(map_controller)
        self.mode_manager = mode_manager
        self.army_icons = self.load_army_icons("icons")
        self.active_icon = self.army_icons["army"]
        self.active_icon_name = "army"

        if self.active_icon.isNull():
            raise ValueError("Nie udało się załadować ikony: icons/a_army.png")
        self.active_state = None
 
    def load_army_icons(self, folder):
        """Ładuje ikony budynków z folderu."""
        building_icons = {}
        for filename in os.listdir(folder):
            if "a_" in filename and filename.endswith(".png"):
                icon_name = filename.split("a_")[1][:-4]  # Usuwa wszystko przed "a_" i ".png" z końca
                icon_path = os.path.join(folder, filename)
                building_icons[icon_name] = QImage(icon_path)
        return building_icons
    
    def get_icon_from_image(self, image):
        pixmap = QPixmap.fromImage(image)
        return QIcon(pixmap)
        
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
        active_state = self.active_state
        if active_state is None or not hasattr(active_state, "color"):
            print("Brak aktywnego państwa lub koloru.")
            return
        state_color = active_state.color.getRgb()[:3]  # Pobierz RGB

        # Przekształć ikonę armii
        recolored_icon = self.recolor_icon(self.active_icon.copy(), state_color)

        army_layer = draw_icon(army_layer, recolored_icon, x, y)
        self.map_controller.layer_manager.refresh_layer("army")

    def erase_army(self, event):
        """Obsługuje zdarzenia związane z usuwaniem (prawy przycisk myszy)."""
        army_layer = self.map_controller.layer_manager.get_layer("army")
        radius = 10  # Promień gumki
        army_layer = erase_area(army_layer, event.x, event.y, radius)
        self.map_controller.layer_manager.refresh_layer("army")


    def recolor_icon(self, image, target_color):
        if isinstance(target_color, tuple):
            target_color = QColor(*target_color)

        # Rozjaśnij kolor docelowy
        lighter_color = target_color.lighter(150)  # 120% jasności oryginalnego koloru

        # Konwersja do formatu ARGB32 dla manipulacji pikselami
        image = image.convertToFormat(QImage.Format_ARGB32)
        for y in range(image.height()):
            for x in range(image.width()):
                pixel_color = QColor(image.pixel(x, y))  # Użycie poprawnego wywołania z x, y
                if pixel_color == QColor(255, 255, 255):  # Jeśli piksel jest biały
                    image.setPixel(x, y, lighter_color.rgb())  # Ustaw jaśniejszy kolor docelowy
        return image

    def setup_menu(self):

        # Tworzenie QButtonGroup
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)  # Tylko jeden przycisk może być zaznaczony w danym momencie

        buttons = []

        for icon_name, icon in self.army_icons.items():
            button = QPushButton()
            button.setIcon(self.get_icon_from_image(icon))  # Konwertuj QImage na QIcon
            button.setIconSize(QSize(40, 40))  # Rozmiar ikony wewnątrz przycisku
            button.setFixedSize(40, 40)  # Przyciski są kwadratowe
            button.setCheckable(True)
            button.clicked.connect(lambda _, name=icon_name: self.set_icon_type(name))
            self.button_group.addButton(button)
            buttons.append(button)
            if button.icon().name() == self.active_icon_name:
                button.setChecked(True)
                
        # Aktualizacja dynamicznego menu
        self.map_controller.button_panel.update_dynamic_menu(buttons)

        # Ustawienie pierwszego przycisku jako domyślnie zaznaczonego


    def set_icon_type(self, icon_type):
        if icon_type in self.army_icons:
            self.active_icon = self.army_icons[icon_type]  # Ustaw ikonę z mapy
            self.active_icon_name = icon_type
        else:
            raise ValueError(f"Nieznany typ ikony: {icon_type}")