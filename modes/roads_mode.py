from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QPainterPath
from PyQt5.QtWidgets import QGraphicsPathItem
import copy
import numpy as np
from controllers.tools import Tools
import copy
from modes.base_mode import Mode
class RoadsMode:
    """Obsługuje tryb rysowania dróg z podglądem na żywo."""

    def __init__(self, mode_manager, map_controller,):
        Mode.__init__(self, map_controller)
        self.map_controller = map_controller
        self.path = QPainterPath()  # Aktualna ścieżka rysowania
        self.preview_item = None  # Podgląd rysowania w czasie rzeczywistym
        self.last_position = None  # Ostatnia znana pozycja myszy

    def handle_event(self, event):
        """Obsługuje zdarzenia myszy."""
        if event.event_type =="click":
            Mode.start_snap(self, "roads")
        if event.button == "left":
            self._rysuj(event)
        elif event.button == "right":
            self._zmazuj(event)
        if event.event_type =="release":
            Mode.end_snap(self, "roads")

    def setup_menu(self):
        self.map_controller.button_panel.update_dynamic_menu([])


    def _zmazuj(self, event):
        """Obsługuje zdarzenia związane z usuwaniem (prawy przycisk myszy)."""
        if event.event_type in {"click", "move"}:
            radius = 10  # Promień gumki
            Tools.erase_area(self.map_controller, self.map_controller.layer_manager, "roads", event.x, event.y, radius)

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
            if roads_layer is None:
                print("Brak warstwy 'roads' do rysowania.")
                return
            height, width, _ = roads_layer.shape
            bytes_per_line = 4 * width
            layer_image = QImage(roads_layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)

            painter = QPainter(layer_image)
            pen = QPen(QColor(128, 128, 128, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawPath(self.path)
            painter.end()

            layer_data = layer_image.bits().asstring(bytes_per_line * height)
            self.map_controller.layer_manager.layers["roads"] = np.frombuffer(layer_data, dtype=np.uint8).reshape(height, width, 4)

            # Odświeżenie warstwy
            self.map_controller.layer_manager.refresh_layer("roads")

            # Usunięcie podglądu
            self.last_position = None
            if self.preview_item:
                self.map_controller.scene.removeItem(self.preview_item)
                self.preview_item = None
