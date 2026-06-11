from datetime import datetime
from backend.app.database import SessionLocal, engine, Base
from backend.app.models import Menu, Transaction, TransactionDetail


def create_tables():
    Base.metadata.create_all(bind=engine)


def seed_data():
    db = SessionLocal()
    try:
        # Hapus data lama jika perlu
        db.query(TransactionDetail).delete()
        db.query(Transaction).delete()
        db.query(Menu).delete()
        db.commit()

        menus = [
            Menu(name="Espresso", price=20000, stock=20),
            Menu(name="Americano", price=22000, stock=18),
            Menu(name="Cappuccino", price=25000, stock=15),
            Menu(name="Latte", price=24000, stock=15),
            Menu(name="Mocha", price=28000, stock=12),
            Menu(name="Tea", price=15000, stock=20),
            Menu(name="Chocolate", price=26000, stock=10),
        ]

        db.add_all(menus)
        db.commit()

        sample_transaction = Transaction(total_price=42000, created_at=datetime.utcnow())
        db.add(sample_transaction)
        db.flush()

        transaction_details = [
            TransactionDetail(
                transaction_id=sample_transaction.id,
                menu_id=menus[0].id,
                qty=1,
                subtotal=20000,
            ),
            TransactionDetail(
                transaction_id=sample_transaction.id,
                menu_id=menus[1].id,
                qty=1,
                subtotal=22000,
            ),
        ]

        db.add_all(transaction_details)
        db.commit()

        print("Database berhasil diisi dengan data seed.")
        print(f"Menu seed: {len(menus)} item")
        print("Contoh transaksi dibuat.")
    finally:
        db.close()


if __name__ == "__main__":
    create_tables()
    seed_data()