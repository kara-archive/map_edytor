import csv
import copy

class DATA(object):
    """Hierarchical database storing coordinates of different types of objects."""
    def __init__(self):
        self.buildings = DATA.Buildings()
        self.army = DATA.Army()
        self.provinces = DATA.Provinces()
        self.province_mode = None  # Add province_mode to DATA for easier restoration

    def __deepcopy__(self, memo):
        copied_data = DATA()
        copied_data.buildings = copy.deepcopy(self.buildings, memo)
        copied_data.army = copy.deepcopy(self.army, memo)
        copied_data.provinces = copy.deepcopy(self.provinces, memo)
        copied_data.province_mode = copy.deepcopy(self.province_mode, memo)
        return copied_data

    class Buildings:
        """Przechowuje różne typy budynków."""
        def __init__(self):
            self.cities = []
            self.towns = []
            self.farms = []

    class Army:
        """Przechowuje współrzędne jednostek wojskowych."""
        def __init__(self):
            self.units = []

    class Provinces(list):
        """Przechowuje współrzędne prowincji."""
        def __init__(self, *args):
            super().__init__(*args)
            self.extend([])

    # Główne kategorie danych
    buildings = Buildings()
    army = Army()
    provinces = Provinces()

    @staticmethod
    def save(file_path):
        """
        Zapisuje dane do pliku CSV.
        :param file_path: Ścieżka do pliku.
        """
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Zapis prowincji
                writer.writerow(["Provinces"])
                for x, y in DATA.provinces:
                    writer.writerow([x, y])

                # Zapis budynków
                writer.writerow(["Buildings:Cities"])
                for x, y in DATA.buildings.cities:
                    writer.writerow([x, y])

                writer.writerow(["Buildings:Towns"])
                for x, y in DATA.buildings.towns:
                    writer.writerow([x, y])

                writer.writerow(["Buildings:Farms"])
                for x, y in DATA.buildings.farms:
                    writer.writerow([x, y])

                # Zapis armii
                writer.writerow(["Army:Units"])
                for x, y in DATA.army.units:
                    writer.writerow([x, y])

            print(f"Dane zapisane do pliku {file_path}.")
        except Exception as e:
            print(f"Błąd podczas zapisu do pliku: {e}")

    @staticmethod
    def load(file_path):
        """
        Wczytuje dane z pliku CSV.
        :param file_path: Ścieżka do pliku.
        """
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                section = None

                # Czyszczenie istniejących danych
                DATA.provinces.clear()
                DATA.buildings.cities.clear()
                DATA.buildings.towns.clear()
                DATA.buildings.farms.clear()
                DATA.army.units.clear()

                for row in reader:
                    if not row:
                        continue

                    # Rozpoznanie sekcji
                    if row[0] in ["Provinces", "Buildings:Cities", "Buildings:Towns", "Buildings:Farms", "Army:Units"]:
                        section = row[0]
                        continue

                    # Parsowanie współrzędnych
                    x, y = map(int, row)
                    if section == "Provinces":
                        DATA.provinces.append((x, y))
                    elif section == "Buildings:Cities":
                        DATA.buildings.cities.append((x, y))
                    elif section == "Buildings:Towns":
                        DATA.buildings.towns.append((x, y))
                    elif section == "Buildings:Farms":
                        DATA.buildings.farms.append((x, y))
                    elif section == "Army:Units":
                        DATA.army.units.append((x, y))

            print(f"Dane wczytane z pliku {file_path}.")
        except Exception as e:
            print(f"Błąd podczas wczytywania pliku: {e}")
