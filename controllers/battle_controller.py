import random
import sys
import argparse

def tab(input_str: str, max_length: int = 5) -> str:
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

def dialog():
    print("Atak:", end=' ')
    units_attack = int(input())
    #print("Atak LvL:", end=' ')
    #lvl_a = int(input())
    print("Obrona:", end=' ')
    units_defence = int(input())
    #print("Obrona LvL:", end=' ')
    #lvl_b = int(input())
    print("Fort?(y/N)", end=' ')
    fort_b = input().lower().strip() in ['y', 'yes', 'tak', 'true', "1"]
    # Create lists where each unit is represented as a tuple (army, type,lvl)
    def create_unit(army, unit_type="inf", lvl=1, fort=False, art=False):
        return (army, unit_type, lvl, fort, art)

    army_a = [create_unit('A',) for _ in range(units_attack)]
    army_b = [create_unit('D',fort=fort_b) for _ in range(units_defence)]
    return army_a, army_b

def rand():
    a = [("A",'inf',random.randint(0,9),False,False) for _ in range(random.randint(5,15))]
    b = [("B",'inf',random.randint(0,9),False,False) for _ in range(random.randint(5,15))]
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
        defence_result = int(defence_result+unit_b[3]*0.5*defence_result)
        result = attack_result - defence_result

        if result > 0:
            winner_icon = '<'
            del army_b[i]
        elif result < 0:
            winner_icon = ">"
            del army_a[i]
        else:
            winner_icon = "="

        #print(f"{unit_a[0]} {unit_a[1]}({tab_rev(f"{unit_a[2]})")}{tab(str(attack_result))}{tab(winner_icon)}{tab(str(defence_result))}{tab(str(unit_b[0]))} {unit_b[1]}({unit_b[2]}){'F' if unit_b[3] else ''}")



    # Print the remaining units
    print(f"pozostało: Atak: {len(army_a)} Obrona: {len(army_b)}")
    if len(army_a) > len(army_b):
        print(f"Atakujący zajmuje: {len(army_a)} prowincji")
    elif len(army_a) < len(army_b):
        print(f"Broniący odbija: {len(army_b)} prowincji")
    else:
        print("Remis")
    print(f"straty: Atak: {a-len(army_a)} Obrona: {b-len(army_b)}")
    return army_a, army_b

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
        a, b = main(a,b)



except KeyboardInterrupt:
    pass
