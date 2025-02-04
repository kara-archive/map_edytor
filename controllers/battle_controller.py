import random
import sys
import argparse

def dialog():
    print("Atak:", end=' ')
    units_attack = int(input())
    print("Atak LvL:", end=' ')
    lvl_a = int(input())
    print("Obrona:", end=' ')
    units_defence = int(input())
    print("Obrona LvL:", end=' ')
    lvl_b = int(input())
    print("Fort?(y/N)", end=' ')
    fort_b = input().lower().strip() in ['y', 'yes', 'tak', 'true']
    # Create lists where each unit is represented as a tuple (army, type,lvl)
    def create_unit(army, unit_type="inf", lvl=1, fort=False, art=False):
        return (army, unit_type, lvl, fort, art)

    army_a = [create_unit('A',lvl=lvl_a) for _ in range(units_attack)]
    army_b = [create_unit('D',lvl=lvl_b,fort=fort_b) for _ in range(units_defence)]
    return army_a, army_b

def rand():
    a = [("A",'inf',1,False,False) for _ in range(random.randint(5,15))]
    b = [("B",'inf',1,False,False) for _ in range(random.randint(5,15))]
    return a, b

def main(army_a, army_b):
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
        defence_result = int(defence_result+unit_b[3]*0.3*defence_result)
        result = attack_result - defence_result

        if result > 0:
            print(
                f"{unit_a[0]} {unit_a[1]}({unit_a[2]})"  # Print unit info
                f"\033[0m \033[1m\t{attack_result} \t {'⚔️️'} \t" # Add result with emoji indicators
                f" {defence_result} \033[0m\t{unit_b[0]} {unit_b[1]}({unit_b[2]}){"F" if unit_b[3] else ""}"  # Print unit info
            )

            del army_b[i]
        elif result < 0:
            print(
                f"{unit_a[0]} {unit_a[1]}({unit_a[2]})"  # Print unit info
                f"\033[0m \033[1m\t{attack_result} \t {'🛡️'} \t" # Add result with emoji indicators
                f" {defence_result} \033[0m\t{unit_b[0]} {unit_b[1]}({unit_b[2]}){"F" if unit_b[3] else ""}"  # Print unit info
            )

            del army_a[i]
        else:
            print(
                f"{unit_a[0]} {unit_a[1]}({unit_a[2]})"  # Print unit info
                f"\033[0m \033[1m\t{attack_result}  \t {' '} \t" # Add result with emoji indicators
                f"  {defence_result}\033[0m\t{unit_b[0]} {unit_b[1]}({unit_b[2]}){"F" if unit_b[3] else ""}" # Print unit info
            )


    # Print the remaining units
    if len(army_a) > len(army_b):
        print(f"Atakujący zajmuje: {len(army_a)} prowincji")
    elif len(army_a) < len(army_b):
        print(f"Broniący odbija: {len(army_b)} prowincji")
    else:
        print("Remis")
    print(f"straty: Atak: {a-len(army_a)} Obrona: {b-len(army_b)}")

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dialog", action="store_true", help="Kreator armii w formie dialogu")
args = parser.parse_args()

try:
    while True:
        title = input()
        if args.dialog:
            a,b = dialog()
        else:
            a,b = rand()
        main(a,b)
except KeyboardInterrupt:
    pass
