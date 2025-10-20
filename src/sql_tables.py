import numpy as np
import time
import sqlalchemy as sql
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"

    player_id: Mapped[str] = mapped_column(sql.Text, primary_key=True, unique=True)
    full_name: str = sql.Column(sql.Text)
    first_name: str = sql.Column(sql.Text)
    last_name: str = sql.Column(sql.Text)
    fantasy_positions: list[str] = sql.Column(sql.ARRAY(sql.Text))
    position: str = sql.Column(sql.Text)
    team_abbr: str = sql.Column(sql.Text)
    team: str = sql.Column(sql.Text)
    status: str = sql.Column(sql.Text)
    number: str = sql.Column(sql.Integer)
    height: str = sql.Column(sql.Text)
    weight: str = sql.Column(sql.Float)
    years_exp: int = sql.Column(sql.Integer)
    depth_chart_order: int = sql.Column(sql.Integer)

    injury_notes: str = sql.Column(sql.Text)
    injury_body_part: str = sql.Column(sql.Text)
    injury_status: str = sql.Column(sql.Text)
    news_updated: int = sql.Column(sql.BigInteger) 

    college: str = sql.Column(sql.Text)
    high_school: str = sql.Column(sql.Text)
    birth_city: str = sql.Column(sql.Text)
    birth_state: str = sql.Column(sql.Text)
    birth_country: str = sql.Column(sql.Text)
    birth_date: str = sql.Column(sql.Text)

    search_rank: int = sql.Column(sql.Integer)

    refreshed_on: int = sql.Column(sql.BigInteger)


    def __init__(self, player_attributes: dict, refreshed_on: int = None) -> None:
        attributes = [
            "player_id",
            "full_name",
            "first_name",
            "last_name",
            "fantasy_positions",
            "position",
            "team_abbr",
            "team",
            "status",
            "number",
            "height",
            "weight",
            "years_exp",
            "depth_chart_order",
            "injury_notes",
            "injury_body_part",
            "injury_status",
            "news_updated",
            "college",
            "high_school",
            "birth_city",
            "birth_state",
            "birth_country",
            "birth_date",
            "seach_rank"
        ]

        for _attr in attributes:
            setattr(self, _attr, player_attributes.get(_attr, None))

        if refreshed_on is None:
            self.refreshed_on = int(time.time())
        else:
            self.refreshed_on = refreshed_on

    def __repr__(self) -> str:
        return f"[{self.position}] {self.first_name} {self.last_name}"


class Manager(Base):
    __tablename__ = "managers"

    manager_id: int = sql.Column(sql.BigInteger, primary_key = True)
    display_name: str = sql.Column(sql.Text)
    team_name: str = sql.Column(sql.Text)
    avatar: str = sql.Column(sql.Text)
    avatar_url: str = sql.Column(sql.Text)
    league_id: str = sql.Column(sql.Text)
    wins: int = sql.Column(sql.Integer)
    losses: int = sql.Column(sql.Integer)
    points_for: float = sql.Column(sql.Float)
    points_against: float = sql.Column(sql.Float)
    dev_transaction_channel_id: int = sql.Column(sql.BigInteger)
    transaction_channel_id: int = sql.Column(sql.BigInteger)
    dev_transaction_message_id: int = sql.Column(sql.BigInteger)
    transaction_message_id: int = sql.Column(sql.BigInteger)

    def __init__(self, manager_id: int, display_name: str, team_name: str, avatar: str, avatar_url: str, league_id: str, wins: int = 0, losses: int = 0, points_for: float = 0, points_against: float = 0):
        self.manager_id = manager_id
        self.display_name = display_name
        self.team_name = team_name
        self.avatar = avatar
        self.avatar_url = avatar_url
        self.league_id = league_id
        self.wins = wins
        self.losses = losses
        self.points_for = points_for
        self.points_against = points_against

    def __repr__(self):
        #if not (self.wins == 0 and self.losses == 0):
        #    return f"{self.display_name}"
        #else:
        #    return f"{self.wins}-{self.losses} - {self.display_name}"
        return self.display_name


class ManagerScore(Base):
    __tablename__ = "manager_scores"
    manager_id: int = sql.Column(sql.BigInteger, primary_key = True)
    timestamp: int = sql.Column(sql.BigInteger, primary_key = True)
    projected_score: float = sql.Column(sql.Float)
    current_score: float = sql.Column(sql.Float)

    def __init__(self, manager_id: int, timestamp: int, projected_score: float, current_score: float) -> None:
        self.manager_id = manager_id
        self.timestamp = timestamp
        self.projected_score = projected_score
        self.current_score = current_score

    def __repr__(self):
        return f"Manager {self.manager_id} at {self.timestamp}: {self.current_score} (Proj: {self.projected_score})"


class Transaction(Base):
    __tablename__ = "transactions"
    
    transaction_id: int = sql.Column(sql.BigInteger, primary_key = True)
    manager_id: int = sql.Column(sql.BigInteger, sql.ForeignKey("managers.manager_id"))
    consenter_id: int = sql.Column(sql.BigInteger, sql.ForeignKey("managers.manager_id"))

    status: str = sql.Column(sql.Text)
    transaction_type: str = sql.Column(sql.Text)
    week: int = sql.Column(sql.Integer)

    player_added: str = sql.Column(sql.Text, sql.ForeignKey("players.player_id"))
    player_dropped: str = sql.Column(sql.Text, sql.ForeignKey("players.player_id"))
    sequence: int = sql.Column(sql.Integer)
    waiver_bid: int = sql.Column(sql.Integer)

    def __init__(self, transaction_id: int, manager_id: int, status: str, transaction_type: str, week: int, player_added: str, player_dropped: str, consenter_id: str = None, sequence: int = 0, waiver_bid: int = 0):
        self.transaction_id = transaction_id
        self.manager_id = manager_id
        self.consenter_id = consenter_id
        self.status = status
        self.transaction_type = transaction_type
        self.week = week
        self.player_added = player_added
        self.player_dropped = player_dropped
        self.sequence = sequence
        self.waiver_bid = waiver_bid


class Roster(Base):
    __tablename__ = "rosters"
    roster_id: int = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    manager_id: int = sql.Column(sql.BigInteger, sql.ForeignKey("managers.manager_id"))
    players: list[str] = sql.Column(sql.ARRAY(sql.Text))
    starters: list[str] = sql.Column(sql.ARRAY(sql.Text))
    reserve: list[str] = sql.Column(sql.ARRAY(sql.Text))

    streak: str = sql.Column(sql.Text)
    wins: int = sql.Column(sql.Integer)
    losses: int = sql.Column(sql.Integer)
    ties: int = sql.Column(sql.Integer)
    points_for: float = sql.Column(sql.FLOAT)
    points_against: float = sql.Column(sql.FLOAT)
    potential_points: float = sql.Column(sql.FLOAT)
    total_moves: int = sql.Column(sql.Integer)
    waiver_budget_used: int = sql.Column(sql.Integer)
    waiver_position: int = sql.Column(sql.Integer)
    refreshed_on: int = sql.Column(sql.BigInteger)

    def __init__(self, roster_id: int, manager_id: int, players: list[str], starters: list[str], reserve: list[str], streak: str, wins: int, losses: int, ties: int, points_for: float, points_against: float, potential_points: float, total_moves: int, waiver_budget_used: int, waiver_position: int, refreshed_on: int): 
        self.roster_id = roster_id 
        self.manager_id = manager_id
        self.players = players
        self.starters = starters
        self.reserve = reserve
        self.streak = streak
        self.wins = wins
        self.losses = losses
        self.ties = ties
        self.points_for = points_for
        self.points_against = points_against
        self.potential_points = potential_points
        self.total_moves = total_moves
        self.waiver_budget_used = waiver_budget_used
        self.waiver_position = waiver_position
        self.refreshed_on = refreshed_on


"""
# This would make roster queries easier
class RosterPlayers(Base):
    __tablename__ = "roster_players"

    roster_id: int = sql.Column(sql.Integer, sql.ForeignKey('rosters.roster_id'))
    player_id: str = sql.Column(sql.Text, sql.ForeignKey('players.player_id'))
    starter: bool = sql.Column(sql.Boolean)
    reserve: bool = sql.Column(sql.Boolean)
"""


