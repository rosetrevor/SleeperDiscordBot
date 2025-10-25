from dotenv import load_dotenv
import os
import requests
import time

from curl_extractor import extract_curl_data
from espn import get_matchup_timestamps
from sql_tables import Player, Manager, ManagerScore, Transaction, Roster


def get_week():
    endpoint = "https://api.sleeper.app/v1/state/nfl"
    r = requests.get(endpoint)
    response = r.json()
    return response["week"]


def get_all_players():
    players = {}
    endpoint = "https://api.sleeper.app/v1/players/nfl"
    r = requests.get(endpoint)
    player_dict = r.json()
    for player_id, player in player_dict.items():
        players[str(player_id)] = player
    return players

def get_scoring_settings() -> dict[str, str]:
    load_dotenv()
    league_id = os.getenv("SLEEPER_LEAGUE_ID")

    endpoint = f"https://api.sleeper.app/v1/league/{league_id}"
    r = requests.get(endpoint)
    league = r.json()
    return league["scoring_settings"]

def get_managers() -> list[Manager]:
    load_dotenv()
    league_id = os.getenv("SLEEPER_LEAGUE_ID")
    
    endpoint = f"https://api.sleeper.app/v1/league/{league_id}/users"
    r = requests.get(endpoint)
    
    managers = []
    for user in r.json():
        manager = Manager(
            manager_id = user["user_id"],
            display_name = user["display_name"],
            team_name = user["metadata"].get("team_name", user["display_name"]),
            avatar = user.get("avatar", None),
            avatar_url = user["metadata"].get("avatar", None),
            league_id = user["league_id"]
        )
        managers.append(manager)
    return managers

def get_manager_matchups(week: int = 1):
    load_dotenv()
    league_id = os.getenv("SLEEPER_LEAGUE_ID")
    endpoint = f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}"
    r = requests.get(endpoint)
    return r.json()

def get_transactions_by_week(week: int = 1):
    load_dotenv()
    league_id = os.getenv("SLEEPER_LEAGUE_ID")

    endpoint = f"https://api.sleeper.app/v1/league/{league_id}/transactions/{week}"
    r = requests.get(endpoint)

    transactions = []
    for trade in r.json():
        # TODO: This is a short term hack, players added should be a list for trades
        added = trade["adds"] if trade["adds"] is None else list(trade["adds"].keys())[0]
        dropped = trade["drops"] if trade["drops"] is None else list(trade["drops"].keys())[0]
        settings = trade["settings"] if isinstance(trade["settings"], dict) else {}
        transaction = Transaction(
            transaction_id = trade["transaction_id"],
            manager_id = trade["creator"],
            consenter_id = None,
            status = trade["status"],
            transaction_type = trade["type"],
            week = trade["leg"],
            player_added = added,
            player_dropped = dropped,
            sequence = settings.get("seq", None),
            waiver_bid = settings.get("waiver_bid", None)
        )
        transactions.append(transaction)
    return transactions

def get_rosters():
    load_dotenv()
    league_id = os.getenv("SLEEPER_LEAGUE_ID")
    
    endpoint = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    response = requests.get(endpoint)
    refresh_time = int(time.time())

    rosters = []
    for r in response.json():
        stats = r["settings"]
        roster = Roster(
            roster_id=r["roster_id"],
            manager_id=r["owner_id"],
            players=r["players"],
            starters=r["starters"],
            reserve=r["reserve"],
            streak=r["metadata"]["streak"],
            wins=stats["wins"],
            losses=stats["losses"],
            ties=stats["ties"],
            points_for=float(f"{stats['fpts']}.{stats['fpts_decimal']}"),
            points_against=float(f"{stats['fpts_against']}.{stats['fpts_against_decimal']}"),
            potential_points=float(f"{stats['ppts']}.{stats['ppts_decimal']}"),
            total_moves=stats["total_moves"],
            waiver_budget_used=stats["waiver_budget_used"],
            waiver_position=stats["waiver_position"],
            refreshed_on=refresh_time
        )
        rosters.append(roster)
    return rosters

def get_game_statuses(week: int):
    url, headers = extract_curl_data()
    url = "https://api.sleeper.com/schedule/nfl/regular/2025"
    
    response = requests.request("GET", url)
    print(response.status_code)
    response = response.json()
    teams = {}

    for game in response:
        if game["week"] == week:
            teams[game["home"]] = game["status"]
            teams[game["away"]] = game["status"]
    return teams

def get_projected_scores(roster: Roster):
    url, headers = extract_curl_data()
    url = "https://sleeper.com/graphql"
    week = get_week()
    
    player_id_str = "["
    for player_id in roster.players:
        player_id_str += "\\\"" + player_id + "\\\""
    player_id_str += "]"

    payload = "{\"query\":\"query get_player_score_and_projections_batch {\\n        \\n        nfl__regular__2025__4__stat: stats_for_players_in_week(sport: \\\"nfl\\\",season: \\\"2025\\\",category: \\\"stat\\\",season_type: \\\"regular\\\",week: "
    payload += f"{week},player_ids: {player_id_str}"
    payload += "){\\n          game_id\\nopponent\\nplayer_id\\nstats\\nteam\\nweek\\nseason\\n        }\\n      \\n\\n        nfl__regular__2025__4__proj: stats_for_players_in_week(sport: \\\"nfl\\\",season: \\\"2025\\\",category: \\\"proj\\\",season_type: \\\"regular\\\",week: "
    payload += f"{week},player_ids: {player_id_str}"
    payload += "){\\n          game_id\\nopponent\\nplayer_id\\nstats\\nteam\\nweek\\nseason\\n        }\\n      \\n      }\",\"variables\":{}}"

    response = requests.request("POST", url, headers=headers, data=payload)
    response = response.json()
    refresh_time = int(time.time())
    
    scoring_settings = get_scoring_settings()
    projections = get_player_projected_scores()  # TODO: Really shouldn't call this for every manager
    projections = {p["player_id"]: p for p in projections}

    matchups = get_matchup_timestamps()

    player_stats = {player["player_id"]: player for player in response["data"]["nfl__regular__2025__4__stat"]}
    player_projs = {player["player_id"]: player for player in response["data"]["nfl__regular__2025__4__proj"]}

    def apply_scoring(score_settings, _stats):
        _score = 0
        for category, projection in _stats.items():
            try:
                _score += scoring_settings.get(category, 0) * projection
            except TypeError:
                pass
        if stats.get("fga", 0) > 0.1:  # Attempting more than .1 field goals means they are a kicker
            # TODO: Kickers still don't align perfectly, but it's close enough I'm over it for now
            _score += score_settings.get("fgmiss", 0) * (stats["fga"] - stats["fgm"]) * 0
            _score += score_settings.get("xpmiss", 0) * (stats["xpa"] - stats["xpm"]) * 0  # TODO: Does this apply?
        return _score
        
    manager_projected_score = 0
    for player_id in roster.starters:
        try:
            stats = projections[player_id]["stats"]
            # stats = player_projs[player]
        except KeyError:
            # Means the player is on a bye
            continue
        projected_score = 0
        in_game = False
        if matchups[projections[player_id]["team"]]["in_progress"]:
            in_game = True
        projected_score = apply_scoring(scoring_settings, stats)
        if in_game:
            # Interpolate by time left in match
            multiplier = matchups[projections[player_id]["team"]]["time_remaining"] / 60
            player_current_score = apply_scoring(scoring_settings, player_stats[player_id]["stats"])
            projected_score = projected_score * multiplier + player_current_score
        manager_projected_score += projected_score

    manager_current_score = 0
    for player_id in roster.starters:
        try:
            player = player_stats[player_id]
        except KeyError:
            # Means the player is on a bye
            continue
        stats = player["stats"]
        try:
            manager_current_score += apply_scoring(scoring_settings, stats)
        except KeyError:
            print(f"KeyError: {player['player_id']} has no attribute pts_half_ppr for manager {roster.manager_id}")

    manager_score = ManagerScore(
        manager_id = roster.manager_id,
        timestamp = refresh_time,
        projected_score = manager_projected_score,
        current_score = manager_current_score
    )
    return manager_score

def get_player_projected_scores():
    endpoint = "https://api.sleeper.app/projections/nfl/2025/8?season_type=regular&position[]=DB&position[]=DEF&position[]=DL&position[]=FLEX&position[]=IDP_FLEX&position[]=K&position[]=LB&position[]=QB&position[]=RB&position[]=REC_FLEX&position[]=SUPER_FLEX&position[]=TE&position[]=WR&position[]=WRRB_FLEX&order_by=ppr"

    response = requests.get(endpoint)

    return response.json()


def update_players():
    db_helper = DatabaseHelper()
    get_all_players(db_helper)
    
    count = 0
    outer_count = 0
    for player, player_info in players.items():
        try:
            player_info["weight"] = int(player_info.get("weight", None))
        except (ValueError, TypeError):
            player_info["weight"] = None
        player = Player(player_info)
        db_helper.db_session.add(player)
        count += 1
        if count > 999:
            db_helper.db_session.commit()
            count = 0
            outer_count += 1
            print(f"Committed {outer_count * 1000} players!")
    db_helper.db_session.commit()
    print(f"Committed {outer_count * 1000 + count} players!")


if __name__ == "__main__":
    from db_helper import DatabaseHelper
    db = DatabaseHelper()
    # # get_rosters(db)
    # #managers = get_managers(db)
    # #print(managers) 
    # transactions = get_transactions_by_week(week=4)
    # for transaction in transactions:
    #     print(db.display_transaction(transaction))

    results = db.db_session.query(Manager).join(Roster).add_columns(Roster)
    for manager, roster in results:
        manager_score = get_projected_scores(roster)
        print(manager, manager_score.projected_score, manager_score.current_score)
    # print(get_game_statuses(8))

