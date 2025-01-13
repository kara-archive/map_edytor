from PyQt5.QtGui import QColor # type: ignore
from PyQt5.QtCore import QObject, pyqtSignal # type: ignore
import csv, os

class StateController(QObject):
    """Handles the list of states and stores the last selected state."""
    state_changed = pyqtSignal()  # New signal to notify when states change

    def __init__(self, map_controller):
        super().__init__()
        self.states = []
        self.last_state = None
        self.map_controller = map_controller

    def get_states(self):
        return self.states

    def emit_state_change_signal(self):
        """Emit a signal to notify that states have changed (for UI updates)."""
        self.state_changed.emit()


    def add_state(self, state):
        if state not in self.states:
            self.states.append(state)
        else:
            print(f"State {state.name} already exists.")

    def save_to_csv(self, file_path):
        """Zapisuje aktualny stan państw do pliku CSV."""
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["name", "color", "province_count"])  # Nagłówki kolumn
            for state in self.states:
                writer.writerow([state.name, state.color.name(), state.provinces])  # Zapis danych
        print(f"Stany zapisane do pliku: {file_path}")

    def export_to_csv(self, obecna_tura, file_path="prowincje.csv"):
        """
        Zapisuje dane do pliku CSV, nadpisując pierwszą linię nagłówkami.
        """
        if not self.states:
            print("Nie można zapisać stanu: brak danych o państwach.")
            return

        # Przygotowanie nagłówków i danych
        headers = ["tura"] + [state.name for state in self.states]
        row = [obecna_tura] + [state.provinces for state in self.states]

        try:
        # Odczyt istniejącego pliku, jeśli istnieje
            existing_rows = []
            if os.path.isfile(file_path):
                with open(file_path, mode='r', newline='', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    existing_rows = list(reader)

            # Nadpisanie pierwszej linii nagłówkami
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Zapisz nagłówki
                writer.writerow(headers)

                # Dopisz istniejące dane, pomijając starą linię nagłówków
                for row_data in existing_rows[1:]:
                    writer.writerow(row_data)

                # Dopisz nowy wiersz dla obecnej tury
                writer.writerow(row)

            print(f"Dane dla tury {obecna_tura} zapisane do pliku: {file_path}")

        except Exception as e:
            print(f"Błąd podczas zapisywania pliku CSV: {e}")


    def load_from_csv(self, file_path):
        """Wczytuje stany z pliku CSV."""
        self.states = []  # Czyści istniejącą listę państw
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row['name']
                color = row['color']
                self.states.append(State(name, color))



class State:
    """Reprezentuje jedno państwo w grze."""
    def __init__(self, name, color):
        self.name = name
        self.color = QColor(color)
        self.provinces = 0

    def get_dynamic_attributes(self):
        """Zwraca sformatowany string z nazwami atrybutów, z wyłączeniem name, color i provinces."""
        attributes = []
        colors = ["green", "purple", "blue", "lime", "red", "brown", "pink", "cyan"]
        color_index = 0

        for attr, value in self.__dict__.items():
            if attr not in {"name", "color", "capital"}:
                color = colors[color_index % len(colors)]
                attr_initial = f'<span style="color:{color}">{attr[0].upper()}</span>'
                value_str = ''.join(f'<span style="color:{color}">{char}</span>' for char in str(value))
                attributes.append(f"{attr_initial}: {value_str}")
                color_index += 1

        return " ".join(attributes)
