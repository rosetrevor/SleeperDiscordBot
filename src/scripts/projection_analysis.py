import os
import requests

from curl_extractor import extract_curl_data

def main():
    cwd = os.getcwd()

    url, headers = extract_curl_data()

    url = "https://sleeper.com/graphql"

    week = 4
    player_ids = ["5849", "12507", "12512", "6794", "11620", "8130", "7564", "8146", "7591", "11786", "MIN", "3294", "11576", "12489", "12533", "9753", "12514", "8110", "6803"]

    player_id_str = "["
    for player_id in player_ids:
        player_id_str += "\\\"" + player_id + "\\\""
    player_id_str += "]"

    payload = "{\"query\":\"query get_player_score_and_projections_batch {\\n        \\n        nfl__regular__2025__4__stat: stats_for_players_in_week(sport: \\\"nfl\\\",season: \\\"2025\\\",category: \\\"stat\\\",season_type: \\\"regular\\\",week: "
    payload += f"{week},player_ids: {player_id_str}"
    payload += "){\\n          game_id\\nopponent\\nplayer_id\\nstats\\nteam\\nweek\\nseason\\n        }\\n      \\n\\n        nfl__regular__2025__4__proj: stats_for_players_in_week(sport: \\\"nfl\\\",season: \\\"2025\\\",category: \\\"proj\\\",season_type: \\\"regular\\\",week: "
    payload += f"{week},player_ids: {player_id_str}"
    payload += "){\\n          game_id\\nopponent\\nplayer_id\\nstats\\nteam\\nweek\\nseason\\n        }\\n      \\n      }\",\"variables\":{}}"


    print(payload)
    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)



if __name__ == "__main__":
    main()
