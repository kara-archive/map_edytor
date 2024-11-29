from controllers.map_controller.layer_manager import LayerManager

class SnapshotManager:
    """Zarządza snapshotami delta stanu aplikacji."""

    def __init__(self, map_controller, max_snapshots=10):
        self.map_controller = map_controller
        self.history = []  # Lista delta snapshotów
        self.future = []  # Lista przyszłych snapshotów dla redo
        self.max_snapshots = max_snapshots

    def create_snapshot(self, changes):
        """
        Tworzy snapshot delta, który zapisuje tylko zmiany.
        :param changes: Słownik zmian (np. zmiana warstw).
        """
        delta_snapshot = {
            "layers": changes.get("layers", {})
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
        print(f"Delta snapshot: {delta_snapshot}")

        # Przywróć warstwy
        layers_delta = delta_snapshot["layers"]
        for layer_name, layer_data in layers_delta.items():
            if undo:
                self.map_controller.layer_manager.layers[layer_name] = layer_data["before"]
            else:
                self.map_controller.layer_manager.layers[layer_name] = layer_data["after"]
            self.map_controller.layer_manager.refresh_layer(layer_name)
