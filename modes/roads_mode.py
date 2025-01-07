from controllers.tools import erase_area, DrawPath
from .base_mode import Mode

class RoadsMode(Mode):
    """Obsługuje tryb rysowania dróg z podglądem na żywo."""

    def __init__(self, mode_manager, map_controller):
        super().__init__(map_controller)
        self.mode_manager = mode_manager
        self.path = None
        self.preview_item = None

    def handle_event(self, event):
        """Obsługuje zdarzenia myszy."""
        if event.event_type == "click":
            self.start_snap("roads")
        if event.button == "right" and event.event_type in {"click", "move"}:
            self._zmazuj(event)
        elif event.button == "left":
            self._rysuj(event)
        if event.event_type == "release":
            self.end_snap("roads")


    def _zmazuj(self, event):
        """Obsługuje zdarzenia związane z usuwaniem (prawy przycisk myszy)."""
        roads_layer = self.layer_manager.get_layer("roads")
        radius = 15  # Promień gumki
        erase_area(roads_layer, event.x, event.y, radius)
        self.layer_manager.refresh_layer("roads")


    # Usage in RoadsMode
    def _rysuj(self, event):
        """Obsługuje zdarzenia związane z rysowaniem (lewy przycisk myszy)."""
        if not hasattr(self, 'draw_path'):
            self.draw_path = DrawPath(self.layer_manager.get_layer("roads"))

        if event.event_type == "click":
            self.draw_path.start_path(event.x, event.y, self.map_controller.scene)
            self.last_position = (event.x, event.y)

        elif event.event_type == "move" and self.last_position is not None:
            self.draw_path.update_path(event.x, event.y)

        elif event.event_type == "release":
            self.draw_path.end_path(self.map_controller.scene)
            self.layer_manager.refresh_layer("roads")
            self.last_position = None
