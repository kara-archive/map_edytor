import sys
import argparse
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtGui import QPalette, QColor
from views.main_view import MainView  # Zakładam, że to Twój główny widok
import os
import shutil
import subprocess

def apply_dark_theme(app):
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(0, 0, 0))
    dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(130, 130, 130))
    dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

    app.setPalette(dark_palette)

    # Wymuszenie ciemnego stylu dla przycisków i innych elementów
    app.setStyleSheet("""
        QPushButton {
            background-color: #505050;
            color: #ffffff;
            min-width: 30px;
            min-height: 30px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #454545;
        }
        QPushButton:pressed {
            background-color: #2d2d2d;
        }
        QPushButton:checked {
            background-color: #707070;
        }

    """)

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
    parser = argparse.ArgumentParser(description="Ultymatywny program do prowadzenia mapkowych. Najlepiej się sprawdza do systemu typu z japońskiej, ale sprawdzi się też pod WAGER. kiedyś dodam config to sobie jeszcze dodacie więcej opcji.", epilog="poza tymi opcjami dostępne są w trybie bitwy następujące komendy: echo, forts, levels, [Pańswo 1] vs [Państwo 2], con (kontynuuj), exit")
    parser.add_argument("--load", type=str, help="Ścieżka do pliku ZIP do wczytania przy uruchomieniu.")
    parser.add_argument("--dark", action="store_true", help="Włącza ciemną paletę kolorów.")
    parser.add_argument("--terka", action="store_true", help="nie dostanie dziś cukierka")
    parser.add_argument("--battle", action="store_true", help="tryb bitwy, tylko w konsoli, bo jestem leniwy, argumenty:")
    parser.add_argument("-r", "--random", action="store_true", help="losowa armia")
    parser.add_argument("-f", "--forts", action="store_true", help="dodaje do dialogu opcje fortów")
    parser.add_argument("-lvl", "--levels", action="store_true", help="dodaje do dialogu opcje leveli")
    parser.add_argument("-p", "--print", action="store_true", help="printuje przykładiową armię", )
    parser.add_argument("-e", "--echo", action="store_true", help="nie printuje detali", )
    parser.add_argument("--gui", action="store_true", help="gui do battle")
    parser.add_argument("--no_roads", action="store_true", help="wyłącza konieczność połączenia budyków drogą")
    args = parser.parse_args()


    if args.battle:
        try:
            import controllers.battle_controller as battle
            battle.main()
        except KeyboardInterrupt:
            sys.exit()

    app = QApplication(sys.argv)

    # Ustawienie ciemnej palety kolorów, jeśli podano argument --dark
    if args.dark:
        apply_dark_theme(app)
    else:
        app.setStyleSheet("""
        QPushButton {
            min-width: 30px;
            min-height: 30px;
        }""" )


    if args.terka:
        app.setStyle("Windows")




    main_view = MainView()

    if args.load:
        try:
            main_view.button_panel.load(args.load)  # Wywołanie funkcji ładowania
            print(f"Pomyślnie wczytano plik: {args.load}")
        except Exception as e:
            print(f"Błąd podczas wczytywania pliku: {e}")

    if args.no_roads:
        main_view.map_controller.mode_manager.roads = False

    # Pokaż główne okno
    main_view.setGeometry(10,10,1970,1600)
    main_view.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
