import random
import sys
import argparse
from .tools import tab, tab_rev

parser = argparse.ArgumentParser()
parser.add_argument("--battle", action="store_true", help="dodaj -h po więcej pomocy")
parser.add_argument("-r", "--random", action="store_true", help="losowa armia")
parser.add_argument("-f", "--forts", action="store_true", help="dodaje do dialogu opcje fortów")
parser.add_argument("-lvl", "--levels", action="store_true", help="dodaje do dialogu opcje leveli")
parser.add_argument("-q", "--quiet", action="store_true", help="nie printuje detali", )
args = parser.parse_args()

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

    def battle(army_a, army_b, prin=False, vs=None):
        a, b = len(army_a), len(army_b)
        for i in reversed(range(len(army_a))):
            # Check if both units exist before accessing them
            if i >= len(army_a) or i >= len(army_b):
                i += -1
                continue

            unit_a = army_a[i]
            unit_b = army_b[i]

            # Simulate the battle outcome
            attack_result = random.randint(0, 9+unit_a[2])
            defence_result = random.randint(0, 9+unit_b[2])*(unit_b[3]+1)
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
                print(f"{unit_a[0]} {unit_a[1]}({tab_rev(f"{unit_a[2]})")}"
                    f"{tab(str(attack_result))}\033[1m{tab(winner_icon)}\033[0m{tab(str(defence_result))}"
                    f"{tab(str(unit_b[0]))} {unit_b[1]}({unit_b[2]}){'F' if unit_b[3] else ''}")

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
            if "quiet" in title:
                args.quiet = not args.quiet
                print("print:", args.quiet)
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
                BattleController.battle(a,b, prin=args.quiet, vs=vs)
            else:
                if args.random:
                    a,b = BattleController.rand()
                else:
                    a,b = BattleController.dialog(args.forts, args.levels, vs=vs)

                a2, b2 = a.copy(), b.copy()
                BattleController.battle(a,b, prin=args.quiet, vs=vs)

            print(f"\033[1mpostało\033[0m: \033[96m{agressor}: {len(a)}\033[93m {defender}: {len(b)} \033[0m")
            if len(a) > len(b):
                print(f"[b]\033[96m{agressor} zajmuje: {len(a)} prow.\033[0m [/b]")
            elif len(a) < len(b):
                print(f"[b]\033[93m{defender} odbija: {len(b)} prow.\033[0m[/b]")
            else:
                print("Remis")
            print(f"\033[1mstraty\033[0m: \033[96m{agressor}: {len(a2)-len(a)}\033[93m {defender}: {len(b2)-len(b)} \033[0m")

    except KeyboardInterrupt:
        sys.exit()
