'''
Ten skrypt pomaga ci stworzyć bazę pikseli do próbkowania mapy. nanieś po jednym pikselu na prowincję. Najłatwiej jest po prostuskopiować output w konsoli do sample_positions = []. Jak nie działa, to upewnij się, że masz importy pobrane (pip install cv2) naip się spłaczesz na forum o kupie.
'''

import cv2
import csv
import os

# Ścieżka do obrazu
image_path = "./mapa.png"  # Zmień tę ścieżkę, jeśli obraz jest w innym miejscu

# Ścieżka do pliku CSV, w którym będą zapisywane współrzędne
output_file = "sample_positions.csv"

# Funkcja obsługująca kliknięcia myszą
def click_event(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"({x}, {y})", end=", ")
        
        # Zapis współrzędnych do pliku CSV
        with open(output_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([x, y])
        
        # Rysowanie kropki na obrazie, aby widzieć zaznaczone punkty
        cv2.circle(img, (x, y), 0, (0, 0, 255), -1)
        cv2.imshow("Obraz", img)

# Wczytanie obrazu
img = cv2.imread(image_path)
if img is None:
    print("Nie można wczytać obrazu. Sprawdź ścieżkę do pliku.")
    exit()

# Inicjalizacja pliku CSV z nagłówkiem (jeśli plik nie istnieje)
if not os.path.exists(output_file):
    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["x", "y"])

# Wyświetlenie obrazu w oknie
cv2.imshow("Obraz", img)
cv2.setMouseCallback("Obraz", click_event)

# Naciśnij 'q', aby zamknąć okno i zakończyć program
print("Kliknij na obraz, aby zapisać pozycję. Naciśnij 'q', aby zakończyć.")
while True:
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()

