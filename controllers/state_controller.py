from PyQt5.QtCore import QObject, pyqtSignal # type: ignore
from PyQt5.QtGui import QImage, QColor, QPainter, QFont, QFontMetrics # type: ignore
import csv, os

class StateController(QObject):
    """Handles the list of states and stores the last selected state."""
    state_changed = pyqtSignal()  # New signal to notify when states change

    def __init__(self, map_controller):
        super().__init__()
        self.states = []
        self.last_state = None
        self.map_controller = map_controller
        self.label_colors = ["burlywood",]

    def get_states(self):
        return self.states

    def get_states_colors(self):
        colors = []
        for state in self.states:
            colors.append(state.color)
        return colors

    def get_states_names(self):
        names = []
        for state in self.states:
            names.append(state.name)
        return names

    def emit_state_change_signal(self):
        """Emit a signal to notify that states have changed (for UI updates)."""
        self.state_changed.emit()


    def add_state(self, state):
        if state not in self.states:
            self.states.append(state)
            self.map_controller.init_modes()
            self.recalculate_all_stats()
        else:
            print(f"State {state.name} already exists.")

    def save_to_csv(self, file_path):
        """Zapisuje aktualny stan państw do pliku CSV."""
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["name", "color", "province_count", "lvl"])  # Nagłówki kolumn
            for state in self.states:
                writer.writerow([state.name, state.color, state.provinces, getattr(state, 'lvl', 0)])  # Zapis danych
        print(f"Stany zapisane do pliku: {file_path}")

    def export_to_csv(self, obecna_tura, file_path="dane.csv"):
        """
        Zapisuje dane do pliku CSV, nadpisując pierwszą linię nagłówkami.
        """
        if not self.states:
            print("Nie można zapisać stanu: brak danych o państwach.")
            return

        # Przygotowanie nagłówków i danych
        all_attributes = set()
        for state in self.states:
            all_attributes.update(attr for attr in state.__dict__.keys() if attr not in {"color", "state_controller", "name"})
        headers = ["Tura " + str(obecna_tura)] + [
            "LvL" if attr.lower() == "lvl" else attr.capitalize()
            for attr in all_attributes
        ]

        rows = []

        for state in self.states:
            if "NPC" not in state.name:
                state_data = [getattr(state, attr, "") for attr in all_attributes]
                rows.append([state.name] + state_data)

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Zapisz nagłówki
                writer.writerow(headers)

                # Dopisz nowy wiersz dla obecnej tury
                for row in rows:
                    writer.writerow(row)

            print(f"Dane dla tury {obecna_tura} zapisane do pliku: {file_path}")

        except Exception as e:
            print(f"Błąd podczas zapisywania pliku CSV: {e}")

    def render_table_image(self, obecna_tura):
            """
            Renderuje tabelę z danymi państw jako QImage.
            Kolumny: Nazwa + wszystkie dynamiczne atrybuty (z pominięciem color, state_controller, name).
            Wiersze: tylko państwa bez 'NPC' w nazwie.
            """
            if not self.states:
                return None

            # Zbierz atrybuty i dane (tak samo jak w export_to_csv)
            all_attributes = []
            for state in self.states:
                for attr in state.__dict__.keys():
                    if attr not in {"color", "state_controller", "name"} and attr not in all_attributes:
                        all_attributes.append(attr)

            # --- PATCH: Słownik tłumaczeń atrybutów na język polski ---
            attribute_translations = {
                "town": "Miasta",
                "rancho": "Wsie",
                "provinces": "Prowincje",
                "plant": "Manufaktury",
                "Capital": "Stolica",
                "army": "Armia",
                "fort": "Forty",
                "ship": "Okręty",
                "investments": "Inw.",
                "food": "Żywność",
                # Miejsce na Twoje kolejne atrybuty (np. "gold": "Złoto")
            }
            # ----------------------------------------------------------

            headers = [f"Tura {obecna_tura}"] + [
                "LvL" if attr.lower() == "lvl" else attribute_translations.get(attr.lower(), attr.capitalize())
                for attr in all_attributes
            ]

            rows = []
            row_colors = []
            for state in self.states:
                if "NPC" not in state.name:
                    state_data = [str(getattr(state, attr, "")) for attr in all_attributes]
                    rows.append([state.name] + state_data)
                    row_colors.append(state.color)  # hex string

            if not rows:
                return None

            # Parametry rysowania
            font = QFont("Sans", 11)
            font.setBold(False)
            header_font = QFont("Sans", 11, QFont.Bold)
            fm = QFontMetrics(font)
            hfm = QFontMetrics(header_font)

            padding_x = 12
            padding_y = 8
            row_height = max(fm.height(), hfm.height()) + padding_y * 2

            # Oblicz szerokość każdej kolumny
            col_widths = []
            for col_idx in range(len(headers)):
                max_w = hfm.horizontalAdvance(headers[col_idx])
                for row in rows:
                    if col_idx < len(row):
                        w = fm.horizontalAdvance(row[col_idx])
                        max_w = max(max_w, w)
                col_widths.append(max_w + padding_x * 2)

            table_width = sum(col_widths)
            table_height = row_height * (1 + len(rows))  # nagłówek + dane

            # Tworzenie obrazu
            image = QImage(table_width, table_height, QImage.Format_RGBA8888)
            image.fill(QColor(30, 30, 30, 255))  # ciemne tło

            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing)

            # Rysuj nagłówek
            painter.setFont(header_font)
            x = 0
            for col_idx, header in enumerate(headers):
                painter.fillRect(x, 0, col_widths[col_idx], row_height, QColor(50, 50, 50, 255))
                painter.setPen(QColor(220, 220, 220))
                painter.drawText(x + padding_x, 0, col_widths[col_idx] - padding_x, row_height,
                                0x0080 | 0x0004, header)  # AlignVCenter | AlignLeft
                x += col_widths[col_idx]

            # Rysuj wiersze
            painter.setFont(font)
            for row_idx, row in enumerate(rows):
                y = (row_idx + 1) * row_height
                state_color = QColor(row_colors[row_idx])

                # Tło wiersza — lekki pasek koloru państwa
                bg = QColor(state_color)
                bg.setAlpha(50)
                painter.fillRect(0, y, table_width, row_height, bg)

                x = 0
                for col_idx, cell in enumerate(row):
                    # Pierwsza kolumna (nazwa) — kolor państwa jako tekst
                    if col_idx == 0:
                        painter.setPen(state_color)
                    else:
                        painter.setPen(QColor(200, 200, 200))
                    painter.drawText(x + padding_x, y, col_widths[col_idx] - padding_x, row_height,
                                    0x0080 | 0x0004, cell)
                    x += col_widths[col_idx]

                # Linia oddzielająca
                painter.setPen(QColor(60, 60, 60))
                painter.drawLine(0, y, table_width, y)

            # Ramka zewnętrzna
            painter.setPen(QColor(80, 80, 80))
            painter.drawRect(0, 0, table_width - 1, table_height - 1)

            painter.end()
            return image


    def get_food_provinces_count(self):
        """Zwraca słownik {nazwa_państwa: liczba_prowincji_produkujących_żywność}."""
        states = self.get_states()
        counts = {state.name: 0 for state in states}
        
        province_layer = self.map_controller.layer_manager.get_layer("province")
        if province_layer is None:
            return counts
            
        provinces_coords = self.map_controller.map_data.provinces
        for x, y in provinces_coords:
            if not (0 <= x < province_layer.width() and 0 <= y < province_layer.height()):
                continue
            color = QColor(province_layer.pixel(x, y)).getRgb()[:3]
            # Znajdź państwo
            for state in states:
                state_rgb = QColor(state.color).getRgb()[:3]
                if all(abs(int(c1) - int(c2)) <= 5 for c1, c2 in zip(color, state_rgb)):
                    # Sprawdź biom
                    biome = self.map_controller.get_biome_at(x, y)
                    if biome not in {"water", "desert"}:
                        counts[state.name] += 1
                    break
        return counts

    def recalculate_all_stats(self):
        """Przelicza Food i Investments dla każdego państwa."""
        food_provinces = self.get_food_provinces_count()
        for state in self.states:
            # 1. Investments
            capital = getattr(state, "capital", 0)
            town = getattr(state, "town", 0)
            plant = getattr(state, "plant", 0)
            #(TODO) czytaj niżej
            state.investments = capital * 5 + town * 1 + plant * 1

            # 2. Food
            rancho = getattr(state, "rancho", 0)
            ship = getattr(state, "ship", 0)
            army = getattr(state, "army", 0)
            # fort is 0, so no need to subtract
            
            prov_food = food_provinces.get(state.name, 0)
            
            # Wzór: prov_food * 1 + rancho * 3 - town * 6 - capital * 6 - plant * 4 - ship * 1 - army * 1
            #(TODO) dodać łatwe konfigurację statyystyk, może być przynajmniej u góry pliku w formie stałych
            state.food = prov_food * 1 + rancho * 3 - town * 6 - capital * 6 - plant * 4 - ship * 1 - army * 1

    def load_from_csv(self, file_path):
        """Wczytuje stany z pliku CSV."""
        self.states = []  # Czyści istniejącą listę państw
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row['name']
                color = row['color']
                state = State(name, color, self)
                state.provinces = int(row.get('province_count', 0))
                state.lvl = int(row.get('lvl', 0))
                self.states.append(state)
        self.recalculate_all_stats()

class State:
    """Representuje jedno państwo w grze."""
    def __init__(self, name, color, state_controller=None):
        self.name = name
        self.color = color
        self.provinces = 0
        self.town = 0
        self.rancho = 0
        self.plant = 0
        self.capital = 0
        self.army = 0
        self.fort = 0
        self.ship = 0
        self.lvl = 0
        self.investments = 0
        self.food = 0
        self.state_controller = state_controller

    def get_building_value(self, building_type, biome):
        building_type = self._normalize_building_type(building_type)
        biome = (biome or "plain").lower()
        #(TODO) tutaj tak samo, to musi być łatwo konfigurowalne 

        if biome == "water":
            return 0
        if building_type == "town" and biome == "mountains":
            return 0
        if building_type == "rancho":
            return 0 if biome == "desert" else 3
        return 1

    def _normalize_building_type(self, building_type):
        building_type = str(building_type).lower()
        aliases = {
            "miasto": "town",
            "town": "town",
            "wies": "rancho",
            "wieś": "rancho",
            "village": "rancho",
            "rancho": "rancho",
            "plant": "plant",
            "fabryka": "plant",
            "factory": "plant",
            "farma": "rancho",
            "farm": "rancho",
            "zywnosc": "rancho",
            "żywność": "rancho",
        }
        return aliases.get(building_type, building_type)

    def get_dynamic_attributes(self):
        """Zwraca sformatowany string z nazwami atrybutów, z wyłączeniem name, color i atrybutów zawierających 'capital'."""
        attributes = []
        if self.state_controller:
            colors = self.state_controller.label_colors
        else:
            colors = ["burlywood",]
        color_index = 0

        for attr, value in self.__dict__.items():
            if attr not in {"name", "color", "label_colors", "state_controller"} and "capital" not in attr:
                color = colors[color_index % len(colors)]
                attr_initial = f'<span style="color:{color}">{attr[0].upper()}</span>'
                value_str = ''.join(f'<span style="color:{color}">{char}</span>' for char in str(value))
                attributes.append(f"{attr_initial}:{value_str}")
                color_index += 1

        return " ".join(attributes)
