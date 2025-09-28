from dotenv import load_dotenv
import json
import os
import requests
import time
import datetime

from curl_extractor import extract_curl_data
from sql_tables import Player, Manager, ManagerScore, Transaction, Roster
from constants import SLEEPER_APP_BASE_URL


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
    
    manager_projected_score = 0
    for player in response["data"]["nfl__regular__2025__4__proj"]:
        if player["player_id"] in roster.starters:
            manager_projected_score += float(player["stats"]["pts_half_ppr"])

    manager_current_score = 0
    for player in response["data"]["nfl__regular__2025__4__stat"]:
        if player["player_id"] in roster.starters:
            try:
                manager_current_score += float(player["stats"]["pts_half_ppr"])
            except KeyError:
                print(f"KeyError: {player['player_id']} has no attribute pts_half_ppr for manager {roster.manager_id}")

    manager_score = ManagerScore(
        manager_id = roster.manager_id,
        timestamp = refresh_time,
        projected_score = manager_projected_score,
        current_score = manager_current_score
    )
    return manager_score

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
    # get_rosters(db)
    #managers = get_managers(db)
    #print(managers) 
    transactions = get_transactions_by_week(week=4)
    for transaction in transactions:
        print(db.display_transaction(transaction))

