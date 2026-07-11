import csv

class CSVSerializer:
    """Klasa odpowiedzialna za odczyt i zapis danych z MapData do formatu CSV."""
    
    @staticmethod
    def save_map_data(map_data, file_path):
        """
        Zapisuje dane z obiektu MapData do pliku CSV.
        :param map_data: Obiekt MapData.
        :param file_path: Ścieżka do pliku.
        """
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Zapis prowincji
                writer.writerow(["Provinces"])
                for x, y in map_data.provinces:
                    writer.writerow([x, y])

                # Zapis budynków
                writer.writerow(["Buildings:Cities"])
                for x, y in map_data.buildings.cities:
                    writer.writerow([x, y])

                writer.writerow(["Buildings:Towns"])
                for x, y in map_data.buildings.towns:
                    writer.writerow([x, y])

                writer.writerow(["Buildings:Farms"])
                for x, y in map_data.buildings.farms:
                    writer.writerow([x, y])

                # Zapis armii
                writer.writerow(["Army:Units"])
                for x, y in map_data.army.units:
                    writer.writerow([x, y])

            print(f"Dane zapisane do pliku {file_path}.")
        except Exception as e:
            print(f"Błąd podczas zapisu do pliku: {e}")

    @staticmethod
    def load_map_data(map_data, file_path):
        """
        Wczytuje dane z pliku CSV do obiektu MapData.
        :param map_data: Obiekt MapData (do zmodyfikowania).
        :param file_path: Ścieżka do pliku.
        """
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                section = None

                # Czyszczenie istniejących danych
                map_data.provinces.clear()
                map_data.buildings.cities.clear()
                map_data.buildings.towns.clear()
                map_data.buildings.farms.clear()
                map_data.army.units.clear()

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
                        map_data.provinces.append((x, y))
                    elif section == "Buildings:Cities":
                        map_data.buildings.cities.append((x, y))
                    elif section == "Buildings:Towns":
                        map_data.buildings.towns.append((x, y))
                    elif section == "Buildings:Farms":
                        map_data.buildings.farms.append((x, y))
                    elif section == "Army:Units":
                        map_data.army.units.append((x, y))

            print(f"Dane wczytane z pliku {file_path}.")
        except Exception as e:
            print(f"Błąd podczas wczytywania pliku: {e}")
