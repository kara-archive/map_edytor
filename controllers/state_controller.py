from PyQt5.QtGui import QColor
from PyQt5.QtCore import QObject, pyqtSignal
import csv, os
from controllers.data import DATA
from controllers.tools import PixelSampler

from PyQt5.QtCore import pyqtSignal

class StateController(QObject):
    """Handles the list of states and stores the last selected state."""
    state_changed = pyqtSignal()  # New signal to notify when states change

    def __init__(self, map_controller):
        super().__init__()
        self.states = []
        self.last_state = None
        self.map_controller = map_controller
        self.provinces = DATA.provinces

    def get_states(self):
        return self.states

    def emit_state_change_signal(self):
        """Emit a signal to notify that states have changed (for UI updates)."""
        self.state_changed.emit()


    def add_state(self, state):
        self.states.append(state)

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
    def __init__(self, name, color, provinces=None):
        self.name = name
        self.color = QColor(color)
        self.provinces = 0
        self.cities = 0  # Liczba miast
        self.farms = 0
