import json
import os
import time
import requests
import mysql.connector
from dotenv import load_dotenv
import re

dotenv_path = 'env/credentials.env'
load_dotenv(dotenv_path)

MAX_POKEMON = 250
MAX_MOVES_GEN_7 = 354
MAX_MOVES = 905
FIRERED_GEN = 7

# list of gen 3 tutor moves
EXCLUDED_MOVES = ["blast-burn", "frenzy-plant", "hydro-cannon",
                    "counter", "double-edge", "dream-eater",
                    "explosion", "mega-kick", "mega-punch",
                    "metronome", "mimic", "seismic-toss",
                    "soft-boiled", "substitute", "thunder-wave",
                    "rock-slide", "swords-dance", "fury-cutter",
                    "rollout", "swagger", "dynamic-punch", "sleep-talk",
                    "nightmare", "self-destruct", "sky-attack"]

base_url = "https://pokeapi.co/api/v2/"

# download *all pokemon data for tables
# download *all move data for tables
# in other file parse data from db with weight

def pokemonLearnReader(db):
    # get MAX_POKEMON
    # response = requests.get(f"{base_url}/pokemon/?limit={MAX_POKEMON}")
    response = requests.get(f"{base_url}/pokemon/?limit=2")
    if response.status_code == 200:
        cursor = db.cursor()

        pokemon_data = response.json()
        results = pokemon_data["results"]
        for pokemon in results:
            # url for each pokemon
            poke_name = pokemon["name"]
            poke_url = pokemon["url"]
            poke_response = requests.get(poke_url)
            if poke_response.status_code == 200:
                # mysql json data
                poke_info = poke_response.json()
                type1 = poke_info["types"][0]["type"]["name"]
                type2 = poke_info["types"][1]["type"]["name"] if poke_info["types"][1] else None
                stats = poke_info["stats"]
                attack = stats[1]["base_stat"]
                spattack = stats[3]["base_stat"]
                name = poke_info["name"]
                moves = poke_info["moves"]

                # learnsets of pokemon
                by_level = {}
                by_machine = {}
                by_tutor = {}
                by_egg = {}
                for move in moves:
                    level_gen = []
                    machine_gen = []
                    tutor_gen = []    
                    egg_gen = []
                    move_name = move["move"]["name"]
                    version_group_details = move["version_group_details"]
                    for content in version_group_details:
                        move_learn_method = content["move_learn_method"]
                        method_name = move_learn_method["name"]
                        gen = re.search(r"/version-group/(\d+)/$", content["version_group"]["url"]).group(1)

                        if content["level_learned_at"] > 0 and method_name == "level-up" and move_name not in EXCLUDED_MOVES:
                            if move_name not in by_level:
                                by_level.update({move_name: level_gen})
                            by_level[move_name].append(gen)
                        if method_name == "egg":
                            if move_name not in by_egg:
                                by_egg.update({move_name: egg_gen})
                            by_egg[move_name].append(gen)
                        if method_name == "machine":
                            if move_name not in by_machine:
                                by_machine.update({move_name: machine_gen})
                            by_machine[move_name].append(gen)
                        if method_name == "tutor" and move_name not in EXCLUDED_MOVES:
                            if move_name not in by_tutor:
                                by_tutor.update({move_name: tutor_gen})                            
                            by_tutor[move_name].append(gen)

                # insert mysql query

                for key, val in by_level.items():
                    print(f"{key}, {val}")

                # poke_json = {}
                # poke_json["name"] = poke_name

                # poke_json['level'] = level_count
                # poke_json['machine'] = machine_count
                # poke_json['tutor'] = tutor_count
                # poke_json['egg'] = egg_count

                # filename = "pokemoves_db.json"
                # if os.path.isfile(filename) and os.stat(filename).st_size != 0:
                #     with open(filename, "r") as file:
                #         existing_data = json.load(file)
                # else:
                #     existing_data = []

                # existing_data.append(poke_json)
                # with open(filename, "w") as outfile:
                #     json.dump(existing_data, outfile)

        
            time.sleep(2)
        db.commit()
    else:
        print("Response request unsuccessful. Status Code", response.status_code)    


def moveDetailsReader(db):
    response = requests.get(f"{base_url}/move/?limit={MAX_MOVES}")
    if response.status_code == 200:
        cursor = db.cursor()

        move_data = response.json() # move info
        for move_id in move_data["results"]:
            move_name = move_id["name"]
            move_response = requests.get(f"{base_url}/move/{move_name}")

            relevent_pokemon = [pokemon for pokemon in move_response["learned_by_pokemon"]
                                if int(re.search(r"/pokemon/(\d+)/", pokemon["url"]).group(1)) < MAX_POKEMON] # empty if no original pokemon can learn this move
            if relevent_pokemon and len(move_response["effect_entries"]) > 0: # check for non-null effects
                # insert into moves table
                temp = move_response["effect_entries"][0]
                effect = temp["effect"]
                short_effect = temp["short_effect"]
                power = move_response["power"]
                accuracy = move_response["accuracy"]
                name = move_response["name"]
                target = move_response["target"]["name"]
                type = move_response["type"]["name"]
                id = move_response["id"]

                insert_query = "INSERT INTO moves (id, name, type, power, accuracy, effect, short_effect, target) VALUES (%d, %s, %s, %d, %d, %s, %s, %s)"
                moves_values = (id, name, type, power, accuracy, effect, short_effect, target)
                cursor.execute(insert_query, moves_values)
                
            time.sleep(2)
        db.commit()
    else:
        print("Categorize moves request unsuccessful. Status Code", response.status_code)
    time.sleep(2)
        

def main():
    try:
        db = mysql.connector.connect(
                user = os.environ.get('DB_USER'),
                password = os.environ.get('DB_PASSWORD'),
                host = os.environ.get('DB_HOST'),
                port = 3306,
                database = os.environ.get('DB_DATABASE')
            )
        print("Successful connection")

        pokemonLearnReader(db)
        # moveDetailsReader(db)

        db.close()
    except mysql.connector.Error as err:
        print("Error connecting to MySQL:", err)


if __name__ == "__main__":
    main()