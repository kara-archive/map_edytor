from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor
from PyQt5.QtWidgets import QGraphicsPathItem
from controllers.tools import erase_area
from .base_mode import Mode

class RoadsMode(Mode):
    """Obsługuje tryb rysowania dróg z podglądem na żywo."""

    def __init__(self, mode_manager, map_controller):
        super().__init__(map_controller)
        self.map_controller = map_controller
        self.path = None
        self.preview_item = None

    def handle_event(self, event):
        """Obsługuje zdarzenia myszy."""
        if event.event_type == "click":
            Mode.start_snap(self, "roads")
        if event.button == "right":
            self._zmazuj(event)
        elif event.button == "left":
            self._rysuj(event)
        if event.event_type == "release":
            Mode.end_snap(self, "roads")

    def setup_menu(self):
        self.map_controller.button_panel.update_dynamic_menu([])

    def _zmazuj(self, event):
        """Obsługuje zdarzenia związane z usuwaniem (prawy przycisk myszy)."""
        if event.event_type in {"click", "move"}:
            radius = 15  # Promień gumki
            erase_area(self.map_controller.layer_manager, "roads", event.x, event.y, radius)

    def _rysuj(self, event):
        """Obsługuje zdarzenia związane z rysowaniem (lewy przycisk myszy)."""
        if event.event_type == "click":
            self.path = QPainterPath()
            self.path.moveTo(event.x, event.y)
            self.last_position = (event.x, event.y)

            if self.preview_item is None:
                self.preview_item = QGraphicsPathItem()
                self.preview_item.setPen(QPen(QColor(128, 128, 128, 255), 2))
                self.map_controller.scene.addItem(self.preview_item)
            self.preview_item.setPath(self.path)

        elif event.event_type == "move" and self.last_position is not None:
            self.path.lineTo(event.x, event.y)
            self.preview_item.setPath(self.path)

        elif event.event_type == "release":
            roads_layer = self.map_controller.layer_manager.get_layer("roads")
            painter = QPainter(roads_layer)
            pen = QPen(QColor(128, 128, 128, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawPath(self.path)
            painter.end()

            # Odświeżenie warstwy
            self.map_controller.layer_manager.refresh_layer("roads")

            # Usunięcie podglądu
            self.last_position = None
            if self.preview_item:
                self.map_controller.scene.removeItem(self.preview_item)
                self.preview_item = None
