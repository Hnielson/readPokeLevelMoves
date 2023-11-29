import json
import os
import time
import requests
import mysql.connector
from dotenv import load_dotenv

dotenv_path = 'env/credentials.env'
load_dotenv(dotenv_path)

MAX_POKEMON = 252
MAX_MOVES_GEN_7 = 354
MAX_MOVES = 905
FIRERED_GEN = 7

host = os.getenv('DB_HOST')
user = os.getenv('DB_USER')
password = os.environ.get('DB_PASSWORD')
database = os.environ.get('DB_DATABASE')

print(host, user, password, database)

try:
    db = mysql.connector.connect(
            user = user,
            password = password,
            host = host,
            port = 3306,
            database = database
        )
    print("Successful connection")
    db.close()
except mysql.connector.Error as err:
    print("Error connecting to MySQL:", err)

base_url = "https://pokeapi.co/api/v2/"

def parse_pokemon_moves():
    for poke_id in range(1, MAX_POKEMON):
        url = f"{base_url}/pokemon/{poke_id}"
        response = requests.get(url)
        if response.status_code == 200:
            pokemon_data = response.json()
            poke_name = pokemon_data["name"]
            moves = pokemon_data["moves"]

            level = []
            level_count = {}
            machine = []
            machine_count = {}
            tutor = []
            tutor_count = {}
            egg = []
            egg_count = {}
            for move in moves:
                learn_method = move["version_group_details"]
                move_name = move["move"]["name"]
                for i in learn_method:
                    method_name = i["move_learn_method"]["name"]
                    if i["level_learned_at"] > 0:
                        if move_name in level:
                            level_count[move_name] += 1
                        else:
                            level.append(move_name)
                            level_count[move_name] = 1
                    if method_name == "egg":
                        if move_name in egg:
                            egg_count[move_name] += 1
                        else:  
                            egg.append(move_name)
                            egg_count[move_name] = 1
                    if method_name == "machine":
                        if move_name in machine:
                            machine_count[move_name] += 1
                        else:
                            machine.append(move_name)
                            machine_count[move_name] = 1
                    if method_name == "tutor":
                        if move_name in tutor:
                            tutor_count[move_name] += 1
                        else:
                            tutor.append(move_name)
                            tutor_count[move_name] = 1
                    
            # print(f'\n--{poke_name}--')
            # print('\n--level--', *((k, v) for k, v in level_count.items()), sep='\n')
            # print('\n--machine--', *((i, machine_count[i]) for i in machine_count), sep='\n')
            # print('\n--tutor--', *((k, tutor_count[k]) for k in tutor_count), sep='\n')
            # print('\n--egg--', *((k, egg_count[k]) for k in egg_count), sep='\n')

            poke_json = {}
            poke_json["name"] = poke_name
            poke_json['level'] = level_count
            poke_json['machine'] = machine_count
            poke_json['tutor'] = tutor_count
            poke_json['egg'] = egg_count

            filename = "pokemoves_db.json"
            if os.path.isfile(filename) and os.stat(filename).st_size != 0:
                with open(filename, "r") as file:
                    existing_data = json.load(file)
            else:
                existing_data = []

            existing_data.append(poke_json)
            with open(filename, "w") as outfile:
                json.dump(existing_data, outfile)

            time.sleep(2)

        else:
            print("Response request unsuccessful. Status Code", response.status_code)
            break    

# download all pokemon 1-251
#   download all moves that each can learn
#   separate moves by:
#       egg
#       tutor
#       level
#       machine
#   count through all instances of moves and add to list with most hits

# create mysql server for housing move_data for
# ease of access
def categorize_moves(eff, short_eff):
    for move_id in range(MAX_MOVES_GEN_7, MAX_MOVES):
        move_url = f"{base_url}/move/{move_id}"
        response = requests.get(move_url)
        if response.status_code == 200:
            move_data = response.json() # moves
            name = move_data["name"]
            id = move_data["id"]
            if len(move_data["effect_entries"]) > 0:
                temp = move_data["effect_entries"][0]
                effect = temp["effect"]
                short_effect = temp["short_effect"]
                if eff in effect and short_eff in short_effect:
                    print(f"{id} {name}: {short_effect}")
        else:
            print("Categorize moves request unsuccessful. Status Code", response.status_code)
        time.sleep(2)
        

def main():
    pass
    # parse_pokemon_moves()

    # __eff__short_eff__
    #   normal      = "inflicts regular damage", "no additional effect"
    #   crit        = "inflicts regular damage", "crit"
    #   damAtrLowr  = "Inflicts regular damage", "to lower"
    #   damAtrRais  = "Inflicts regular damage", "to raise"
    #   damageHeal  = "Inflicts regular damage", "drain"

    # categorize_moves("Inflicts regular damage.", "no additional effect")


if __name__ == "__main__":
    main()