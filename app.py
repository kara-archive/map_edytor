import sys
import argparse
from PyQt5.QtWidgets import QApplication
from views.main_view import MainView  # Zakładam, że to Twój główny widok
import os
import shutil

def ensure_resources_exist():
    # Ścieżka do katalogu tymczasowego w PyInstaller
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))

    # Ścieżki do folderów wbudowanych w aplikację
    icons_path = os.path.join(base_path, "icons")
    tury_path = os.path.join(base_path, "Tury")

    # Ścieżki, gdzie mają być zapisane brakujące pliki
    output_icons = os.path.join(os.getcwd(), "icons")
    output_tury = os.path.join(os.getcwd(), "Tury")

    # Tworzenie folderów, jeśli nie istnieją
    if not os.path.exists(output_icons):
        print("Tworzę brakujący folder 'icons'")
        shutil.copytree(icons_path, output_icons)

    if not os.path.exists(output_tury):
        print("Tworzę brakujący folder 'Tury'")
        os.makedirs(output_tury, exist_ok=True)

# Wywołaj funkcję podczas uruchamiania programu
ensure_resources_exist()

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
