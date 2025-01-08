class Mode:
    """
    Klasa bazowa dla trybów zarządzania mapą.
    """
    def __init__(self, map_controller):
        self.map_controller = map_controller
        self.layer_manager = map_controller.layer_manager
        self.snapshot_manager = map_controller.snapshot_manager
                
    def handle_event(self, event):

        raise NotImplementedError

    def start_snap(self, name):
            self.snapshot_manager.start_snap(name)


    def end_snap(self, name):
            self.snapshot_manager.end_snap(name)

    def setup_menu(self):
        self.map_controller.button_panel.update_dynamic_menu([])