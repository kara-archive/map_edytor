from modes.base_mode import Mode
from PyQt5.QtWidgets import QPushButton

class NewMode(Mode):
    def __init__(self, mode_manager, map_controller):
        self.name = "new"
        super().__init__(map_controller)
        self.mode_manager = mode_manager
        self.register_mode(z=4, label="Nowy", short="n")



    def handle_event(self, event):
        if event.event_type == 'click':
            print(event)
        elif event.event_type == 'release':
            print(event)


    def setup_menu(self):
        try:
            button = QPushButton('Przycisk')
            self.map_controller.button_panel.update_dynamic_menu([button])
        except NameError:
            print('Nowy Tryb: brak QPushButton')
