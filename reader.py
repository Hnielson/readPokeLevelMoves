import json
import requests

MAX_POKEMON = 251
FIRERED_GEN = 7

base_url = "https://pokeapi.co/api/v2/"
endpoint = "pokemon"
move_category = "move-category/"
drill = "move"

url = base_url + endpoint
# url = base_url + move_category
# url = base_url + drill
response = requests.get(url)

if response.status_code == 200:
    # poke_data = response.json()["moves"]
    poke_data = response.json()["results"]
    # print(json.dumps(poke_data, indent=4))
    
    pokemon_subset = [pokemon for pokemon in poke_data[:10]]
    # for move in poke_data:
    for pokemon in pokemon_subset:
        poke_name = pokemon["name"]
        moves = requests.get(pokemon["url"]).json()["moves"]
        level = []
        level_count = {}
        machine = []
        machine_count = {}
        tutor = []
        tutor_count = {}
        egg = []
        egg_count = {}
        for move in moves:
            name = move["version_group_details"]
            move_name = move["move"]["name"]
            for i in name:
                name_subset = i["move_learn_method"]["name"]
                if name_subset == "egg":
                    if move_name in egg:
                        egg_count[move_name] += 1
                    else:  
                        egg.append(move_name)
                        egg_count[move_name] = 1
                if name_subset == "machine":
                    if move_name in machine:
                        machine_count[move_name] += 1
                    else:
                        machine.append(move_name)
                        machine_count[move_name] = 1
                if name_subset == "tutor":
                    if move_name in tutor:
                        tutor_count[move_name] += 1
                    else:
                        tutor.append(move_name)
                        tutor_count[move_name] = 1
                if i["level_learned_at"] > 0:
                    if move_name in level:
                        level_count[move_name] += 1
                    else:
                        level.append(move_name)
                        level_count[move_name] = 1

        print(f'\n--{poke_name}--')
        print('\n--level--', *((k, v) for k, v in level_count.items()), sep='\n')
        print('\n--machine--', *((i, machine_count[i]) for i in machine_count), sep='\n')
        print('\n--tutor--', *((k, tutor_count[k]) for k in tutor_count), sep='\n')
        print('\n--egg--', *((k, egg_count[k]) for k in egg_count), sep='\n')

    

# download all pokemon 1-251
#   download all moves that each can learn
#   separate moves by:
#       egg
#       tutor
#       level
#       machine
#   count through all instances of moves and add to list with most hits

    # -- for move short_effects -- 
    # moves_data = response.json()["results"]
    # moves_short_effect = [
    #     (move_data["name"], requests.get(move_data["url"]).json()["effect_entries"][0]["short_effect"]) 
    #     for move_data in moves_data 
    #     if requests.get(move_data["url"]).status_code == 200
    # ]
    # print(*((move_name, short_effect) for (move_name, short_effect) in moves_short_effect), sep='\n')

else:
    print("Request unsuccessful. Status Code", response.status_code)
