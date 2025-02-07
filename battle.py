import sys
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QCheckBox, QLabel

def battle(army_a, army_b, prin=False, vs=None):
    a, b = len(army_a), len(army_b)
    for i in reversed(range(len(army_a))):
        if i >= len(army_a) or i >= len(army_b):
            continue
        unit_a = army_a[i]
        unit_b = army_b[i]
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
        if prin:
            print(f"{unit_a[0]} {unit_a[1]}({unit_a[2]}){'F' if unit_a[3] else ''}\t"
                  f"{str(attack_result)}\033[1m\t{winner_icon}\t\033[0m{str(defence_result)}\t"
                  f"{str(unit_b[0])} {unit_b[1]}({unit_b[2]}){'F' if unit_b[3] else ''}")
    return army_a, army_b

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 800, 600)
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
            self.add_unit_a_button = QPushButton('Add Unit to Army A')
            self.add_unit_a_button.clicked.connect(lambda: self.add_unit(self.table_a))
            self.left_layout.addWidget(self.add_unit_a_button)

            self.add_unit_a_button = QPushButton('Add 5 Unit to Army A')
            self.add_unit_a_button.clicked.connect(lambda: self.add_5_unit(self.table_a))
            self.left_layout.addWidget(self.add_unit_a_button)
            #table
            self.table_a = QTableWidget(0, 4)
            self.table_a.setHorizontalHeaderLabels(['Army', 'Type', 'Level', 'Fort'])
            self.left_layout.addWidget(self.table_a)





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
            self.add_unit_b_button = QPushButton('Add Unit to Army B')
            self.add_unit_b_button.clicked.connect(lambda: self.add_unit(self.table_b, army='B'))
            self.right_layout.addWidget(self.add_unit_b_button)

            self.add_unit_b_button = QPushButton('Add 5 Unit to Army B')
            self.add_unit_b_button.clicked.connect(lambda: self.add_5_unit(self.table_b, army='B',))
            self.right_layout.addWidget(self.add_unit_b_button)
            #table
            self.table_b = QTableWidget(0, 4)
            self.table_b.setHorizontalHeaderLabels(['Army', 'Type', 'Level', 'Fort'])
            self.right_layout.addWidget(self.table_b)






    def simulate_battle(self):
        army_a = []
        for row in range(self.table_a.rowCount()):
            army, unit_type, level, fort = (self.table_a.item(row, col).text() if self.table_a.item(row, col) else ''
                                           for col in range(4))
            army_a.append((army, unit_type, int(level), fort in ['True', "1"]))

        army_b = []
        for row in range(self.table_b.rowCount()):
            army, unit_type, level, fort = (self.table_b.item(row, col).text() if self.table_b.item(row, col) else ''
                                           for col in range(4))
            army_b.append((army, unit_type, int(level), fort in ['True', "1"]))

        final_a, final_b = battle(army_a.copy(), army_b.copy(), prin=True)
        print(f"A: {len(army_a)-len(final_a)} B: {len(army_b)-len(final_b)}")
        self.update_tables(final_a, final_b)

    def add_unit(self, table, army='A', unit='inf', lvl='1', fort=False):
        row = table.rowCount()
        table.setRowCount(row + 1)
        table.setItem(row, 0, QTableWidgetItem(army))
        table.setItem(row, 1, QTableWidgetItem(unit))
        table.setItem(row, 2, QTableWidgetItem(lvl))
        table.setItem(row, 3, QTableWidgetItem(fort))

    def add_5_unit(self, table, army='A',):
        for _ in range(50):
            self.add_unit(table, army,)

    def update_tables(self, army_a, army_b):
        # Clear table_a
        self.left_layout.removeWidget(self.table_a)
        self.table_a = QTableWidget(0, 4)
        self.table_a.setHorizontalHeaderLabels(['Army', 'Type', 'Level', 'Fort'])
        self.left_layout.addWidget(self.table_a)

        # Add units from army_a to table_a
        for unit in army_a:
            row = self.table_a.rowCount()
            self.table_a.setRowCount(row + 1)
            self.table_a.setItem(row, 0, QTableWidgetItem(unit[0]))
            self.table_a.setItem(row, 1, QTableWidgetItem(unit[1]))
            self.table_a.setItem(row, 2, QTableWidgetItem(str(unit[2])))
            self.table_a.setItem(row, 3, QTableWidgetItem(str(unit[3])))

        # Clear table_b
        self.left_layout.removeWidget(self.table_b)
        self.table_b = QTableWidget(0, 4)
        self.table_b.setHorizontalHeaderLabels(['Army', 'Type', 'Level', 'Fort'])
        self.right_layout.addWidget(self.table_b)

        # Add units from army_b to table_b
        for unit in army_b:
            row = self.table_b.rowCount()
            self.table_b.setRowCount(row + 1)
            self.table_b.setItem(row, 0, QTableWidgetItem(unit[0]))
            self.table_b.setItem(row, 1, QTableWidgetItem(unit[1]))
            self.table_b.setItem(row, 2, QTableWidgetItem(str(unit[2])))
            self.table_b.setItem(row, 3, QTableWidgetItem(str(unit[3])))

    def setup_tables(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.setup_tables()
    window.show()
    sys.exit(app.exec_())
