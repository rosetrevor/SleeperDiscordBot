from datetime import datetime
import requests
import re

def get_matchup_timestamps() -> dict[str, str]:
    # https://github.com/stylo-stack/ESPN-API-Documentation/blob/master/endpoints.txt
    endpoint = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    r = requests.get(endpoint)
    response = r.json()
    
    split_regex = "@|VS"
    game_times = {}
    for event in response["events"]:
        event_name = event["shortName"].upper().replace(" ", "")
        teams = re.split(split_regex, event_name)
        event_datetime = event["date"].replace("T", " ").replace("Z", "")
        format_string = "%Y-%m-%d %H:%M"
        event_datetime = datetime.strptime(event_datetime, format_string)
        for team in teams:
            if team == "WSH":
                game_times["WAS"] =  event_datetime.timestamp()
            game_times[team] = event_datetime.timestamp()
    return game_times

if __name__ == "__main__":
    game_times = get_matchup_timestamps()
    print(game_times)
