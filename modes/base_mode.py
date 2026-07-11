from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap # type: ignore

class Mode(QObject):
    """
    Klasa bazowa dla trybów zarządzania mapą.
    """
    request_menu_update = pyqtSignal(list)

    def __init__(self, map_controller):
        super().__init__()
        self.map_controller = map_controller
        self.layer_manager = map_controller.layer_manager
        self.snapshot_manager = map_controller.snapshot_manager
        self.active_state = None
        self.z_value = 0
        self.short = None
        self.label = None

    def register_mode(self, z, short=None, label=None):
        self.z_value = z
        self.short = short
        self.label = label
        # Odrzucamy wywołania do map_controller, to ModeManager się tym zajmie

    def handle_event(self, event):
        raise NotImplementedError

    def start_snap(self, name):
        self.snapshot_manager.start_snap(name)

    def end_snap(self, name):
        self.snapshot_manager.end_snap(name)

    def setup_menu(self):
        self.request_menu_update.emit([])

    def get_icon_from_image(self, image):
        pixmap = QPixmap.fromImage(image)
        return QIcon(pixmap)
