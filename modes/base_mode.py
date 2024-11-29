class Mode:
    """
    Klasa bazowa dla trybów zarządzania mapą.
    """
    def __init__(self, map_controller, name, z_value):
        self.name = name
        self.z_value = z_value
        self.map_controller = map_controller
        self.layer_manager = map_controller.layer_manager
        self.mode_manager = map_controller.mode_manager
        self.initialize_layer(self.map_controller.cv_image, self.map_controller.scene, z_value)

    def initialize_layer(self, cv_image, scene, z_value):
        """
        Inicjalizuje warstwę specyficzną dla tego trybu.
        """
        height, width, _ = map_controller.cv_image.shape
        self.layer_manager.add_layer(self.name, width, height, self.z_value, scene)
        print(f"Zainicjalizowano warstwę '{self.name}' z Z_VALUE: {self.z_value}")

    def handle_event(self, event):
        """
        Obsługuje zdarzenia. Wymagane do zaimplementowania w podklasach.
        """
        raise NotImplementedError

    def start_snapshot(self):
        """
        Tworzy stan warstwy przed rozpoczęciem operacji.
        """
        layer = self.layer_manager.get_layer(self.name)
        if layer is None:
            print(f"Błąd: warstwa '{self.name}' nie istnieje.")
            return None
        return copy.deepcopy(layer)

    def end_snapshot(self, before_layer):
        """
        Tworzy stan warstwy po zakończeniu operacji i zapisuje snapshot.
        """
        after_layer = copy.deepcopy(self.layer_manager.get_layer(self.name))
        self.map_controller.snapshot_manager.create_snapshot({
            "layers": {
                self.name: {
                    "before": before_layer,
                    "after": after_layer
                }
            }
        })
        print(f"Snapshot utworzony dla trybu '{self.name}'.")
