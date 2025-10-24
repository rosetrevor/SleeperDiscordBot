from datetime import datetime
import requests
import re

def get_matchup_timestamps() -> dict[str, dict[str, datetime | bool | float]]:
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
        status = event.get("status", {})
        in_progress = status.get("type", {}).get("state", False) in ["in", "post"]
        display_clock = status.get("displayClock", "0:00")
        quarter = status.get("period", 0)
        mins_seconds = [int(substr) for substr in display_clock.split(":")]
        time_remaining = mins_seconds[0] + mins_seconds[1] / 60 + (4 - quarter) * 15
        for team in teams:
            if team == "WSH":
                team = "WAS"
            game_times[team] = {
                "timestamp": event_datetime.timestamp(),
                "in_progress": in_progress,
                "time_remaining": time_remaining
            }
    return game_times

if __name__ == "__main__":
    game_times = get_matchup_timestamps()
    for game, details in game_times.items():
        print(game, details)


