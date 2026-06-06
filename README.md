# CoffeeShop Backend

Backend API untuk aplikasi CoffeeShop menggunakan FastAPI dan SQLAlchemy.

## Teknologi

- Python
- FastAPI
- SQLAlchemy
- SQLite

## Struktur Proyek

- `app/main.py` - definisi FastAPI dan semua endpoint.
- `app/models.py` - model database SQLAlchemy.
- `app/schemas.py` - schema Pydantic untuk request dan response.
- `app/database.py` - konfigurasi database SQLite dan session.

## Instalasi

1. Buat virtual environment dan aktifkan:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependency:
   ```powershell
   pip install fastapi uvicorn sqlalchemy pydantic
   ```
3. Jalankan aplikasi:
   ```powershell
   uvicorn app.main:app --reload
   ```
4. Akses dokumentasi interaktif di:
   - `http://127.0.0.1:8000/docs`
   - `http://127.0.0.1:8000/redoc`

## Database

- Menggunakan SQLite dengan file `database.db`.
- Tabel yang dibuat otomatis saat server dijalankan.

### Model

- `Menu`
  - `id`: integer, primary key
  - `name`: string
  - `price`: integer
  - `stock`: integer

- `Transaction`
  - `id`: integer, primary key
  - `created_at`: datetime
  - `total_price`: integer
  - `details`: relasi ke `TransactionDetail`

- `TransactionDetail`
  - `id`: integer, primary key
  - `transaction_id`: foreign key ke `transactions`
  - `menu_id`: foreign key ke `menus`
  - `qty`: integer
  - `subtotal`: integer

## API Endpoints

Base path: `/api/v1`

### Menu

#### Buat menu baru

- Method: `POST`
- URL: `/api/v1/menus`
- Request body:
  ```json
  {
    "name": "Espresso",
    "price": 20000,
    "stock": 10
  }
  ```
- Response:
  ```json
  {
    "id": 1,
    "name": "Espresso",
    "price": 20000,
    "stock": 10
  }
  ```

#### Ambil menu berdasarkan ID

- Method: `GET`
- URL: `/api/v1/menus/{menu_id}`
- Response:
  ```json
  {
    "id": 1,
    "name": "Espresso",
    "price": 20000,
    "stock": 10
  }
  ```

#### Ambil semua menu

- Method: `GET`
- URL: `/api/v1/menus`
- Response:
  ```json
  [
    {
      "id": 1,
      "name": "Espresso",
      "price": 20000,
      "stock": 10
    },
    {
      "id": 2,
      "name": "Cappuccino",
      "price": 25000,
      "stock": 8
    }
  ]
  ```

#### Update menu

- Method: `PATCH`
- URL: `/api/v1/menus/{menu_id}`
- Request body (semua field opsional):
  ```json
  {
    "name": "Latte",
    "price": 22000,
    "stock": 12
  }
  ```
- Response:
  ```json
  {
    "id": 1,
    "name": "Latte",
    "price": 22000,
    "stock": 12
  }
  ```

#### Update stok menu

- Method: `PUT`
- URL: `/api/v1/menus/{menu_id}/stock`
- Request body:
  ```json
  {
    "stock": 15
  }
  ```
- Response:
  ```json
  {
    "id": 1,
    "name": "Espresso",
    "price": 20000,
    "stock": 15
  }
  ```

#### Hapus menu

- Method: `DELETE`
- URL: `/api/v1/menus/{menu_id}`
- Response:
  ```json
  {
    "message": "Menu deleted successfully"
  }
  ```

### Transaction

#### Buat transaksi

- Method: `POST`
- URL: `/api/v1/transactions`
- Request body:
  ```json
  {
    "items": [
      {
        "menu_id": 1,
        "qty": 2
      },
      {
        "menu_id": 2,
        "qty": 1
      }
    ]
  }
  ```
- Response:
  ```json
  {
    "id": 1,
    "created_at": "2025-01-01T12:00:00",
    "total_price": 65000,
    "details": [
      {
        "menu_id": 1,
        "qty": 2,
        "subtotal": 40000
      },
      {
        "menu_id": 2,
        "qty": 1,
        "subtotal": 25000
      }
    ]
  }
  ```

- Validasi:
  - Menu harus ada
  - Stok harus cukup
  - Jika stok tidak cukup, response error 400 dengan detail `Stok tidak mencukupi...`

#### Ambil semua transaksi

- Method: `GET`
- URL: `/api/v1/transactions`
- Response:
  ```json
  [
    {
      "id": 1,
      "created_at": "2025-01-01T12:00:00",
      "total_price": 65000,
      "details": [
        {
          "menu_id": 1,
          "qty": 2,
          "subtotal": 40000
        }
      ]
    }
  ]
  ```

#### Ambil transaksi berdasarkan ID

- Method: `GET`
- URL: `/api/v1/transactions/{transaction_id}`
- Response:
  ```json
  {
    "id": 1,
    "created_at": "2025-01-01T12:00:00",
    "total_price": 65000,
    "details": [
      {
        "menu_id": 1,
        "qty": 2,
        "subtotal": 40000
      }
    ]
  }
  ```

### Analytics

#### Ringkasan analytics

- Method: `GET`
- URL: `/api/v1/analytics/summary`
- Response:
  ```json
  {
    "total_revenue": 65000,
    "total_transactions": 1,
    "total_menus": 4
  }
  ```

#### Revenue per day

- Method: `GET`
- URL: `/api/v1/analytics/revenue-per-day`
- Response:
  ```json
  [
    {
      "date": "2025-01-01",
      "total_revenue": 65000
    }
  ]
  ```

#### Total revenue all time

- Method: `GET`
- URL: `/api/v1/analytics/total-revenue`
- Response:
  ```json
  {
    "total_revenue": 65000
  }
  ```

#### Total transaksi all time

- Method: `GET`
- URL: `/api/v1/analytics/total-transactions`
- Response:
  ```json
  {
    "total_transactions": 1
  }
  ```

#### Best selling menu

- Method: `GET`
- URL: `/api/v1/analytics/best-selling-menu`
- Response:
  ```json
  [
    {
      "menu_name": "Espresso",
      "total_sold": 5
    }
  ]
  ```

#### Total terjual per menu

- Method: `GET`
- URL: `/api/v1/analytics/total-sold-per-menu`
- Response:
  ```json
  [
    {
      "menu_name": "Espresso",
      "total_sold": 5
    }
  ]
  ```

## Error Handling

- `404 Not Found`: Ketika menu atau transaksi tidak ditemukan.
- `400 Bad Request`: Ketika stok tidak mencukupi atau permintaan tidak valid.

## Catatan

- `created_at` pada transaksi dibuat otomatis menggunakan waktu server.
- Stok menu dikurangi saat transaksi dibuat.
- Response model Pydantic menggunakan `orm_mode = True` agar model SQLAlchemy dapat di-serialisasi dengan benar.

## Saran Perbaikan

- Tambahkan validasi harga, nama, dan stok pada schema.
- Tambahkan endpoint pagination untuk daftar menu dan transaksi.
- Tambahkan fitur autentikasi jika dibutuhkan.
- Tambahkan unit test untuk endpoint dan model.
