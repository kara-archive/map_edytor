import sys
import argparse
from PyQt5.QtWidgets import QApplication
from views.main_view import MainView  # Zakładam, że to Twój główny widok

def main():
    # Parsowanie argumentów
    parser = argparse.ArgumentParser(description="sram psa jak sra")
    parser.add_argument("--load", type=str, help="Ścieżka do pliku ZIP do wczytania przy uruchomieniu.")
    args = parser.parse_args()

    # Uruchomienie aplikacji
    app = QApplication(sys.argv)
    main_view = MainView()

    # Jeśli podano parametr --load
    if args.load:
        try:
            main_view.button_panel.load(args.load)  # Wywołanie funkcji ładowania
            print(f"Pomyślnie wczytano plik: {args.load}")
        except Exception as e:
            print(f"Błąd podczas wczytywania pliku: {e}")

    # Pokaż główne okno
    main_view.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
