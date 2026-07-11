import os
import zipfile
from controllers.csv_serializer import CSVSerializer

class ArchiveManager:
    def __init__(self, map_controller):
        self.map_controller = map_controller

    def save_to_zip(self, output_zip_path):
        """
        Eksportuje cv_image, warstwy, dane mapy (MapData) oraz CSV ze stanami jako ZIP bez kompresji.
        """
        temp_dir = "temp_export"
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Zapisz obrazy PNG za pomocą MapController
            self.map_controller.save_layers_to_png(temp_dir)

            # Zapisz CSV stanów za pomocą StateController
            states_csv_path = os.path.join(temp_dir, "states_metadata.csv")
            self.map_controller.state_controller.save_to_csv(states_csv_path)

            # Zapisz CSV z danymi mapy (MapData)
            data_csv_path = os.path.join(temp_dir, "data_metadata.csv")
            CSVSerializer.save_map_data(self.map_controller.map_data, data_csv_path)

            # Spakuj wszystkie pliki do ZIP bez kompresji
            with zipfile.ZipFile(output_zip_path, "w", compression=zipfile.ZIP_STORED) as zipf:
                for file_name in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file_name)
                    zipf.write(file_path, arcname=file_name)
            print(f"Dane spakowane do {output_zip_path}")

        finally:
            self._cleanup_temp_dir(temp_dir)

    def load_from_zip(self, input_zip_path):
        """
        Importuje dane z pliku ZIP i przywraca je do stanu aplikacji.
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
                    if layer_name in self.map_controller.layer_manager.layers:
                        print(f"Warstwa '{layer_name}' już istnieje. Nadpisywanie...")
                    self.map_controller.load_layer_from_png(layer_name, layer_path)

            # Przywróć stany z CSV
            states_csv_path = os.path.join(temp_dir, "states_metadata.csv")
            if os.path.exists(states_csv_path):
                self.map_controller.state_controller.load_from_csv(states_csv_path)
                print(f"Stany załadowane z {states_csv_path}")

            # Przywróć dane z MapData
            data_csv_path = os.path.join(temp_dir, "data_metadata.csv")
            if os.path.exists(data_csv_path):
                CSVSerializer.load_map_data(self.map_controller.map_data, data_csv_path)
                print(f"Dane MapData załadowane z {data_csv_path}")

            # Odśwież scenę
            self.map_controller.update_scene()

        finally:
            self._cleanup_temp_dir(temp_dir)
            self.map_controller.init_modes()

        print("Dane zostały pomyślnie przywrócone.")

    def _cleanup_temp_dir(self, directory):
        """Usuwa katalog tymczasowy."""
        if os.path.exists(directory):
            for file_name in os.listdir(directory):
                os.remove(os.path.join(directory, file_name))
            os.rmdir(directory)
