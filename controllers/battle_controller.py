import random
import sys
import argparse
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QCheckBox, QLabel

parser = argparse.ArgumentParser()
parser.add_argument("--battle", action="store_true", help="dodaj -h po więcej pomocy")
parser.add_argument("--gui", action="store_true", help="gui")
parser.add_argument("-r", "--random", action="store_true", help="losowa armia")
parser.add_argument("-f", "--forts", action="store_true", help="dodaje do dialogu opcje fortów")
parser.add_argument("-lvl", "--levels", action="store_true", help="dodaje do dialogu opcje leveli")
parser.add_argument("-e", "--echo", action="store_true", help="nie printuje detali", )
args = parser.parse_args()

def tab(input_str: str, max_length: int = 4) -> str:
    letters = input_str
    #print(letters, len(letters))
    result = []
    for _ in range(max_length-len(letters)):
        result.append(" ")
    result.append(input_str)
    return ''.join(result)

def tab_rev(input_str: str, max_length: int = 3) -> str:
    letters = input_str
    #print(letters, len(letters))
    result = []
    result.append(input_str)
    for _ in range(max_length-len(letters)):
        result.append(" ")
    return ''.join(result)

class BattleController:
    def dialog(forts=False,lvls=False, vs=None):
        while True:
            chuj = " "
            if not vs:
                vs = ["", "",""]
                chuj = ""
            try:
                print(f"Atak{chuj+vs[0]}:", end=' ')
                units_attack = int(input())
                if lvls:
                    print(f"{vs[0]} LvL:", end=' ')
                    lvl_a = int(input())
                else:
                    lvl_a=0
                print(f"Obrona{chuj+(vs[2])}:", end=' ')
                units_defence = int(input())
                if lvls:
                    print(f"{vs[2]} LvL:", end=' ')
                    lvl_b = int(input())
                else:
                    lvl_b = 0
                if forts:
                    print("Fort?(y/N)", end=' ')
                    fort_b = input().lower().strip() in ['y', 'yes', 'tak', 'true', "1"]
                else:
                    fort_b = False
                break
            except ValueError:
                print("Dane muszą być liczbą.")

        # Create lists where each unit is represented as a tuple (army, type,lvl)
        def create_unit(army, unit_type="inf", lvl=1, fort=False, art=False):
            return (army, unit_type, lvl, fort, art)

        army_a = [create_unit('A',lvl=lvl_a) for _ in range(units_attack)]
        army_b = [create_unit('B',lvl=lvl_b,fort=fort_b) for _ in range(units_defence)]
        return army_a, army_b

    def rand():
        a = [("A",'inf',random.randint(0,0),False,False) for _ in range(random.randint(10,10))]
        b = [("B",'inf',random.randint(0,0),random.randint(0,1),False) for _ in range(random.randint(10,10))]
        return a, b

    def battle(army_a, army_b, echo=False):
        """army_a, army_b is a list of tuples (army, unit_type, lvl, fort, art)
        where army is string 'A' or 'B', unit_type is string 'inf' or 'cav', lvl is int, fort and art are bool"""
        a, b = len(army_a), len(army_b)
        for i in reversed(range(len(army_a))):
            # Check if both units exist before accessing them
            if i >= len(army_a) or i >= len(army_b):
                i += -1
                continue

            unit_a = army_a[i]
            unit_b = army_b[i]

            # Simulate the battle outcome
            attack_result = int(random.randint(0, 9+unit_a[2])*(unit_a[3]*0.5+1))
            defence_result = int(random.randint(0, 9+unit_b[2])*(unit_b[3]*0.5+1))
            result = attack_result - defence_result

            if result > 0:
                winner_icon = '<-'
                del army_b[i]
            elif result < 0:
                winner_icon = "->"
                del army_a[i]
            else:
                winner_icon = "=="
            if echo:
                print(f"{unit_a[0]} {unit_a[1]}({tab_rev(f"{unit_a[2]})")}{'\b'+tab_rev(('F' if unit_a[3] else '')+('A' if unit_a[4] else ''))}"
                    f"{tab(str(attack_result))}\033[1m{tab(winner_icon)}\033[0m{tab(str(defence_result))}"
                    f"{tab(str(unit_b[0]))} {unit_b[1]}({unit_b[2]}){'F' if unit_b[3] else ''}{'A' if unit_b[4] else ''}")

        return army_a, army_b


def main():
    print("symulator bitew")
    try:
        while True:
            title = input()
            vs = None
            if title == "exit":
                sys.exit()
            if title == "app":
                break
            if title == "gui":
                start()
                continue
            if "echo" in title:
                args.echo = not args.echo
                print("echo:", args.echo)
                continue
            if "forts" in title:
                args.forts = not args.forts
                print("Forty:", args.forts)
                continue
            if "levels" in title:
                args.levels = not args.levels
                print("LvL:", args.levels)
                continue
            if "vs" in title:
                vs = title.title().split()
                agressor = vs[0]
                defender = vs[2]
            else:
                agressor = "Atakujący"
                defender = "Broniący"
            if title == "con":
                BattleController.battle(a,b, echo=args.echo)
            elif title == "kurwa":
                while len(a) > 0 and len(b) > 0:
                    BattleController.battle(a,b, echo=args.echo)
            else:
                if args.random:
                    a,b = BattleController.rand()
                else:
                    a,b = BattleController.dialog(args.forts, args.levels, vs=vs)

                a2, b2 = a.copy(), b.copy()
                BattleController.battle(a,b, echo=args.echo)

            print(f"\033[1mpostało\033[0m: \033[96m{agressor}: {len(a)}\033[93m {defender}: {len(b)} \033[0m")
            if len(a) > len(b):
                print(f"[b]\033[96m{agressor} zajmuje: {len(a)} prow.\033[0m[/b]")
            elif len(a) < len(b):
                print(f"[b]\033[93m{defender} odbija: {len(b)} prow.\033[0m[/b]")
            else:
                print("Remis")
            print(f"\033[1mstraty\033[0m: \033[96m{agressor}: {len(a2)-len(a)}\033[93m {defender}: {len(b2)-len(b)} \033[0m")

    except KeyboardInterrupt:
        sys.exit()



class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 1080, 720)
        self.setWindowTitle("Army Battle Simulator")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Left
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_widget.setLayout(self.left_layout)
        self.layout.addWidget(self.left_widget)
        if True:
            #ad unit butto
            self.add_unit_a_button = QPushButton('Dodaj')
            self.add_unit_a_button.clicked.connect(lambda: self.add_unit(self.table_a))
            self.left_layout.addWidget(self.add_unit_a_button)

            self.add_unit_a_button = QPushButton('Dodaj 5')
            self.add_unit_a_button.clicked.connect(lambda: self.add_5_unit(self.table_a))
            self.left_layout.addWidget(self.add_unit_a_button)

            self.add_table("A")


        #MIDDLE START bATTLE
        self.start_button = QPushButton('Start Battle')
        self.start_button.clicked.connect(self.simulate_battle)
        self.layout.addWidget(self.start_button)

        #right
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_widget.setLayout(self.right_layout)
        self.layout.addWidget(self.right_widget)
        if True:
            #add unit
            self.add_unit_b_button = QPushButton('Dodaj')
            self.add_unit_b_button.clicked.connect(lambda: self.add_unit(self.table_b, army='B'))
            self.right_layout.addWidget(self.add_unit_b_button)

            self.add_unit_b_button = QPushButton('Dodaj 5')
            self.add_unit_b_button.clicked.connect(lambda: self.add_5_unit(self.table_b, army='B',))
            self.right_layout.addWidget(self.add_unit_b_button)
            #table
            self.add_table("B")

    def simulate_battle(self):
        army_a = []
        for row in range(self.table_a.rowCount()):
            army, unit_type, level, fort, art = (self.table_a.item(row, col).text() if self.table_a.item(row, col) else ''
                                           for col in range(5))
            army_a.append((army, unit_type, int(level), fort in ['True', "1"], art in ['True', "1"]))

        army_b = []
        for row in range(self.table_b.rowCount()):
            army, unit_type, level, fort, art = (self.table_b.item(row, col).text() if self.table_b.item(row, col) else ''
                                           for col in range(5))
            army_b.append((army, unit_type, int(level), fort in ['True', "1"], art in ['True', "1"]))

        final_a, final_b = BattleController.battle(army_a.copy(), army_b.copy(), echo=args.echo)

        print(f"\033[1mpostało\033[0m: \033[96mAtakujący: {len(final_a)}\033[93m Broniący: {len(final_b)} \033[0m")
        if len(final_a) > len(final_b):
            print(f"[b]\033[96mAtakujący: zajmuje: {len(final_a)} prow.\033[0m[/b]")
        elif len(final_a) < len(final_b):
            print(f"[b]\033[93mBroniący odbija: {len(final_b)} prow.\033[0m[/b]")
        else:
            print("Remis")
        print(f"\033[1mstraty\033[0m: \033[96mAtakujący:: {len(army_a)-len(final_a)}\033[93m Broniący: {len(army_b)-len(final_b)} \033[0m")

        self.update_tables(final_a, final_b)

    def add_unit(self, table, army='A', unit='inf', lvl='1', fort=False, art=False):
        row = table.rowCount()
        table.setRowCount(row + 1)
        table.setItem(row, 0, QTableWidgetItem(army))
        table.setItem(row, 1, QTableWidgetItem(unit))
        table.setItem(row, 2, QTableWidgetItem(lvl))
        table.setItem(row, 3, QTableWidgetItem(fort))
        table.setItem(row, 4, QTableWidgetItem(art))

    def add_5_unit(self, table, army='A',):
        for _ in range(5):
            self.add_unit(table, army,)

    def add_table(self, table):
        if table=='B':
            self.table_b = QTableWidget(0, 5)
            self.table_b.setHorizontalHeaderLabels(['Army', 'Type', 'Level', 'Fort', "Art"])
            self.right_layout.addWidget(self.table_b)
        elif table == 'A':
            self.table_a = QTableWidget(0, 5)
            self.table_a.setHorizontalHeaderLabels(['Army', 'Type', 'Level', 'Fort', 'Art'])
            self.left_layout.addWidget(self.table_a)

    def update_tables(self, army_a, army_b):
        # Clear table_a
        self.left_layout.removeWidget(self.table_a)
        self.add_table('A')
        for unit in army_a:
            self.add_unit(self.table_a, unit[0], unit[1], str(unit[2]), str(unit[3]), str(unit[4]))
        # Clear table_b
        self.left_layout.removeWidget(self.table_b)
        self.add_table('B')
        for unit in army_b:
            self.add_unit(self.table_b, unit[0], unit[1], str(unit[2]), str(unit[3]), str(unit[4]))


def start():
        app = QApplication(sys.argv)
        window = MyWindow()
        window.show()
        app.exec_()

if args.gui:
    sys.exit(start())
elif __name__ == "__main__":
    main()
