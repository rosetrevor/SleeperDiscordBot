from dotenv import load_dotenv
import os
import sqlalchemy as sql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import time

from espn import get_matchup_timestamps
from sleeper import get_rosters
from sql_tables import Base, Player, Manager, Transaction, Roster

class DatabaseHelper:
    def __init__(self):
        self.db_session = None
        self.db_engine = self.create_engine()
        self.db_metadata = sql.MetaData()
        self.db_metadata.reflect(bind=self.db_engine)
        Base.metadata.create_all(self.db_engine)

    def create_engine(self, drivername: str="postgresql", port: int=5432, host: str="localhost", db_name: str="sleeper_db"):
        load_dotenv()
        db_url = sql.URL.create(
            drivername=drivername,
            username=os.getenv("SLEEPER_DB_USERNAME"),
            password=os.getenv("SLEEPER_DB_PASSWORD"),
            host=host,
            port=port,
            database=db_name
        )
        _engine = create_engine(db_url)
        _session = sessionmaker(_engine)
        self.db_session = _session()
        return _engine

    def get_player(self, player_id) -> Player:
        """
        Get a player by their ID
        """
        q = self.db_session.query(Player)
        q = q.where(Player.player_id == player_id)
        return q.first()

    def get_players_by_ids(self, player_ids: list[str]) -> list[Player]:
        """
        Pass a list of player IDs, get a list of corresponding player objects
        """
        q = self.db_session.query(Player)
        q = q.where(Player.player_id.in_(player_ids))
        return q.all()

    def get_manager(self, manager_id) -> Manager:
        """
        Get a manager by their ID
        """
        q = self.db_session.query(Manager)
        q = q.where(Manager.manager_id == manager_id)
        return q.first()

    def get_all_managers(self) -> list[Manager]:
        """
        Get a list of managers for the league.
        """
        q = self.db_session.query(Manager)
        return q.all()

    def get_rosters(self) -> list[Roster]:
        """
        Get a list of rosters for the league.
        """
        q = self.db_session.query(Roster)
        return q.all()

    def get_transactions_by_week(self, week: int) -> list[Transaction]:
        """
        Get a list of databased transactions for a given week.
        """
        q = self.db_session.query(Transaction)
        q = q.where(Transaction.week == week)
        return q.all()

    def display_transaction(self, transaction: Transaction):
        manager = self.get_manager(transaction.manager_id)
        add_player = self.get_player(transaction.player_added)
        drop_player = self.get_player(transaction.player_dropped)
        top_line = f"{manager.display_name}\n"                              
        mid_line = f"  + {add_player}\n"
        bot_line = f"  \\- {drop_player}"
        if transaction.transaction_type == "waiver" and transaction.status == "complete":
            top_line = f"{manager.display_name} (${transaction.waiver_bid})\n"
        elif transaction.transaction_type == "waiver" and transaction.status == "failed":
            return ""
        return top_line + mid_line + bot_line

    def update_rosters(self, rosters: list[Roster], commit: bool = True) -> str | None:
        live_rosters = get_rosters()
        db_rosters = self.get_rosters()
        refresh_time = int(time.time())

        comparison_fields = [
            "players",
            "starters",
            "reserve",
            "streak",
            "wins",
            "losses",
            "ties",
            "points_for",
            "points_against",
            "potential_points",
            "total_moves",
            "waiver_budget_used"
        ]
        late_starter_str = ""
        for live_roster in live_rosters:
            compared_roster = False
            for db_roster in db_rosters:
                if live_roster.roster_id == db_roster.roster_id:
                    compared_roster = True 
                    differing_fields = []
                    identical = True 
                    for field in comparison_fields:
                        if not getattr(live_roster, field) == getattr(db_roster, field):
                            differing_fields.append(field)

                    if "starters" in differing_fields:
                        live_starters = set(live_roster.starters)
                        db_starters = set(db_roster.starters)
                        started = live_starters.difference(db_starters)
                        benched = db_starters.difference(live_starters)
                        late_starter_str += self.check_late_starter_swap(started, benched, live_roster.manager_id)

                    for field in differing_fields:
                        setattr(db_roster, field, getattr(live_roster, field))
                        db_roster.refreshed_on = refresh_time
            if not compared_roster:
                # Means there's nothing matching in the DB
                self.db_session.add(live_roster)

        if commit:
            self.db_session.commit()

        if len(late_starter_str) > 0:
            return late_starter_str

    def check_late_starter_swap(self, started_ids, benched_ids, manager_id, late_starter_threshold: int = 600):
        matchup_timestamps = get_matchup_timestamps()
        manager = self.get_manager(manager_id)
        started_players = self.get_players_by_ids(started_ids)
        benched_players = self.get_players_by_ids(benched_ids)
        player_swap_str = f"Boldly late move by {manager.display_name}:\n  Started:\n"
        late_swap = False
        for started_player in started_players:
            game_time = matchup_timestamps[started_player.team]
            current_time = time.time()
            delta_time = game_time - current_time
            if abs(delta_time) < late_starter_threshold:
                late_swap = True
            player_swap_str += f"    \\- {started_player}" + "\n"
        player_swap_str += "  Benched:\n"
        for benched_player in benched_players:
            game_time = matchup_timestamps[benched_player.team]
            current_time = time.time()
            delta_time = game_time - current_time
            if abs(delta_time) < late_starter_threshold:
                late_swap = True  
            player_swap_str += f"    \\- {benched_player}" + "\n"
        if late_swap:
            return player_swap_str
        else:
            return ""
 

if __name__ == "__main__":
    db = DatabaseHelper()
    transactions = db.get_transactions_by_week(4)
    for transaction in transactions:
        print(transaction.transaction_id)
