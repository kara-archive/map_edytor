from controllers.map_controller.layer_manager import LayerManager
import copy
from controllers.data import DATA

class SnapshotManager:
    """Zarządza snapshotami delta stanu aplikacji."""

    def __init__(self, map_controller, max_snapshots=10):
        self.map_controller = map_controller
        self.history = []  # Lista delta snapshotów
        self.future = []  # Lista przyszłych snapshotów dla redo
        self.max_snapshots = max_snapshots
        self.before_data = None

    def create_snapshot(self, changes):
        """
        Tworzy snapshot delta, który zapisuje zmiany i pełną kopię danych.
        :param changes: Słownik zmian (np. zmiana warstw).
        """
        delta_snapshot = {
            "layers": changes.get("layers", {}),
            "data": changes.get("data", {}),  # Kopia stanu DATA
        }
        self.history.append(delta_snapshot)
        self.future.clear()  # Po stworzeniu nowego snapshotu czyścimy przyszłą historię
        if len(self.history) > self.max_snapshots:
            self.history.pop(0)  # Usuwamy najstarszy snapshot, aby utrzymać limit

    def undo(self):
        """Cofa ostatnie zmiany, przywracając poprzedni snapshot delta."""
        if not self.history:
            print("Brak snapshotów do cofnięcia.")
            return

        last_snapshot = self.history.pop()
        self.future.append(last_snapshot)
        self._apply_delta(last_snapshot, undo=True)

    def redo(self):
        print("Redoing last snapshot...")
        """Przywraca cofnięty snapshot, jeśli istnieje."""
        if not self.future:
            print("Brak snapshotów do przywrócenia.")
            return

        next_snapshot = self.future.pop()
        self.history.append(next_snapshot)
        self._apply_delta(next_snapshot, undo=False)

    def _apply_delta(self, delta_snapshot, undo):
        print(f"Applying delta, undo: {undo}")
        restored_data = delta_snapshot["data"]
        restored = restored_data["before"] if undo else restored_data["after"]
        #print(f"Restoring DATA: {restored.buildings.cities}")

        # Odtwórz dane
        #DATA.buildings.cities = copy.deepcopy(restored.buildings.cities)
        #DATA.army = copy.deepcopy(restored.army)
        #DATA.provinces = copy.deepcopy(restored.provinces)

        # Przywróć warstwy
        layers_delta = delta_snapshot["layers"]
        for layer_name, layer_data in layers_delta.items():
            self.map_controller.layer_manager.layers[layer_name] = layer_data["before"] if undo else layer_data["after"]
            self.map_controller.layer_manager.refresh_layer(layer_name)
        print(f"DATA after restore: {DATA.buildings.cities}")


    def start_snap(self, layer):
        """Rozpoczyna proces tworzenia snapshotu."""
        self.before_layer = copy.deepcopy(self.map_controller.layer_manager.get_layer(layer))
        self.before_data = copy.deepcopy(DATA.buildings)  # Tworzenie pełnej kopii DATA
        #print("start_snap before_data:", str(self.before_data.buildings.cities))
        print("Snapshot start: Kopia przed zmianami zapisana.")

    def end_snap(self, layer):
        """Kończy proces tworzenia snapshotu."""
        after_layer = copy.deepcopy(self.map_controller.layer_manager.get_layer(layer))
        after_data = copy.deepcopy(DATA.buildings)
        #print("end_snap before_data:", str(self.before_data.buildings.cities))  # Powinno równać się start_snap before_data
        #print("end_snap after_data:", str(after_data.buildings.cities))        # Powinno zawierać zmiany
        self.create_snapshot({
            "layers": {
                layer: {
                    "before": self.before_layer,
                    "after": after_layer
                }
            },
            "data": {
                "before": self.before_data,
                "after": after_data
            }
        })
        print("Snapshot end: Kopia po zmianach zapisana.")
