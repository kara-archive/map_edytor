import copy
from PyQt5.QtGui import QImage

class SnapshotManager:
    """Zarządza snapshotami delta stanu aplikacji."""

    def __init__(self, map_controller, max_snapshots=20):
        self.map_controller = map_controller
        self.history = []  # Lista delta snapshotów
        self.future = []  # Lista przyszłych snapshotów dla redo
        self.max_snapshots = max_snapshots
        self.before_layer = None

    def create_snapshot(self, changes):
        delta_snapshot = {
            "layers": changes.get("layers", {}),
        }
        self.history.append(delta_snapshot)
        self.future.clear()  # Po stworzeniu nowego snapshotu czyścimy przyszłą historię
        if len(self.history) > self.max_snapshots:
            self.history.pop(0)  # Usuwamy najstarszy snapshot, aby utrzymać limit

    def undo(self):
        if not self.history:
            print("Brak snapshotów do cofnięcia.")
            return
        last_snapshot = self.history.pop()
        self.future.append(last_snapshot)
        self._apply_delta(last_snapshot, undo=True)


    def redo(self):
        if not self.future:
            print("Brak snapshotów do przywrócenia.")
            return
        next_snapshot = self.future.pop()
        self.history.append(next_snapshot)
        self._apply_delta(next_snapshot, undo=False)

    def _apply_delta(self, delta_snapshot, undo):
        layers_delta = delta_snapshot["layers"]
        for layer_name, layer_data in layers_delta.items():
            self.map_controller.layer_manager.layers[layer_name] = layer_data["before"] if undo else layer_data["after"]
            self.map_controller.layer_manager.refresh_layer(layer_name)
            self.map_controller.mode_manager.update_snap(layer_name)



    def start_snap(self, layer):
        self.before_layer = self._copy_layer(self.map_controller.layer_manager.get_layer(layer))

    def end_snap(self, layer):
        after_layer = self._copy_layer(self.map_controller.layer_manager.get_layer(layer))

        self.create_snapshot({
            "layers": {
                layer: {
                    "before": self.before_layer,
                    "after": after_layer
                }
            }
        })

    def _copy_layer(self, layer):
        if isinstance(layer, QImage):
            return layer.copy()
        return copy.deepcopy(layer)
