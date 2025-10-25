from dotenv import load_dotenv
import os
import sqlalchemy as sql
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
import time

from espn import get_matchup_timestamps
from sleeper import get_rosters
from sql_tables import Base, ManagerScore, Player, Manager, Transaction, Roster

class DatabaseHelper:
    def __init__(self):
        self.db_session: Session = None
        self.db_engine: Engine = self.create_engine()
        self.db_metadata = sql.MetaData()
        self.db_metadata.reflect(bind=self.db_engine)
        Base.metadata.create_all(self.db_engine)

    def create_engine(self, drivername: str="postgresql", port: int=5432, host: str="localhost", db_name: str="sleeper_db") -> Engine:
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

    def get_managers_and_rosters(self) -> list[tuple[Manager, Roster]]:
        """
        Get all managers and their rosters.
        """
        q = self.db_session.query(Manager)
        q = q.join(Roster, Manager.manager_id == Roster.manager_id)
        q = q.add_columns(Roster)
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

    def display_roster(self, roster: Roster, manager: Manager | None = None):
        if manager is None:
            manager = self.get_manager(roster.manager_id)
        q = self.db_session.query(Manager)
        q = q.where(Manager.manager_id == roster.manager_id)
        q = q.join(ManagerScore, ManagerScore.manager_id == Manager.manager_id)
        q = q.order_by(ManagerScore.timestamp.desc())
        q = q.add_columns(ManagerScore)
        manager, manager_score = q.first()

        players = self.get_players_by_ids(roster.players)
        player_map: dict[int, Player] = {player.player_id: player for player in players}

        display_roster = f"## **{manager.team_name}** ({manager_score.current_score:.2f} / *{manager_score.projected_score:.2f}*)\n"
        for player in roster.starters:
            try:
                display_roster += f"{player_map[player]}\n"
            except KeyError:
                display_roster += f"[    ] - Empty\n"

        bench = set(roster.players).difference(set(roster.starters))
        for player in bench:
            try:
                display_roster += f"[BN] {player_map[player].full_name}\n"
            except KeyError:
                display_roster += f"[    ] - Empty\n"
        return display_roster

    def update_rosters(self, rosters: list[Roster] | None = None, commit: bool = True) -> str | None:
        if rosters is None: 
            live_rosters = get_rosters()
        else:
            live_rosters = rosters
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
                        try:
                            late_starter_str += self.check_late_starter_swap(started, benched, live_roster.manager_id)
                        except Exception:
                            # This is a non-critical part of the code. We never want to block on this.
                            # TODO: Should setup a real logger and add logging here
                            print(f"Failed to check late starter swap for manager {live_roster.manager_id}")
                            pass

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
        player_swap_str = f"🚨 Late move alert by {manager.display_name} 🚨\n  Started:\n"
        late_swap = False
        for started_player in started_players:
            game_time = matchup_timestamps[started_player.team]["timestamp"]
            current_time = time.time()
            delta_time = game_time - current_time
            if abs(delta_time) < late_starter_threshold:
                late_swap = True
            player_swap_str += f"    \\- {started_player}" + "\n"
        player_swap_str += "  Benched:\n"
        for benched_player in benched_players:
            game_time = matchup_timestamps[benched_player.team]["timestamp"]
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

    results = db.get_managers_and_rosters()
    for manager, roster in results:
        print(db.display_roster(roster))

