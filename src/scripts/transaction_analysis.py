from db_helper import DatabaseHelper
from sql_tables import Transaction

def main():
    db = DatabaseHelper()
    q = db.db_session.query(Transaction)
    q = q.where(Transaction.week == 3)
    q = q.where(Transaction.transaction_type == "waiver")
    #q = q.where(Transaction.status == "complete")
    q = q.order_by(Transaction.sequence)
    transactions = q.all()
   
    for t in transactions:
        print(db.display_transaction(t))
        db.db_session.delete(t)
    db.db_session.commit()

if __name__ == "__main__":
    main()
