from datetime import datetime, timedelta
import random  # Ditambahkan untuk mengacak data transaksi
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
            Menu(name="Creamy Matcha", price=20000, stock=25),
            Menu(name="Vanilla Milk", price=16000, stock=20)
        ]

        db.add_all(menus)
        db.commit()  # Commit di sini agar `menus` mendapatkan ID dari database

        for i in range(30):
            # 1. Tentukan jumlah item unik dalam satu transaksi (1 sampai 3 jenis menu)
            num_items = random.randint(1, 3)
            selected_menus = random.sample(menus, num_items)

            # 2. Atur tanggal mundur berdasarkan hari (i hari ke belakang)
            # Ditambah random jam dan menit agar waktu transaksinya lebih natural (tidak di jam yang sama setiap hari)
            hari_ke_belakang = i
            random_jam = random.randint(8, 21) # Transaksi terjadi antara jam 8 pagi - 9 malam
            random_menit = random.randint(0, 59)
            
            transaction_time = datetime.utcnow() - timedelta(days=hari_ke_belakang)
            transaction_time = transaction_time.replace(hour=random_jam, minute=random_menit, second=0, microsecond=0)

            # 3. Buat objek Transaksi dengan total_price sementara = 0
            transaction = Transaction(total_price=0, created_at=transaction_time)
            db.add(transaction)
            db.flush() # Flush agar mendapatkan ID transaksi

            total_price = 0
            transaction_details = []

            # 4. Buat detail transaksi untuk setiap menu yang terpilih
            for menu in selected_menus:
                qty = random.randint(1, 2) # Jumlah item (1-2 pcs)
                subtotal = menu.price * qty
                total_price += subtotal

                detail = TransactionDetail(
                    transaction_id=transaction.id,
                    menu_id=menu.id,
                    qty=qty,
                    subtotal=subtotal
                )
                transaction_details.append(detail)

            # 5. Update total_price asli dan masukkan detail ke DB
            transaction.total_price = total_price
            db.add_all(transaction_details)

        # Commit semua data transaksi sekaligus
        db.commit()

        print("Database berhasil diisi dengan data seed.")
        print(f"Menu seed: {len(menus)} item.")
        print("Berhasil membuat 30 record transaksi acak beserta detailnya.")
        
    except Exception as e:
        db.rollback()
        print(f"Terjadi kesalahan saat seeding: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_tables()
    seed_data()