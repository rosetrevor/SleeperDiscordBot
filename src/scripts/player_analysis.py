import json

def main():
    with open("src/players.json") as file:
        players = json.load(file)

    attributes = {}
    for player, _attributes in players.items():
        for attribute in _attributes.keys():
            if not attributes.get(attribute, False):
                attributes[attribute] = 1
            else:
                attributes[attribute] += 1
    
            if attribute == "metadata":
                if _attributes[attribute] is not None:
                    print(_attributes[attribute])
    # alphabetized_attrs = list(attributes.keys())
    # alphabetized_attrs = sorted(alphabetized_attrs)
    # for attr in alphabetized_attrs:
    #    print(attr, attributes[attr])


if __name__ == "__main__":
    main()
