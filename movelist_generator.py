import json
import os
import mysql.connector
from dotenv import load_dotenv

dotenv_path = 'env/credentials.env'
load_dotenv(dotenv_path)

GEN3 = 7
MOVES_MAX = 354

super_eff_dict = {"normal": [],
                  "fire": ["bug", "steel", "grass", "ice"],
                  "fighting": ["rock", "ice", "steel", "normal", "dark"],
                  "water": ["fire", "ground", "rock"],
                  "flying": ["fighting", "grass", "bug"],
                  "grass": ["rock", "ground", "water"],
                  "poison": ["grass"],
                  "electric": ["flying", "water"],
                  "rock": ["flying", "fire", "bug", "ice"],
                  "ground": ["electric", "poison", "fire", "steel", "rock"],
                  "ice": ["flying", "dragon", "grass", "ground"],
                  "dragon": ["dragon"],
                  "ghost": ["ghost", "psychic"],
                  "dark": ["ghost", "psychic"],
                  "psychic": ["fighting", "poison"],
                  "bug": ["grass", "psychic", "dark"],
                  "steel": ["rock", "ice"],
                  "fairy": ["dragon", "fighting", "dark"]
                  }
not_eff_dict = {"normal": ["rock", "steel"],
                "fire": ["rock", "fire", "water", "dragon"],
                "fighting": ["flying", "poison", "bug", "psychic", "fairy"],
                "water": ["water", "grass", "dragon"],
                "flying": ["rock", "steel", "electric"],
                "grass": ["flying", "poison", "bug", "steel", "fire", "grass", "dragon"],
                "poison": ["poison", "ground", "rock", "ghost"],
                "electric": ["grass", "electric", "dragon"],
                "rock": ["fighting", "ground", "steel"],
                "ground": ["bug", "grass"],
                "ice": ["ice", "steel", "fire", "water"],
                "dragon": ["steel"],
                "ghost": ["dark"],
                "dark": ["fighting", "dark", "fairy"],
                "psychic": ["steel", "psychic"],
                "bug": ["fighting", "flying", "poison", "ghost", "steel", "fire", "fairy"],
                "steel": ["steel", "fire", "water", "electric"],
                "fairy": ["poison", "fire", "steel"]
                }
# necessary for dualtype pokemon calculation
weakness_dict = {"normal": ["fighting"],
                  "fire": ["ground", "rock", "water"],
                  "fighting": ["flying", "psychic"],
                  "water": ["grass", "electric"],
                  "flying": ["electric", "rock", "ice"],
                  "grass": ["flying", "poison", "bug", "fire", "ice"],
                  "poison": ["psychic", "ground"],
                  "electric": ["ground"],
                  "rock": ["water", "fighting", "steel", "grass", "ground"],
                  "ground": ["water", "ice", "grass"],
                  "ice": ["fire", "fighting", "rock", "steel"],
                  "dragon": ["dragon", "ice"],
                  "ghost": ["ghost", "dark"],
                  "dark": ["fighting", "bug"],
                  "psychic": ["dark", "bug", "ghost"],
                  "bug": ["fire", "flying", "rock"],
                  "steel": ["fire", "fighting", "ground"],
                  "fairy": ["poison", "steel"]
                  }
# just in case
immunity_dict = {"normal": ["ghost"],
                 "fighting": ["ghost"],
                 "poison": ["steel"],
                 "ground": ["flying"],
                 "ghost": ["normal"],
                 "electric": ["ground"],
                 "psychic": ["dark"],
                 "dragon": ["fairy"]
                 }
damage_type_dict = {"physical": ["normal", "fighting", "flying", "bug", "rock", "ground", "dark", "poison", "steel"],
                    "special": ["electric", "grass", "water", "fire", "ghost", "dragon", "ice", "psychic", "fairy"]
                    }
known_short_effs = []

# weight moves
# normal weight - gen 3 moves
# later gen moves = unknown - less weight unless effect is known
# extra weight - type weakness coverage, known move effects
# type weakness coverage based on atk or spatk

EFF_KNOWN = 1
TYPE_WEAKNESS_COVERAGE = 1.5
ATTACK_ALIGNMENT = .75
LEVEL_W_GEN3 = 1
POWER = 1
STAB = .75
OTHER_W = .25

def moveListConstructor(db):
    cursor = db.cursor()
    # get all unique short effects that are currently known in gen 3
    short_effs_query = "WITH CTE AS (SELECT DISTINCT id, name, short_effect, row_number() OVER (PARTITION BY short_effect ORDER BY id ASC) RN FROM moves) SELECT * FROM cte WHERE RN = 1 AND id<=354 ORDER BY id ASC"
    cursor.execute(short_effs_query)
    for res in cursor.fetchall():
        known_short_effs.append(res[2])

    # TODO loop through all pokemon
    # query pokemon
    poke_query = "SELECT name, type1, type2, attack, spattack, by_level, by_tutor, by_machine, by_breeding FROM pokemon WHERE name = 'bulbasaur'"
    cursor.execute(poke_query)
    name, type1, type2, attack, spattack, level_temp, tutor_temp, machine_temp, egg_temp = cursor.fetchone()
    cursor.close()
    by_level = json.loads(level_temp)
    by_tutor = json.loads(tutor_temp)
    by_machine = json.loads(machine_temp)
    by_egg = json.loads(egg_temp)

    # check attack alignment
    physical = None
    if attack > spattack and (attack - spattack) >= 20:
        physical = True
    if attack < spattack and (spattack - attack) >= 20:
        physical = False

    # find types for attacks to counter pokemon's counters
    weak_combo = []
    if type2 == None:
        weak_combo = weakness_dict[type1]
    else:
        for i in weakness_dict[type1]:
            if type2 not in not_eff_dict[i]:
                weak_combo.append(i)
        for j in weakness_dict[type2]:
            if type1 not in not_eff_dict[j]:
                weak_combo.append(j)
    weak_coverage = []
    for i in weak_combo:
        for j in weakness_dict[i]:
            if j not in weak_coverage:
                weak_coverage.append(j)

    types = (type1, type2)
    # new dict for all moves weights
    weight_dict = {}
    addWeights(types, physical, weak_coverage, weight_dict, by_level, True, db)
    addWeights(types, physical, weak_coverage, weight_dict, by_tutor, False, db)
    addWeights(types, physical, weak_coverage, weight_dict, by_machine, False, db)
    addWeights(types, physical, weak_coverage, weight_dict, by_egg, False, db)

    top_moves = sorted(weight_dict.items(), key=lambda x:x[1], reverse=True)
    [print(move, val) for move, val in top_moves[:13]]


def addWeights(poke_types, physical, coverage, weight_dict, learn_dict, by_level, db):   
    cursor = db.cursor()
    # print("Analyzing new learn_dict")
    # search through learn_dicts
    for key, val in learn_dict.items():
        # print(f"{key}")
        # if GEN3 not in val: ########################
            if key not in weight_dict:
                weight_dict[key] = 0
            # db query -- what is the type if the current move
            type_query = f"SELECT type, short_effect, power FROM moves WHERE name = '{key}'"
            cursor.execute(type_query)
            move_type, short_eff, power = cursor.fetchone()
            # TODO remove gen 3 machine/tutor moves from the list

            # by_level
            if by_level:
                # print(f"    + by level")
                for gen in val:
                    if int(gen) <= GEN3:
                        weight_dict[key] += LEVEL_W_GEN3
                    else:
                        weight_dict[key] += OTHER_W
            # STAB weight
            if move_type in poke_types:
                weight_dict[key] += STAB
                # print(f"    + stab")
            # coverage weight
            if move_type in coverage:
                weight_dict[key] += TYPE_WEAKNESS_COVERAGE
                # print(f"    + coverage")
            # attack type alignment weight
            if physical != None:
                if physical and move_type in damage_type_dict["physical"]:
                    weight_dict[key] += ATTACK_ALIGNMENT
                    # print(f"    + physical preference")
                if not physical and move_type in damage_type_dict["special"]:
                    weight_dict[key] += ATTACK_ALIGNMENT
                    # print(f"    + special preference")
            # known short effects
            if short_eff in known_short_effs:
                weight_dict[key] += EFF_KNOWN
                # print(f"    + known effect")
            # preference for attack moves
            if power != None:
                weight_dict[key] += POWER
                # print(f"    + attack")
        
    # print()

def main():
    try:
        db = mysql.connector.connect(
            user = os.environ.get("DB_USER"),
            password = os.environ.get("DB_PASSWORD"),
            host = os.environ.get("DB_HOST"),
            port = 3306,
            database = os.environ.get("DB_DATABASE")
        )
        print("Successful connection")

        moveListConstructor(db)
        db.close()
    except mysql.connector.Error as err:
        print(f"Error connecting to MYSQL: {err}")
    

if __name__ == "__main__":
    main()