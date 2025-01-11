import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QButtonGroup, QFileDialog, QShortcut, QCheckBox, QHBoxLayout, QGroupBox # type: ignore
from PyQt5.QtCore import QTimer, pyqtSignal # type: ignore
from PyQt5.QtGui import QKeySequence # type: ignore
import zipfile
from controllers.data import DATA

class ButtonPanel(QWidget):
    """Panel boczny z przyciskami do interakcji."""
    active_mode = pyqtSignal(str)  # Sygnał zmiany trybu

    def __init__(self, map_controller, map_view, state_controller, state_panel):
        super().__init__()
        self.map_controller = map_controller
        self.map_view = map_view
        self.state_controller = state_controller
        self.state_panel = state_panel
        self.obecna_tura = None
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setMaximumWidth(150)  # Ustawienie maksymalnej szerokości

        # Tworzenie grupy przycisków
        group_box = QGroupBox("Opcje")
        group_layout = QVBoxLayout()

        # Tworzenie QButtonGroup
        button_group = QButtonGroup(self)
        button_group.setExclusive(True)  # Tylko jeden przycisk może być zaznaczony w danym momencie

        # Definicja przycisków i checkboxów
        buttons_info = [
            ("Wojsko", "army"),
            ("Budynki", "buildings"),
            ("Drogi", "roads"),
            ("Prowincje", "province")
        ]

        self.buttons = {}
        for label, mode in buttons_info:
            row_layout = QHBoxLayout()
            if mode != "province":
                visibility_checkbox = QCheckBox()
                visibility_checkbox.setChecked(True)
                visibility_checkbox.stateChanged.connect(lambda state, m=mode: self.toggle_visibility(state, m))
                row_layout.addWidget(visibility_checkbox)

            button = QPushButton(label)
            button.setCheckable(True)
            button.clicked.connect(lambda _, m=mode, b=button: self.set_active_mode(m, b))
            row_layout.addWidget(button)

            group_layout.addLayout(row_layout)
            button_group.addButton(button)
            self.buttons[mode] = button

        # Ustawienie layoutu grupy
        group_box.setLayout(group_layout)

        # Dodanie grupy do głównego layoutu
        layout.addWidget(group_box)

        # Zmienna do przechowywania aktywnego trybu
        self.current_mode = None

        self.shortcuts = {"q": "army", "w": "buildings", "r": "province", "e": "roads"}
        self.initialize_shortcuts()

        # Odstęp
        layout.addStretch()
        # Sekcja dla dynamicznego menu
        # Ustawienie kontenera na dynamiczne menu
        self.dynamic_menu_container = QWidget()
        self.dynamic_menu_layout = QGridLayout()  # Ustawienie układu jako QGridLayout
        self.dynamic_menu_container.setLayout(self.dynamic_menu_layout)
        self.layout().addWidget(self.dynamic_menu_container)

        self.clear_dynamic_menu()

        layout.addStretch()


        # „Wczytaj”
        self.load_button = QPushButton("Wczytaj")
        layout.addWidget(self.load_button)
        self.load_button.clicked.connect(self.load_data)

        self.save_button = QPushButton("Zapisz")
        layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save_data)

        # Przycisk Eksportuj z licznikiem
        self.export_turn_button = QPushButton()
        layout.addWidget(self.export_turn_button)
        self.export_turn_button.clicked.connect(self.export_turn)

        # Timer do odświeżania przycisku eksportu
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_export_button)
        self.timer.start(5000)

        # Pierwsze ustawienie tekstu przycisku
        self.update_export_button()

    def clear_dynamic_menu(self):
        """Czyści dynamiczne menu."""
        while self.dynamic_menu_layout.count():
            item = self.dynamic_menu_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def update_dynamic_menu(self, widgets):
        """
        Aktualizuje dynamiczne menu w układzie siatki (QGridLayout).

        :param widgets: Lista widżetów do dodania do dynamicznego menu.
        """
        self.clear_dynamic_menu()  # Czyści dynamiczne menu

        # Dodanie widżetów do siatki
        for i, widget in enumerate(widgets):
            row, col = divmod(i, 2)  # Rozmieszczenie w siatce: 3 kolumny
            self.dynamic_menu_layout.addWidget(widget, row, col)

    def toggle_visibility(self, state, layer_name):
        """
        Przełącza widoczność warstwy w zależności od stanu przycisku.

        :param state: True, jeśli warstwa ma być widoczna; False, jeśli ma być ukryta.
        :param layer_name: Nazwa warstwy, której widoczność zmieniamy.
        """
        try:
            self.map_controller.layer_manager.set_visibility(layer_name, state)
            print(f"Warstwa '{layer_name}' widoczność ustawiona na: {state}.")
        except ValueError as e:
             print(f"Błąd: {e}")
 
    def set_active_mode(self, mode, button):
        """Ustawia aktywny tryb i wyróżnia odpowiedni przycisk."""
        self.current_mode = mode
        self.active_mode.emit(mode)  # Emituje sygnał, aby zmienić tryb
        button.setChecked(True)

    def initialize_shortcuts(self):
        """Inicjalizuje skróty klawiszowe na podstawie `self.shortcuts`."""
        for key, mode in self.shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)  # Przypisanie skrótu do widżetu
            shortcut.activated.connect(lambda m=mode: self.set_active_mode(m, self.buttons[m]))

    def get_last_turn(self):
        """Zwraca numer ostatniej zapisanej tury."""
        try:
            tury = [f for f in os.listdir("Tury") if f.endswith(".png")]
            tury.sort()
            if not tury:
                return -1
            ostatnia_tura = tury[-1]
            return int(ostatnia_tura.split(".")[0])
        except Exception as e:
            return -1

    def update_export_button(self):
        """Aktualizuje tekst przycisku eksportu tury."""
        self.obecna_tura = self.get_last_turn() + 1
        self.export_turn_button.setText(f"Eksport {self.obecna_tura} Tury")

    def load_states(self):
        """Wczytuje stany z pliku CSV."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Wczytaj Państwa", "", "")
        if file_path:
            self.state_controller.load_from_csv(file_path)
            # Wywołaj metodę aktualizacji widoku
            self.map_view.scene().update()
            if hasattr(self.map_view, 'state_panel'):
                self.map_view.state_panel.update_states()

    def export_turn(self):
        """Eksportuje turę: zapisuje obraz mapy i plik CSV z danymi stanu."""
        obecna_tura = self.get_last_turn() + 1  # Pobierz aktualny numer tury

        # Ścieżki do zapisania
        export_path = f"Tury/{obecna_tura}.Tura"
        self.map_controller.export_image(f"Tury/{obecna_tura}.Tura"+".png")
        self.state_controller.export_to_csv(obecna_tura,"Tury/prowincje"+".csv")

    def save_data(self):
        """
        Wywołuje okno dialogowe do wyboru lokalizacji pliku ZIP i zapisuje dane.
        """
        file_path, _ = QFileDialog.getSaveFileName(self, "Zapisz dane", "", "ZIP Files (*.zip)")
        if file_path:
            if not file_path.endswith(".zip"):
                file_path += ".zip"  # Dodaj rozszerzenie, jeśli użytkownik go nie podał
            try:
                self.save(file_path)
                print(f"Pomyślnie zapisano dane do {file_path}.")
            except Exception as e:
                print(f"Błąd podczas zapisywania danych: {e}")

    def save(self, output_zip_path):
        """
        Eksportuje cv_image, warstwy, dane z DATA oraz CSV ze stanami jako ZIP bez kompresji.
        :param output_zip_path: Ścieżka do pliku ZIP.
        """
        temp_dir = "temp_export"
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Zapisz obrazy PNG za pomocą MapController
            self.map_controller.save_layers_to_png(temp_dir)

            # Zapisz CSV stanów za pomocą StateController
            states_csv_path = os.path.join(temp_dir, "states_metadata.csv")
            self.state_controller.save_to_csv(states_csv_path)

            # Zapisz CSV z DATA
            data_csv_path = os.path.join(temp_dir, "data_metadata.csv")
            DATA.save(data_csv_path)  # Bezpośrednie wywołanie istniejącej funkcji

            # Spakuj wszystkie pliki do ZIP bez kompresji
            with zipfile.ZipFile(output_zip_path, "w", compression=zipfile.ZIP_STORED) as zipf:
                for file_name in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file_name)
                    zipf.write(file_path, arcname=file_name)  # Dodaj pliki z relatywną ścieżką
            print(f"Dane spakowane do {output_zip_path}")

        finally:
            # Usuń tymczasowy katalog
            for file_name in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file_name))
            os.rmdir(temp_dir)

    def load_data(self):
        """
        Wywołuje okno dialogowe do wyboru pliku ZIP i ładuje dane.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Wczytaj dane", "", "")
        if file_path:
            try:
                self.load(file_path)
                print(f"Pomyślnie wczytano dane z {file_path}.")
            except Exception as e:
                print(f"Błąd podczas wczytywania danych: {e}")

    def load(self, input_zip_path):
        """
        Importuje dane z pliku ZIP i przywraca je do stanu aplikacji.
        :param input_zip_path: Ścieżka do pliku ZIP.
        """
        temp_dir = "temp_import"
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Rozpakuj ZIP do katalogu tymczasowego
            with zipfile.ZipFile(input_zip_path, "r") as zipf:
                zipf.extractall(temp_dir)
            print(f"Dane rozpakowane z {input_zip_path}")

            # Przywróć cv_image (bazowy obraz)
            base_image_path = os.path.join(temp_dir, "base_image.png")
            if os.path.exists(base_image_path):
                self.map_controller.load_map(base_image_path)
                print(f"Obraz bazowy załadowany z {base_image_path}")

            # Przywróć warstwy
            for file_name in os.listdir(temp_dir):
                if file_name.endswith(".png") and file_name != "base_image.png":
                    layer_name = os.path.splitext(file_name)[0]
                    layer_path = os.path.join(temp_dir, file_name)
                    # Sprawdź, czy warstwa już istnieje, i nadpisz ją
                    if layer_name in self.map_controller.layer_manager.layers:
                        print(f"Warstwa '{layer_name}' już istnieje. Nadpisywanie...")
                    self.map_controller.load_layer_from_png(layer_name, layer_path)

            # Przywróć stany z CSV
            states_csv_path = os.path.join(temp_dir, "states_metadata.csv")
            if os.path.exists(states_csv_path):
                self.state_controller.load_from_csv(states_csv_path)
                print(f"Stany załadowane z {states_csv_path}")

            # Przywróć dane z DATA
            data_csv_path = os.path.join(temp_dir, "data_metadata.csv")
            if os.path.exists(data_csv_path):
                DATA.load(data_csv_path)  # Wywołanie funkcji z DATA
                print(f"Dane DATA załadowane z {data_csv_path}")

            # Odśwież scenę
            self.map_controller.update_scene()
            self.map_view.scene().update()

        finally:
            # Usuń tymczasowy katalog
            for file_name in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file_name))
            os.rmdir(temp_dir)
            self.map_controller.init_modes()
            self.state_panel.update_states()

        print("Dane zostały pomyślnie przywrócone.")
