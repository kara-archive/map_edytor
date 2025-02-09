from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QGraphicsScene, QShortcut # type: ignore
from PyQt5.QtGui import QKeySequence # type: ignore
from views.state_panel import StatePanel
from views.map_view import MapView
from views.button_panel import ButtonPanel
from controllers.state_controller import StateController
from controllers.map_controller.map_controller import MapController
class MainView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Map Editor")

        # Controllers
        self.map_controller = MapController()
        self.state_controller = StateController(self.map_controller)

        # Link controllers to ensure consistency
        self.map_controller.state_controller = self.state_controller

        # Connect the state changed signal
        self.state_controller.state_changed.connect(self.update_state_view)

        self._setup_shortcuts()
        self.init_ui()
        self.setup_signals()

    def update_state_view(self):
        """Update the state panel to reflect any changes in states."""
        if hasattr(self, 'state_panel'):
            self.state_panel.update_states()


    def init_ui(self):
        """Inicjalizuje interfejs użytkownika."""
        self.scene = QGraphicsScene()
        self.map_view = MapView(self.map_controller, self.scene, self.state_controller)
        self.map_controller.set_scene(self.map_view.scene())# Ustaw scenę w kontrolerze mapy

        # Inicjalizacja UI
        self.state_panel = StatePanel(self.state_controller)
        self.button_panel = ButtonPanel(self.map_controller, self.map_view, self.state_controller, self.state_panel)
        
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.state_panel)
        main_layout.addWidget(self.map_view)
        main_layout.addWidget(self.button_panel)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Ładowanie domyślnej mapy
        self.map_controller.button_panel = self.button_panel
#        self.map_controller.load_map("Tury/0.Tura.png")

    def setup_signals(self):
        """Podłącza sygnały między komponentami."""
        self.map_view.event_occurred.connect(self.handle_event_occurred)
        self.button_panel.active_mode.connect(self.handle_active_mode)
        self.state_panel.active_state_changed.connect(self.handle_active_state)

    def handle_event_occurred(self, event):
        """Obsługuje zdarzenie z MapView."""
        self.map_controller.mode_manager.handle_event(event)

    def handle_active_mode(self, mode):
        """Obsługuje zmianę aktywnego trybu."""
        self.map_controller.mode_manager.set_mode(mode)

    def handle_active_state(self, state):
        """Obsługuje zmianę aktywnego stanu."""
        self.map_controller.mode_manager.update_active_state(state)

    def _setup_shortcuts(self):
        """Rejestruje skróty klawiszowe."""
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        undo_shortcut.activated.connect(self._undo_action)
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        redo_shortcut.activated.connect(self._redo_action)

    def _undo_action(self):
        """Obsługuje cofanie zmian."""
        self.map_controller.snapshot_manager.undo()

    def _redo_action(self):
        """Obsługuje cofanie zmian."""
        self.map_controller.snapshot_manager.redo()
