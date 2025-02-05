import random
import sys
import argparse

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

def dialog(forts=False,lvls=False):
    while True:
        try:
            print("Atak:", end=' ')
            units_attack = int(input())
            if lvls:
                print("Atak LvL:", end=' ')
                lvl_a = int(input())
            else:
                lvl_a=0
            print("Obrona:", end=' ')
            units_defence = int(input())
            if lvls:
                print("Obrona LvL:", end=' ')
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
    army_b = [create_unit('D',lvl=lvl_b,fort=fort_b) for _ in range(units_defence)]
    return army_a, army_b

def rand():
    a = [("A",'inf',random.randint(0,9),False,False) for _ in range(random.randint(5,15))]
    b = [("B",'inf',random.randint(0,9),False,False) for _ in range(random.randint(5,15))]
    return a, b

def battle(army_a, army_b):
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
        defence_result = random.randint(0, 9+unit_b[2])
        defence_result = int(defence_result+unit_b[3]*defence_result)
        result = attack_result - defence_result

        if result > 0:
            winner_icon = '<'
            del army_b[i]
        elif result < 0:
            winner_icon = ">"
            del army_a[i]
        else:
            winner_icon = "="
        if not args.quiet:
            print(f"{unit_a[0]} {unit_a[1]}({tab_rev(f"{unit_a[2]})")}{tab(str(attack_result))}\033[1m{tab(winner_icon)}\033[0m{tab(str(defence_result))}{tab(str(unit_b[0]))} {unit_b[1]}({unit_b[2]}){'F' if unit_b[3] else ''}")



    # Print the remaining units
    print(f"\033[1mpostało\033[0m: \033[96mAtak: {len(army_a)}\033[93m Obrona: {len(army_b)} \033[0m")
    if len(army_a) > len(army_b):
        print(f"\033[96mAtakujący zajmuje: {len(army_a)} prow.\033[0m")
    elif len(army_a) < len(army_b):
        print(f"\033[93mBroniący odbija: {len(army_b)} prow.\033[0m")
    else:
        print("Remis")
    print(f"\033[1mstraty\033[0m: \033[96mAtak: {a-len(army_a)}\033[93m Obrona: {b-len(army_b)} \033[0m")
    return army_a, army_b

parser = argparse.ArgumentParser(epilog="pojedyncza jednostka to tuple: ('Armia', 'Typ', LvL, Fort, Artyleria)",prefix_chars="+")
parser.add_argument("+r", "++random", action="store_true", help="losowa armia")
parser.add_argument("+f", "++forts", action="store_true", help="dodaje do dialogu opcje fortów")
parser.add_argument("+lvl", "++levels", action="store_true", help="dodaje do dialogu opcje leveli")
parser.add_argument("+p", "++print", action="store_true", help="printuje przykładiową armię", )
parser.add_argument("+q", "++quiet", action="store_true", help="nie printuje detali", )



args = parser.parse_args()

try:
    while True:
        title = input()
        if args.random:
            a,b = rand()
            print(a,b)
        else:
            a,b = dialog(args.forts, args.levels)
        a, b = battle(a,b)



except KeyboardInterrupt:
    pass
