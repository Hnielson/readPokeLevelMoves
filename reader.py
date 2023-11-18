import requests

MAX_POKEMON = 251

base_url = "https://pokeapi.co/api/v2/"
endpoint = "pokemon/1"
move_category = "move-category/"
drill = "move"

url = base_url + endpoint
# url = base_url + move_category
# url = base_url + drill
response = requests.get(url)

if response.status_code == 200:
    poke_data = response.json()["moves"]
    level = []
    machine = []
    tutor = []
    egg = []
    for move in poke_data:
        name = move["version_group_details"][0]["move_learn_method"]["name"]
        move_name = move["move"]["name"]
        if name == "egg":
            egg.append(move_name)
        if name == "machine":
            machine.append(move_name)
        if name == "tutor":
            tutor.append(move_name)
        if move["version_group_details"][0]["level_learned_at"] > 0:
            level.append(move_name)
    print("--level--", *level, sep='\n')
    print('\n', "--machine--", *machine, sep='\n')
    print('\n', "--egg--", *egg, sep='\n')
    print('\n', "--tutor--", *tutor, sep='\n')

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
