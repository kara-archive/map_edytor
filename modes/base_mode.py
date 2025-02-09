from PyQt5.QtGui import QIcon, QPixmap # type: ignore

class Mode:
    """
    Klasa bazowa dla trybów zarządzania mapą.
    """
    def __init__(self, map_controller):
        self.map_controller = map_controller
        self.layer_manager = map_controller.layer_manager
        self.snapshot_manager = map_controller.snapshot_manager
        self.active_state = None

    def register_mode(self, z, label=None):
        self.mode_manager.modes.update({self.name: self})
        self.map_controller.layer_manager.Z_VALUES.update({self.name: z})
        if label:
            self.map_controller.buttons_info.append((label, self.name))


    def handle_event(self, event):
        raise NotImplementedError

    def start_snap(self, name):
        self.snapshot_manager.start_snap(name)


    def end_snap(self, name):
        self.snapshot_manager.end_snap(name)

    def setup_menu(self):
        self.map_controller.button_panel.update_dynamic_menu([])

    def get_icon_from_image(self, image):
        pixmap = QPixmap.fromImage(image)
        return QIcon(pixmap)
