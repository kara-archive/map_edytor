from PyQt5.QtCore import pyqtSignal, Qt # type: ignore
from PyQt5.QtWidgets import QGraphicsView # type: ignore # type: ignore
from PyQt5.QtGui import QWheelEvent # type: ignore
class MapEvent:
    """Uniwersalny obiekt zdarzenia mapy."""
    def __init__(self, event_type, x, y, button=None, delta=None):
        self.event_type = event_type  # Typ zdarzenia (np. "click", "drag", "hold", "release")
        self.x = x  # Pozycja X
        self.y = y  # Pozycja Y
        self.button = button  # Przycisk myszy (opcjonalne)
        self.delta = delta  # Przesunięcie myszy (opcjonalne)
    def __repr__(self):
        return f"MapEvent(type={self.event_type}, x={self.x}, y={self.y}, button={self.button}, delta={self.delta})"

class MapView(QGraphicsView):
    """Widok mapy z uniwersalnym sygnałem zdarzeń."""
    event_occurred = pyqtSignal(MapEvent)  # Uniwersalny sygnał

    def __init__(self, map_controller, scene, state_controller):
        super().__init__(scene)
        self.map_controller = map_controller
        self.state_controller = state_controller
        self.setDragMode(QGraphicsView.NoDrag)
        self.last_mouse_pos = None
        self.ctrl_pressed = False  # To track Ctrl key state
        self.min_zoom = 0.25  # Minimum zoom level
        self.max_zoom = 10.0  # Maximum zoom level
        self.zoom_factor = 1.10
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing)
        self.setSceneRect(scene.itemsBoundingRect())


    def updateSceneRect(self):
        self.setSceneRect(self.scene().itemsBoundingRect())

    def mousePressEvent(self, event):
        if not self.ctrl_pressed:  # Do not emit events in drag mode
            scene_pos = self.mapToScene(event.pos())
            x, y = int(scene_pos.x()), int(scene_pos.y())
            button = "left" if event.button() == Qt.LeftButton else "right" if event.button() == Qt.RightButton else None
            self.event_occurred.emit(MapEvent("click", x, y, button))  # Emit event
        super().mousePressEvent(event)



    def mouseMoveEvent(self, event):
        """Obsługuje ruch myszy i emituje zdarzenia MapEvent."""
        if not self.ctrl_pressed:  # Do not emit events in drag mode
            scene_pos = self.mapToScene(event.pos())
            x, y = int(scene_pos.x()), int(scene_pos.y())

            # Oblicz delta
            if self.last_mouse_pos:
                delta_qpoint = event.pos() - self.last_mouse_pos
                delta = (delta_qpoint.x(), delta_qpoint.y())
            else:
                delta = None

            # Ustal button w zależności od wciśniętego przycisku
            if event.buttons() & Qt.LeftButton:
                button = "left"
            elif event.buttons() & Qt.RightButton:
                button = "right"
            else:
                button = None

            # Emit event
            self.event_occurred.emit(MapEvent("move", x, y, button=button, delta=delta))
            self.last_mouse_pos = event.pos()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if not self.ctrl_pressed:  # Do not emit events in drag mode
            scene_pos = self.mapToScene(event.pos())
            x, y = int(scene_pos.x()), int(scene_pos.y())
            button = "left" if event.button() == Qt.LeftButton else "right" if event.button() == Qt.RightButton else None
            self.event_occurred.emit(MapEvent("release", x, y, button))
            self.last_mouse_pos = None
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        zoom_in = event.angleDelta().y() > 0
        current_scale = self.transform().m11()

        if zoom_in and current_scale < self.max_zoom:
            scale_factor = self.zoom_factor
        elif not zoom_in and current_scale > self.min_zoom:
            scale_factor = 1 / self.zoom_factor
        else:
            return

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scale(scale_factor, scale_factor)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)

        # Aktualizuj granice sceny, aby pasowały do widoku
        self.updateSceneRect()


    def keyPressEvent(self, event):
        """Enable drag mode on Ctrl press."""
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = True
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Disable drag mode on Ctrl release."""
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = False
            self.setDragMode(QGraphicsView.NoDrag)
        super().keyReleaseEvent(event)
