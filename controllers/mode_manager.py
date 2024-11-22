from PyQt5.QtCore import QObject

class ModeManager(QObject):
    """Zarządza aktywnym trybem i deleguje zdarzenia do aktywnego modu."""

    def __init__(self, map_controller,):
        super().__init__()
        self.map_controller = map_controller
        self.layer_manager = self.map_controller.layer_manager
        self.snapshot_manager = self.map_controller.snapshot_manager
        # Inicjalizacja trybów
        self.buildings_mode = BuildingsMode(self, map_controller)
        self.province_mode = ProvinceMode(self, map_controller)
        self.army_mode = ArmyMode(self, map_controller)
        self.roads_mode = RoadsMode(self, map_controller)
        self.active_state = None
        self.active_mode = None
        self.active_mode_name = None
        self.modes = {
            "buildings": self.buildings_mode,
            "province": self.province_mode,
            "army": self.army_mode,
            "roads": self.roads_mode,
        }

    def set_mode(self, mode_name=None):
        """Ustawia aktywny tryb."""
        self.active_mode = self.modes.get(mode_name)
        self.active_mode_name = mode_name

    def get_mode(self):
        return self.active_mode_name

    def handle_event(self, event):
        """Przekazuje zdarzenie do aktywnego trybu."""
        if self.active_mode:
            self.active_mode.handle_event(event)

    def update_active_state(self, state):
        """Aktualizuje aktywny stan w trybie prowincji."""
        if state is None:
            print("ProvinceMode: Ustawiony stan jest None!")
        else:
            self.active_state = state

    def get_active_state(self,):
        return self.active_state

    class Mode:
        """
        Klasa bazowa dla trybów zarządzania mapą.
        """
        def __init__(self, map_controller, name, z_value=0):
            self.name = name
            self.z_value = z_value
            self.map_controller = map_controller
            self.layer_manager = map_controller.layer_manager

        def initialize_layer(self, cv_image, scene):
            """
            Inicjalizuje warstwę specyficzną dla tego trybu.
            """
            height, width, _ = cv_image.shape
            self.layer_manager.add_layer(self.name, width, height, self.z_value, scene)
            print(f"Zainicjalizowano warstwę '{self.name}' z Z_VALUE: {self.z_value}")

        def handle_event(self, event):
            """
            Obsługuje zdarzenia. Wymagane do zaimplementowania w podklasach.
            """
            raise NotImplementedError

        def activate(self):
            """Wywoływana przy aktywacji trybu."""
            print(f"Tryb '{self.name}' aktywowany.")

        def deactivate(self):
            """Wywoływana przy dezaktywacji trybu."""
            print(f"Tryb '{self.name}' dezaktywowany.")


class BuildingsMode:
    """Obsługuje tryb budynków."""
    MAX_RECENT_OPERATIONS = 5  # Limit zapisanych operacji

    def __init__(self, mode_manager, map_controller):
        self.snap = False
        self.map_controller = map_controller
        self.building_positions = {}  # Pozycje budynków
        self.building_icon = QImage("icons/city.png")
        self.before_layer = None

        if self.building_icon.isNull():
            raise ValueError("Nie udało się załadować ikony budynku: icons/city.png")

    def handle_event(self, event):
        if event.event_type == "click":
            self.before_layer = copy.deepcopy(self.map_controller.layer_manager.get_layer("buildings"))
        if event.event_type == "click" and event.button == "left":
            self.add_building(event.x, event.y)
            self.count_cities_by_state()

        elif event.event_type in {"move", "click"} and event.button == "right":
            self.erase_building(event)
            self.count_cities_by_state()

        elif event.event_type == "release":
            after_layer = copy.deepcopy(self.map_controller.layer_manager.get_layer("buildings"))
            self.do_snap(self.before_layer, after_layer)

    def add_building(self, x, y):
        print(f"Adding building at: ({x}, {y})")
        """Dodaje budynek do warstwy i zapisuje operację."""
        self.building_positions[(x, y)] = "city"
        building_layer = self.map_controller.layer_manager.get_layer("buildings")
        if building_layer is None:
            print("Nie można znaleźć warstwy 'buildings'.")
            return
        self._draw_icon(building_layer, x, y)
        self.add_building_position(x, y)

    def do_snap(self, before, after):
        self.map_controller.snapshot_manager.create_snapshot({
            "layers": {
                "buildings": {
                    "before": before,
                    "after": after
                }
            }
        })

    def erase_building(self, event):
        print(f"Erasing buildings around: ({event.x}, {event.y}), radius: 20")
        """Usuwa budynki w promieniu i zapisuje operację."""
        radius = 20
        removed_positions = self.remove_building_positions(event, radius)
        Tools.erase_area(self.map_controller, self.map_controller.layer_manager, "buildings", event.x, event.y, radius)

    def _draw_icon(self, building_layer, x, y):
        """Rysuje ikonę budynku na warstwie."""
        height, width, _ = building_layer.shape
        bytes_per_line = 4 * width

        # Tworzenie obrazu warstwy
        layer_image = QImage(building_layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)
        painter = QPainter(layer_image)
        if not painter.isActive():
            print("Painter nie jest aktywny!")
            return
        painter.drawImage(x - self.building_icon.width() // 2, y - self.building_icon.height() // 2, self.building_icon)
        painter.end()

        # Aktualizacja danych warstwy
        data = layer_image.bits().asstring(bytes_per_line * height)
        self.map_controller.layer_manager.layers["buildings"] = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 4)
        self.map_controller.layer_manager.refresh_layer("buildings")

    def add_building_position(self, x, y):
        print(f"Adding building position to DATA: ({x}, {y})")
        """Dodaje pozycję budynku i zapisuje operację."""
        DATA.buildings.cities.append((x, y))
        print(f"Dodano budynek w pozycji: ({x}, {y})")

    def remove_building_positions(self, event, radius):
        print(f"Removing building positions around: ({event.x}, {event.y}), radius: {radius}")
        """
        Usuwa pozycje budynków w zadanym promieniu.
        Zwraca listę usuniętych pozycji.
        """
        x, y = event.x, event.y
        removed_positions = [
            (bx, by) for bx, by in DATA.buildings.cities
            if math.sqrt((bx - x) ** 2 + (by - y) ** 2) <= radius
        ]

        # Usuwanie budynków z bazy danych w dokładnym promieniu
        for pos in removed_positions:
            DATA.buildings.cities.remove(pos)

        print(f"Usunięto {len(removed_positions)} budynków w promieniu {radius} od punktu ({x}, {y}).")
        return removed_positions

    def restore_operation(self, type, x, y):
        print(type, x, y)

    def count_cities_by_state(self):
        """
        Próbkuje piksele w pozycjach budynków (miast) i wyświetla liczbę miast dla każdego państwa.
        """
        if self.map_controller.cv_image is None:
            print("Brak obrazu bazowego (cv_image) do próbkowania miast.")
            return

        if not DATA.buildings.cities:
            print("Brak zapisanych pozycji miast w DATA.buildings.cities.")
            return

        # Użycie PixelSampler
        pixel_sampler = PixelSampler(
            self.map_controller.layer_manager.layers.get("province"),
            DATA.buildings.cities,
            self.map_controller.state_controller.get_states()
        )
        for state in self.map_controller.state_controller.get_states():
            state.cities = pixel_sampler.get(state.name, 0)

class ProvinceMode:
    """Obsługuje tryb prowincji."""
    def __init__(self, mode_manager, map_controller):
        self.map_controller = map_controller
        self.sampled_color = None
        self.active_state = None
        self.provinces = DATA.provinces
        self.mode_manager = mode_manager
        self.layer = self.mode_manager.layer_manager.layers.get("province")

    def handle_event(self, event):
        """Obsługuje zdarzenia w trybie prowincji."""
        if self.active_state != self.mode_manager.active_state:
            self.active_state = self.mode_manager.active_state
            self.sampled_color = None
        if event.event_type == "click" and event.button == "right":
            self.sampled_color = self.get_color_at(event.x, event.y)
        elif event.event_type == "click" and event.button == "left":
            if self.sampled_color:
                fill_color = self.sampled_color
            elif self.active_state and hasattr(self.active_state, 'color'):
                fill_color = self.active_state.color.getRgb()[:3]
            else:
                print("ProvinceMode: Brak aktywnego państwa lub koloru próbki.")
                return
            self.flood_fill(event.x, event.y, fill_color)

    def flood_fill(self, x, y, color):
        """
        Flood fill dla warstwy 'province' z tworzeniem snapshotów.

        Args:
            x (int): Współrzędna X punktu startowego.
            y (int): Współrzędna Y punktu startowego.
            color (tuple): Kolor docelowy w RGB.
        """
        if color == (0, 0, 0):
            return  # Ignoruj kolor czarny jako wypełnienie
                # Utwórz snapshot przed operacją

        layer = self.mode_manager.layer_manager.get_layer("province")
        before_layer = copy.deepcopy(layer)
        if layer is None:
            print("Warstwa 'province' nie istnieje.")
            return
        updated_layer = self._fill(layer, x, y, color)
        self.mode_manager.layer_manager.layers["province"] = updated_layer
        self.mode_manager.layer_manager.refresh_layer("province")
        self.sample_provinces()
        # Utwórz snapshot po operacji
        after_layer = copy.deepcopy(self.mode_manager.layer_manager.layers["province"])
        self.map_controller.snapshot_manager.create_snapshot({
            "layers": {
                "province": {
                    "before": before_layer,
                    "after": after_layer
                }
            }
        })

    def _fill(self, layer, x, y, color):



        # Pobranie wymiarów obrazu
        height, width, channels = layer.shape
        bytes_per_line = channels * width

        # Konwersja numpy array na QImage
        image = QImage(layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)

        fill_color = (color[0], color[1], color[2])  # RGB
        start_color = QColor(image.pixel(x, y)).getRgb()[:3]
        if start_color == fill_color or start_color == (0, 0, 0):
            print("Debug: Kolor startowy i docelowy są takie same lub czarny.")
            return

        # Pobranie rozmiarów obrazu
        pixels = image.bits()
        pixels.setsize(height * width * 4)  # 4 kanały (RGBA)
        pixel_array = np.frombuffer(pixels, dtype=np.uint8).reshape((height, width, 4))

        # BFS z liniowym przetwarzaniem
        queue = [(x, y)]
        visited = set()

        while queue:
            current_x, current_y = queue.pop(0)
            if (current_x, current_y) in visited:
                continue
            visited.add((current_x, current_y))

            # Zabezpieczenie przed przekroczeniem granic
            if current_x < 0 or current_y < 0 or current_x >= width or current_y >= height:
                continue

            # Sprawdź kolor bieżącego piksela
            current_pixel = pixel_array[current_y, current_x][:3]  # Tylko RGB
            if not np.array_equal(current_pixel, start_color):
                continue

            # Wypełnij linię w prawo
            left_x, right_x = current_x, current_x
            while left_x > 0 and np.array_equal(pixel_array[current_y, left_x - 1][:3], start_color):
                left_x -= 1
            while right_x < width - 1 and np.array_equal(pixel_array[current_y, right_x + 1][:3], start_color):
                right_x += 1

            # Wypełnij linię i dodaj sąsiadów do kolejki
            for fill_x in range(left_x, right_x + 1):
                pixel_array[current_y, fill_x][:3] = fill_color  # Ustaw RGB
                if current_y > 0:  # Dodaj linię powyżej
                    queue.append((fill_x, current_y - 1))
                if current_y < height - 1:  # Dodaj linię poniżej
                    queue.append((fill_x, current_y + 1))

        # Aktualizacja obrazu
        updated_layer = np.copy(pixel_array)
        return updated_layer

    def sample_provinces(self):
        """
        Próbkuje piksele na mapie i przypisuje liczbę prowincji do odpowiednich państw.
        """
        print("Rozpoczynanie próbkowania prowincji...")
        states = self.map_controller.state_controller.get_states()
        image = self.mode_manager.layer_manager.layers.get("province")
        province_counts = PixelSampler(image, self.provinces, states)

        # Przypisanie liczby prowincji do obiektów State
        for state in states:
            state.provinces = province_counts.get(state.name, 0)
            print(f"Państwo {state.name} ma {state.provinces} prowincji")

    def get_color_at(self, x, y):
        print(f"Pobieranie koloru w punkcie ({x}, {y})")

        # Pobierz warstwę
        self.layer = self.mode_manager.layer_manager.get_layer("province")
        if self.layer is None:
            print("Warstwa 'province' nie istnieje.")
            return None

        # Upewnij się, że współrzędne są w granicach obrazu
        height, width, _ = self.layer.shape
        if not (0 <= x < width and 0 <= y < height):
            print(f"Punkt ({x}, {y}) znajduje się poza granicami obrazu.")
            return None

        # Pobierz kolor z warstwy
        self.sampled_color = tuple(self.layer[y, x][:3])  # Ignorujemy kanał alfa
        print(f"Pobrano kolor: {self.sampled_color}")
        return self.sampled_color

class ArmyMode:
    """Obsługuje tryb armii."""
    def __init__(self, mode_manager, map_controller):
        self.map_controller = map_controller
        self.mode_manager = mode_manager
        self.army_icon = QImage("icons/army.png")
        if self.army_icon.isNull():
            raise ValueError("Nie udało się załadować ikony: icons/army.png")
        self.active_state = None

    def handle_event(self, event):
        if event.event_type == "click" and event.button == "left":
            self.add_army(event.x, event.y)
        elif event.button == "right":
            self.erase_army(event)

    def add_army(self, x, y):
        """Dodaje ikonę armii na warstwę z kolorem wybranego państwa."""
        army_layer = self.map_controller.layer_manager.get_layer("army")
        if army_layer is None:
            print("Nie można dodać jednostki armii: brak warstwy 'army'.")
            return

        # Pobierz aktywny kolor państwa z ModeManager
        active_state = self.mode_manager.get_active_state()
        if active_state is None or not hasattr(active_state, "color"):
            print("Brak aktywnego państwa lub koloru.")
            return
        state_color = active_state.color.getRgb()[:3]  # Pobierz RGB

        # Przekształć ikonę armii
        recolored_icon = self.recolor_icon(self.army_icon.copy(), state_color)

        # Pobranie wymiarów obrazu warstwy
        height, width, _ = army_layer.shape
        bytes_per_line = 4 * width

        # Tworzenie obrazu warstwy na bazie istniejących danych
        layer_image = QImage(army_layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)

        # Rysowanie ikony armii
        painter = QPainter(layer_image)
        painter.drawImage(x - recolored_icon.width() // 2, y - recolored_icon.height() // 2, recolored_icon)
        painter.end()

        # Aktualizacja danych warstwy
        data = layer_image.bits().asstring(bytes_per_line * height)
        self.map_controller.layer_manager.layers["army"] = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 4)

        # Odświeżenie warstwy
        self.map_controller.layer_manager.refresh_layer("army")
        self.map_controller.snapshot_manager.create_snapshot({
            "layers": {
                "army": {
                    "before": copy.deepcopy(army_layer),
                    "after": copy.deepcopy(self.map_controller.layer_manager.layers["army"])
                }
            }
        })

    def erase_army(self, event):
        army_layer = self.map_controller.layer_manager.get_layer("army")
        """Obsługuje zdarzenia związane z usuwaniem (prawy przycisk myszy)."""
        if event.event_type in {"click", "move"}:
            radius = 10  # Promień gumki
            x, y = event.x, event.y
            Tools.erase_area(self.map_controller, self.map_controller.layer_manager, "army", x, y, radius)
            if event.event_type =="click":
                layer = self.map_controller.layer_manager.get_layer("army")
                self.map_controller.snapshot_manager.create_snapshot({
                    "layers": {
                        "army": {
                            "before": copy.deepcopy(layer),
                            "after": copy.deepcopy(self.map_controller.layer_manager.layers["army"])
                        }
                    }
                })
        elif event.event_type == "release":
            pass

    def recolor_icon(self, image, target_color):
        """
        Zmienia białe piksele w ikonie na wybrany kolor.
        :param image: QImage ikony.
        :param target_color: QColor lub (R, G, B) reprezentujący kolor wybranego państwa.
        :return: Zmieniona QImage.
        """
        if isinstance(target_color, tuple):
            target_color = QColor(*target_color)

        # Konwersja do formatu ARGB32 dla manipulacji pikselami
        image = image.convertToFormat(QImage.Format_ARGB32)
        for y in range(image.height()):
            for x in range(image.width()):
                pixel_color = QColor(image.pixel(x, y))  # Użycie poprawnego wywołania z x, y
                if pixel_color == QColor(255, 255, 255):  # Jeśli piksel jest biały
                    image.setPixel(x, y, target_color.rgb())  # Ustaw kolor docelowy
        return image

class RoadsMode:
    """Obsługuje tryb rysowania dróg z podglądem na żywo."""

    def __init__(self, mode_manager, map_controller,):
        self.map_controller = map_controller
        self.path = QPainterPath()  # Aktualna ścieżka rysowania
        self.preview_item = None  # Podgląd rysowania w czasie rzeczywistym
        self.last_position = None  # Ostatnia znana pozycja myszy

    def handle_event(self, event):
        """Obsługuje zdarzenia myszy."""
        if event.button == "left":
            self._rysuj(event)
        elif event.button == "right":
            self._zmazuj(event)
            if event.event_type =="click":
                layer = self.map_controller.layer_manager.get_layer("roads")
                self.map_controller.snapshot_manager.create_snapshot({"layers": {"roads": {"before": copy.deepcopy(layer),"after": copy.deepcopy(self.map_controller.layer_manager.layers["roads"])}}})

    def _zmazuj(self, event):
        """Obsługuje zdarzenia związane z usuwaniem (prawy przycisk myszy)."""
        if event.event_type in {"click", "move"}:
            radius = 10  # Promień gumki
            Tools.erase_area(self.map_controller, self.map_controller.layer_manager, "roads", event.x, event.y, radius)

    def _rysuj(self, event):
        """Obsługuje zdarzenia związane z rysowaniem (lewy przycisk myszy)."""
        if event.event_type == "click":
            self.path = QPainterPath()
            self.path.moveTo(event.x, event.y)
            self.last_position = (event.x, event.y)

            if self.preview_item is None:
                self.preview_item = QGraphicsPathItem()
                self.preview_item.setPen(QPen(QColor(128, 128, 128, 255), 2))
                self.map_controller.scene.addItem(self.preview_item)
            self.preview_item.setPath(self.path)

        elif event.event_type == "move" and self.last_position is not None:
            self.path.lineTo(event.x, event.y)
            self.preview_item.setPath(self.path)

        elif event.event_type == "release":
            roads_layer = self.map_controller.layer_manager.get_layer("roads")
            if roads_layer is None:
                print("Brak warstwy 'roads' do rysowania.")
                return
            self.map_controller.snapshot_manager.create_snapshot({
                "layers": {
                    "roads": {
                        "before": copy.deepcopy(roads_layer),
                        "after": copy.deepcopy(self.map_controller.layer_manager.layers["roads"])
                    }
                }
            })
            height, width, _ = roads_layer.shape
            bytes_per_line = 4 * width
            layer_image = QImage(roads_layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)

            painter = QPainter(layer_image)
            pen = QPen(QColor(128, 128, 128, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawPath(self.path)
            painter.end()

            layer_data = layer_image.bits().asstring(bytes_per_line * height)
            self.map_controller.layer_manager.layers["roads"] = np.frombuffer(layer_data, dtype=np.uint8).reshape(height, width, 4)

            # Odświeżenie warstwy
            self.map_controller.layer_manager.refresh_layer("roads")

            # Usunięcie podglądu
            self.last_position = None
            if self.preview_item:
                self.map_controller.scene.removeItem(self.preview_item)
                self.preview_item = None

class Tools:

    @staticmethod
    def erase_area(map_controller, layer_manager, layer_name, x, y, radius=5):
        """
        Usuwa obszar z podanej warstwy, ustawiając piksele w obszarze na przezroczyste.

        :param layer_manager: Obiekt LayerManager odpowiedzialny za warstwy.
        :param layer_name: Nazwa warstwy, na której działa gumka.
        :param x: Współrzędna X środka gumki.
        :param y: Współrzędna Y środka gumki.
        :param radius: Promień gumki.
        """
        # Pobierz warstwę z LayerManager
        layer = layer_manager.get_layer(layer_name)
        if layer is None:
            print(f"Brak warstwy '{layer_name}' do usuwania.")
            return

        # Pobranie wymiarów obrazu warstwy
        height, width, _ = layer.shape
        bytes_per_line = 4 * width
        layer_image = QImage(layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)

        # Usuwanie (rysowanie przezroczystości)
        painter = QPainter(layer_image)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)  # Ustaw tryb usuwania
        painter.setBrush(Qt.transparent)
        painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
        painter.end()

        # Aktualizacja danych warstwy
        layer_data = layer_image.bits().asstring(bytes_per_line * height)
        layer_manager.layers[layer_name] = np.frombuffer(layer_data, dtype=np.uint8).reshape(height, width, 4)

        # Odświeżenie graficznej reprezentacji warstwy
        layer_manager.refresh_layer(layer_name)  # Zamiana z refresh_layer_item

    @staticmethod
    def draw_shape(layer_manager, layer_name, shape, *args, **kwargs):
        """
        Rysuje kształt na podanej warstwie.
        :param shape: Typ kształtu (np. 'ellipse', 'rectangle', 'line').
        :param args: Argumenty definiujące położenie i wymiary kształtu.
        :param kwargs: Opcjonalne argumenty, np. kolor, szerokość linii.
        """
        layer = layer_manager.get_layer(layer_name)
        if layer is None:
            raise ValueError(f"Warstwa '{layer_name}' nie istnieje.")

        # Tworzenie obrazu warstwy
        height, width, _ = layer.shape
        bytes_per_line = 4 * width
        layer_image = QImage(layer.data, width, height, bytes_per_line, QImage.Format_RGBA8888)

        painter = QPainter(layer_image)
        pen = QPen(kwargs.get("color", Qt.black))
        pen.setWidth(kwargs.get("width", 1))
        painter.setPen(pen)

        if shape == "ellipse":
            x, y, w, h = args
            painter.drawEllipse(x, y, w, h)
        elif shape == "rectangle":
            x, y, w, h = args
            painter.drawRect(x, y, w, h)
        elif shape == "line":
            x1, y1, x2, y2 = args
            painter.drawLine(x1, y1, x2, y2)

        painter.end()
        layer_data = layer_image.bits().asstring(bytes_per_line * height)
        layer_manager.layers[layer_name] = np.frombuffer(layer_data, dtype=np.uint8).reshape(height, width, 4)
        layer_manager.refresh_layer(layer_name)

class PixelSampler(dict):
    """Klasa odpowiedzialna za próbkowanie pikseli na mapie."""

    def __init__(self, image, sample_positions, states, tolerance=5):
        self.image = image
        self.sample_positions = sample_positions
        self.states = states
        self.tolerance = tolerance
        print(self.image)
        # Zapisanie wyników próbkowania bezpośrednio w self (dziedziczenie po dict)
        super().__init__(self._sample_pixels())

    def _sample_pixels(self):
        if self.image is None:
            return {}

        # Pobierz wymiary obrazu
        height, width, _ = self.image.shape

        # Inicjalizuj słownik do zliczania prowincji
        counts = {state.name: 0 for state in self.states}

        # Próbkuj piksele na podstawie pozycji
        for x, y in self.sample_positions:
            if 0 <= x < width and 0 <= y < height:
                color = tuple(self.image[y, x])  # Pobierz kolor w formacie RGB

                # Znajdź państwo odpowiadające kolorowi
                for state in self.states:
                    if self.is_similar_color(color, state.color.getRgb()[:3], self.tolerance):
                        counts[state.name] += 1  # Zlicz prowincję
                        break
        return counts

    @staticmethod
    def is_similar_color(color1, color2, tolerance):
        """Porównuje dwa kolory z uwzględnieniem tolerancji."""
        return all(abs(int(c1) - int(c2)) <= tolerance for c1, c2 in zip(color1, color2))
