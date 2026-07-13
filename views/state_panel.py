from PyQt5.QtWidgets import QWidget, QSpinBox, QVBoxLayout, QLabel, QPushButton, QScrollArea, QDialog, QLineEdit, QColorDialog, QHBoxLayout, QSizePolicy, QShortcut, QButtonGroup  # type: ignore
from PyQt5.QtGui import QColor, QKeySequence, QIntValidator # type: ignore
from PyQt5.QtCore import QSize, pyqtSignal # type: ignore
from controllers.state_controller import State
from PyQt5.QtCore import QTimer, Qt # type: ignore

class StatePanel(QWidget):
    """Panel zarządzający państwami."""
    active_state_changed = pyqtSignal(object)

    def __init__(self, controller):
        super().__init__()
        self.active_state = None
        self.controller = controller
        self.init_ui()
        self.initialize_shortcuts()  # Inicjalizacja skrótów klawiszowych
        self.update_states()
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)  # Tylko jeden przycisk może być zaznaczony w danym momencie

    def init_ui(self):
        """Inicjalizuje interfejs użytkownika."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.title = QLabel("Państwa")
        layout.addWidget(self.title)

        # Przycisk do dodawania państwa
        self.add_button = QPushButton("Dodaj państwo")
        self.add_button.clicked.connect(self.add_new_state)
        layout.addWidget(self.add_button)

        # Obszar przewijania
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        self.setMaximumWidth(800)

        # Timer do odświeżania widoku co sekundę
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_states)
        self.timer.start(2000)

        # Pierwsze wywołanie aktualizacji
        self.update_states()

    def update_states(self):
        """Aktualizuje widok listy państw."""
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        for state in self.controller.get_states():
            self.add_state_widget(state)

    def add_state_widget(self, state):
            """Dodaje widget reprezentujący jedno państwo."""
            # Kontener dla elementu
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(3, 3, 3, 3)

            # Górna linijka: Kolor + przycisk + Poziom (lvl)
            top_layout = QHBoxLayout()
            
            color_label = QPushButton()
            color_label.setFixedSize(QSize(40, 40))
            color_label.setStyleSheet(f"background-color: {state.color}; border: 1px solid black;")
            
            button = QPushButton(state.name)
            button.setCheckable(True)
            button.setMaximumWidth(600)

            # --- LVL ---
            lvl_spinbox = QSpinBox()
            lvl_spinbox.setRange(0, 100)  # Zmień zakres minimum i maksimum wg potrzeb
            lvl_spinbox.setValue(state.lvl) # Ustawienie początkowej wartości
            lvl_spinbox.setMaximumWidth(80)
            lvl_spinbox.setToolTip("LvL")

            inv_spinbox = QSpinBox()
            inv_spinbox.setRange(0, 100)  # Zmień zakres minimum i maksimum wg potrzeb
            inv_spinbox.setValue(state.inv_bonus) # Ustawienie początkowej wartości
            inv_spinbox.setMaximumWidth(80)
            inv_spinbox.setToolTip("Handel")

            # Funkcja lambda automatycznie zaktualizuje atrybut state.lvl w obiekcie
            lvl_spinbox.valueChanged.connect(lambda value, s=state: setattr(s, 'lvl', value))
            inv_spinbox.valueChanged.connect(lambda value, s=state: setattr(s, 'inv_bonus', value))
            # --------------------------------------------

            # Sprawdź, czy to ostatnio wybrane państwo
            if state == self.active_state:
                button.setChecked(True)
                button.setStyleSheet("font-weight: bold;")  # Ustaw pogrubioną czcionkę

            button.clicked.connect(lambda _, s=state: self.set_active_state(state))
            color_label.clicked.connect(lambda _, s=state: self.edit_state(state))
            
            top_layout.addWidget(color_label)
            top_layout.addWidget(button)
            top_layout.addWidget(lvl_spinbox) # Dodanie spinboxa do górnego układu
            top_layout.addWidget(inv_spinbox) # Dodanie spinboxa do górnego układu

            # Dodanie przycisku do QButtonGroup
            self.button_group.addButton(button)

            bottom_label = self.assemble_attribute_widgets(state)         
  
            container_layout.addLayout(top_layout)
            container_layout.addWidget(bottom_label)

            # Dodanie do układu przewijanej listy
            self.scroll_layout.addWidget(container)

    def set_active_state(self, state):
            self.active_state = state
            self.active_state_changed.emit(state)
            self.update_states()

    def edit_state(self, state):
        """Edytuje istniejące państwo."""
        dialog = AddStateDialog(self, state)
        if dialog.exec_() == QDialog.Accepted:
            new_name, new_color, new_lvl = dialog.get_state()
            if new_name and new_color:
                state.name = new_name
                state.color = new_color.name()
                state.lvl = new_lvl
                self.controller.recalculate_all_stats()
                self.update_states()
                self.set_active_state(state)

    def add_new_state(self):
        dialog = AddStateDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name, color, lvl = dialog.get_state()  # Pobranie nazwy, koloru i lvl z dialogu
            if name and color:
                new_state = State(name, color.name(), self.controller)  # Tworzenie obiektu State
                new_state.lvl = lvl
                self.controller.add_state(new_state)
                self.update_states()

    def initialize_shortcuts(self):
        """Inicjalizuje skróty klawiszowe na podstawie `self.shortcuts`."""
        self.next_state_shortcut = QShortcut(QKeySequence("Tab"), self)
        self.next_state_shortcut.activated.connect(self.select_next_state)

    def select_next_state(self):
        """Przełącza na kolejne państwo."""
        states = self.controller.get_states()
        if not states:
            return

        if self.active_state is None:
            self.set_active_state(states[0])
        else:
            current_index = states.index(self.active_state)
            next_index = (current_index + 1) % len(states)
            self.set_active_state(states[next_index])

    def assemble_attribute_widgets(self, state):
            """Tworzy listę interaktywnych widgetów z tooltipami na podstawie strukturalnych danych."""
            from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
            
            # 1. Pobranie danych strukturalnych (lista krotek) z modelu
            attributes_data = state.get_dynamic_attributes()
            
            if not attributes_data:
                return QLabel("Brak dynamicznych atrybutów do wyświetlenia.")

            # Tworzenie głównego kontenera i układu (Layout)
            container_widget = QWidget()
            h_layout = QHBoxLayout(container_widget)
            
            # Usunięcie marginesów wokół layoutu, by widget nie był zbyt szeroki
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(5) # Odstęp między etykietami
            
            for display_html, attr_name in attributes_data:
                # 2. Tworzenie widgetu dla każdego segmentu
                attribute_label = QLabel()
                
                # Przypisujemy gotowy kod HTML (inicjał + wartość w kolorach)
                attribute_label.setText(display_html) 
                
                # 3. Ustawienie Tooltipa - teraz wyświetla SAMĄ nazwę atrybutu
                attribute_label.setToolTip(attr_name) 
                
                # Twoje ostylowanie - dodanie ramki i zaokrąglenia
                attribute_label.setStyleSheet("""
                    QLabel {
                        padding: 0px 0px; 
                        border: 0px solid #444; 
                        border-radius: 5px;
                        background-color: #fff; 
                    }
                """)
                
                h_layout.addWidget(attribute_label)

            # Dodanie elastycznego odstępu na końcu, by etykiety były dociśnięte do lewej strony
            h_layout.addStretch()

            # Zwrot głównego, złożonego widżetu GUI
            return container_widget

class AddStateDialog(QDialog):
    """Okno dialogowe do dodawania/edytowania państwa."""
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.setWindowTitle("Dodaj/Edytuj państwo")

        layout = QVBoxLayout(self)

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Nazwa państwa")
        layout.addWidget(self.name_input)

        self.lvl_input = QLineEdit(self)
        self.lvl_input.setPlaceholderText("Poziom (LvL)")
        self.lvl_input.setValidator(QIntValidator(0, 99999, self))
        self.lvl_input.setText("0")
        layout.addWidget(self.lvl_input)

        self.color_button = QPushButton("Wybierz kolor", self)
        self.color_button.clicked.connect(self.choose_color)
        layout.addWidget(self.color_button)

        self.submit_button = QPushButton("Zapisz", self)
        self.submit_button.clicked.connect(self.accept)
        layout.addWidget(self.submit_button)

        self.selected_color = QColor("#FFFFFF")

        # Jeśli edytujemy istniejące państwo
        if state:
            self.name_input.setText(state.name)
            self.selected_color = QColor(state.color)
            self.color_button.setStyleSheet(f"background-color: {self.selected_color.name()};")
            self.lvl_input.setText(str(getattr(state, 'lvl', 0)))
            self.setWindowTitle(f"Edytuj państwo: {state.name}")

    def choose_color(self):
        # Tworzenie instancji QColorDialog
        color_dialog = QColorDialog()

        custom_colors = []

        for j in range(5):
            for i in range(3):
                hue = int(i * 120 + j * 24)  # 22.590 degrees apart
                color = QColor()
                color.setHsv(hue, 230, 128)  # Saturation 230, Value 128
                custom_colors.append(color)

        for i, color in enumerate(custom_colors):
            color_dialog.setCustomColor(i, color)

        # Wyświetlenie dialogu
        color = color_dialog.getColor()

        if color.isValid():
            self.selected_color = color
            self.color_button.setStyleSheet(f"background-color: {color.name()};")

    def get_state(self):
        name = self.name_input.text()
        lvl = int(self.lvl_input.text() or 0)
        if name:
            return name, self.selected_color, lvl
        return None, None, 0
