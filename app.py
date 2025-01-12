import sys
import argparse
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
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
    parser.add_argument("--light", action="store_true", help="Włącza jasną paletę kolorów.")
    args = parser.parse_args()

    # Uruchomienie aplikacji
    app = QApplication(sys.argv)

    # Ustawienie ciemnej palety kolorów, jeśli podano argument --dark
    if not args.light:
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(130, 130, 130))
        dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        app.setPalette(dark_palette)

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
