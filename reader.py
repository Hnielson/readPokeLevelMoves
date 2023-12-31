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

def pokemonLearnReader(db):
    # get MAX_POKEMON
    response = requests.get(f"{base_url}/pokemon/?limit={MAX_POKEMON}")
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
                type2 = poke_info["types"][1]["type"]["name"] if len(poke_info["types"]) > 1 else None
                stats = poke_info["stats"]
                attack = stats[1]["base_stat"]
                spattack = stats[3]["base_stat"]
                name = poke_info["name"]
                moves = poke_info["moves"]
                # print(f"{type1}, {type2}, {attack}, {spattack}, {name}")

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
                # make by_level, etc., a json dump
                level_json = json.dumps(by_level)
                machine_json = json.dumps(by_machine)
                tutor_json = json.dumps(by_tutor)
                egg_json = json.dumps(by_egg)
                insert_query = "INSERT INTO pokemon (name, attack, spattack, by_level, by_machine, by_tutor, by_breeding, type1, type2) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                pokemon_values = (name, attack, spattack, level_json, machine_json, tutor_json, egg_json, type1, type2)
                try:
                    cursor.execute(insert_query, pokemon_values)
                except mysql.connector.Error as err:
                    print("didn't have all parameters:", err)

        
            time.sleep(1)
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
            if move_response.status_code == 200:
                move_info = move_response.json()
                relevent_pokemon = [pokemon["name"] for pokemon in move_info["learned_by_pokemon"]
                                    if int(re.search(r"/pokemon/(\d+)/", pokemon["url"]).group(1)) < MAX_POKEMON] # empty if no original pokemon can learn this move
                if len(relevent_pokemon) > 0 and len(move_info["effect_entries"]) > 0: # check for non-null effects
                    # insert into moves table
                    temp = move_info["effect_entries"][0]
                    effect = temp["effect"]
                    short_effect = temp["short_effect"]
                    power = move_info["power"]
                    accuracy = move_info["accuracy"]
                    name = move_info["name"]
                    target = move_info["target"]["name"]
                    type = move_info["type"]["name"]
                    id = move_info["id"]

                    insert_query = "INSERT INTO moves (id, name, type, power, accuracy, effect, short_effect, target) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    moves_values = (id, name, type, power, accuracy, effect, short_effect, target)
                    cursor.execute(insert_query, moves_values)
                
            time.sleep(1)
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
        moveDetailsReader(db)
        db.close()
    except mysql.connector.Error as err:
        print("Error connecting to MySQL:", err)


if __name__ == "__main__":
    main()