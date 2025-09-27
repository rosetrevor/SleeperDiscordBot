from random import choice, randint

from db_helper import DatabaseHelper
from sql_tables import Manager, Roster
from sleeper import get_rosters, get_transactions_by_week, get_week

def get_response(user_input: str) -> str:
    lowered: str = user_input.lower()
    
    db = DatabaseHelper()

    if lowered == "":
       return "Well, you are awfully silent..."
    elif "hello" in lowered:
        return "Hello there"
    elif "how are you" in lowered:
        return "Good, thanks"
    elif "bye" in lowered:
        return "See you!"
    elif "roll dice" in lowered:
        return f"You rolled: {randint(1, 6)}"

    elif lowered[0] == "!":
        players = get_rosters()
        player_input = lowered.split("!")[-1]
        if player_input in players.keys():
            starter_str = ""
            player = players[player_input]
            for starter in player["starters"]:
                starter_str += starter + "\n"
            return starter_str
        elif player_input == "teams":
            teams_str = ""
            for team in players.keys():
                teams_str += team + "\n"
            return teams_str
        elif player_input == "transactions":
            # TODO: Hard coding week 3 is not a solution.
            all_transactions = get_transactions_by_week(week=3)
            db_transactions = db.get_transactions_by_week(week=3)
            all_transaction_ids = set([_t.transaction_id for _t in all_transactions])
            db_transaction_ids = set([_t.transaction_id for _t in db_transactions])
            new_transactions = all_transaction_ids.difference(db_transaction_ids)
            transaction_str = ""
            for transaction in all_transactions:
                if transaction.transaction_id in new_transactions:
                    transaction_str += f"{db.display_transaction(transaction)}\n"
            print(transaction_str)
            return transaction_str
        else:
            return choice(["I don't know that player, try again?", "new phone, who dis", "try again dummy"])
    else:
        return choice(["I do not understand", "What?", "Repeat that?", "Come again?"])

class ResponseHandler:
    def __init__(self):
        self.db = DatabaseHelper()
        self.managers = {m.display_name.lower(): m for m in self.db.get_all_managers()}

    def handle(self, message: str) -> str:
        lowered = message.lower()
        if lowered[0] == "!":
            return self.process_command(lowered.split("!")[-1])
        else:
            return self.handle_basic_response(lowered)
    
    def handle_unknown_response(self):
        return choice(["I do not understand", "What?", "Repeat that?", "Come again?"])

    def handle_basic_response(self, message: str) -> str:
        if lowered == "":
           return "Well, you are awfully silent..."
        elif "hello" in lowered:
            return "Hello there"
        elif "how are you" in lowered:
            return "Good, thanks"
        elif "bye" in lowered:
            return "See you!"
        elif "roll dice" in lowered:
            return f"You rolled: {randint(1, 6)}"
        else:
            return self.handle_unknown_response()
    
    def process_command(self, player_input: str) -> str:
        # Extract everything up to first " -"
        command = player_input.split(" -")[0]
        # Extract all arguments separated with " -"
        command_args = player_input.split(" -")[1:]
        if command in self.managers.keys():
            q = self.db.db_session.query(Manager)
            q = q.where(Manager.display_name.ilike(command))
            q = q.join(Roster, Roster.manager_id == Manager.manager_id)
            q = q.add_columns(Roster)
            manager, roster = q.first()
            players = self.db.get_players_by_ids(roster.starters)

            starter_str = ""
            for starter in roster.starters:
                for player in players:
                    if player.player_id == starter:
                        starter_str += f"{player}" + "\n"
            return starter_str
        elif player_input == "teams":
            teams_str = ""
            for team in self.managers.keys():
                teams_str += team + "\n"
            return teams_str
        elif player_input == "rosters":
            live_rosters = get_rosters()
            return self.db.update_rosters(live_rosters, True)
        elif player_input == "transactions":
            all_transactions = get_transactions_by_week(week=get_week())
            db_transactions = self.db.get_transactions_by_week(week=get_week())
            all_transaction_ids = set([int(_t.transaction_id) for _t in all_transactions])
            db_transaction_ids = set([int(_t.transaction_id) for _t in db_transactions])
            new_transactions = all_transaction_ids.difference(db_transaction_ids)
            transaction_str = None
            for transaction in all_transactions:
                if int(transaction.transaction_id) in new_transactions and transaction.status == "complete":
                    if transaction_str is None:
                        transaction_str = f"{self.db.display_transaction(transaction)}\n"
                    else:
                        transaction_str += f"{self.db.display_transaction(transaction)}\n"
                if int(transaction.transaction_id) in new_transactions:
                    print(new_transactions)
                    print()
                    print(db_transactions)
                    print()
                    print(all_transactions)
                    self.db.db_session.add(transaction)
                    self.db.db_session.commit()  # TODO: Problably want to move a bit of this logic
            return transaction_str
        else:
            return self.handle_unknown_response()

if __name__ == "__main__":
    response_handler = ResponseHandler()
    print(get_week())
    print(response_handler.handle("!transactions"))

