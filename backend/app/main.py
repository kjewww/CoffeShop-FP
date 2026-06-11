from datetime import date, datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import timezone
from fastapi.middleware.cors import CORSMiddleware

from app.database import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    SessionLocal,
    engine,
    get_db,
)
import app.models as models
from app.models import Menu, Transaction, TransactionDetail, User
from app.schemas import (
    Item,
    MenuCreate,
    MenuResponse,
    MenuStockUpdate,
    MenuUpdate,
    Token,
    TransactionCreate,
    TransactionResponse,
    UserCreate,
    UserResponse,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mengizinkan Streamlit lokal Anda mengakses backend Vercel
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Sinkronisasi skema database termasuk tabel users baru
models.Base.metadata.create_all(bind=engine)

# --- KONFIGURASI KEAMANAN & AUTENTIKASI ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Helper Fungsi Keamanan
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    # Menggantikan datetime.utcnow() yang sudah deprecated
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Dependency untuk mengekstrak user yang sedang login saat ini
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesi masuk telah berakhir atau token tidak valid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# Dependency untuk memvalidasi Role (RBAC) sebelum mengakses endpoint
def require_role(allowed_roles: list):
    def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses ditolak! Anda tidak memiliki otoritas hak akses untuk fitur ini.",
            )
        return current_user

    return dependency


@app.get("/")
async def root():
    return {"message": "Hello World"}


# AUTHENTICATION ROUTES ==========================================================


@app.post("/api/v1/auth/register", response_model=UserResponse, status_code=201)
async def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Validasi duplikasi username
    existing_user = db.query(User).filter(User.username == payload.username).first()
    if existing_user:
        raise HTTPException(
            status_code=400, detail="Username tersebut telah terdaftar"
        )

    if payload.role not in ["owner", "kasir"]:
        raise HTTPException(
            status_code=400, detail="Role pilihan harus berupa 'owner' atau 'kasir'"
        )

    new_user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/api/v1/auth/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Username atau password salah")

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
    }


# MENU ROUTES =====================================================================


# create menu (Owner Only)
@app.post("/api/v1/menus", response_model=MenuResponse, status_code=201)
async def create_menu(
    payload: MenuCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"])),
):
    menu = Menu(name=payload.name, price=payload.price, stock=payload.stock)
    db.add(menu)
    db.commit()
    db.refresh(menu)
    return menu


# read menu by id (Owner & Kasir)
@app.get("/api/v1/menus/{menu_id}", response_model=MenuResponse)
async def read_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "kasir"])),
):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu


# read all menus (Owner & Kasir)
@app.get("/api/v1/menus", response_model=list[MenuResponse])
async def read_menus(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "kasir"])),
):
    menus = db.query(Menu).all()
    return menus


# update menu (Owner Only)
@app.patch("/api/v1/menus/{menu_id}", response_model=MenuResponse)
async def update_menu(
    menu_id: int,
    payload: MenuUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"])),
):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    if payload.name is not None:
        menu.name = payload.name
    if payload.price is not None:
        menu.price = payload.price
    if payload.stock is not None:
        menu.stock = payload.stock

    db.commit()
    db.refresh(menu)
    return menu


# update menu stock (Owner & Kasir)
@app.put("/api/v1/menus/{menu_id}/stock", response_model=MenuResponse)
async def update_menu_stock(
    menu_id: int,
    payload: MenuStockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "kasir"])),
):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    menu.stock = payload.stock
    db.commit()
    db.refresh(menu)
    return menu


# delete menu (Owner Only)
@app.delete("/api/v1/menus/{menu_id}")
async def delete_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"])),
):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    db.delete(menu)
    db.commit()
    return {"message": "Menu deleted successfully"}


# TRANSACTION ROUTES ==============================================================


# create transaction and update stock (Owner & Kasir)
@app.post(
    "/api/v1/transactions", status_code=201, response_model=TransactionResponse
)
async def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "kasir"])),
):
    total_price = 0
    transaction_details_to_add = []
    menus_to_update = []

    for item in payload.items:
        menu = db.query(Menu).filter(Menu.id == item.menu_id).first()
        if not menu:
            raise HTTPException(
                status_code=404, detail=f"Menu ID {item.menu_id} not found"
            )

        if menu.stock < item.qty:
            raise HTTPException(
                status_code=400,
                detail=f"Stok tidak mencukupi untuk {menu.name}. Tersisa: {menu.stock}",
            )

        subtotal = menu.price * item.qty
        total_price += subtotal

        menu.stock -= item.qty
        menus_to_update.append(menu)

        detail = TransactionDetail(
            menu_id=item.menu_id, qty=item.qty, subtotal=subtotal
        )
        transaction_details_to_add.append(detail)

    new_transaction = Transaction(total_price=total_price)
    db.add(new_transaction)
    db.flush()

    for detail in transaction_details_to_add:
        detail.transaction_id = new_transaction.id
        db.add(detail)

    db.commit()
    db.refresh(new_transaction)
    return new_transaction


# read all transactions (Owner & Kasir)
@app.get("/api/v1/transactions", response_model=list[TransactionResponse])
async def read_all_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "kasir"])),
):
    transactions = db.query(Transaction).all()
    return transactions


# read transaction by id for detail view (Owner & Kasir)
@app.get(
    "/api/v1/transactions/{transaction_id}",
    response_model=TransactionResponse,
)
async def read_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner", "kasir"])),
):
    transaction = (
        db.query(Transaction).filter(Transaction.id == transaction_id).first()
    )
    if not transaction:
        raise HTTPException(
            status_code=404, detail="Transaksi tidak ditemukan"
        )
    return transaction


# DASHBOARD ANALYTICS ROUTES ======================================================


# summary per day/week/month (Owner Only)
@app.get("/api/v1/analytics/summary")
async def analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"])),
):
    total_revenue = db.query(func.sum(Transaction.total_price)).scalar() or 0
    total_transactions = db.query(func.count(Transaction.id)).scalar() or 0
    total_menus = db.query(func.count(Menu.id)).scalar() or 0
    return {
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "total_menus": total_menus,
    }


# total revenue per day (Owner Only)
@app.get("/api/v1/analytics/revenue-per-day")
async def revenue_per_day(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"])),
):
    results = (
        db.query(
            func.date(Transaction.created_at).label("date"),
            func.sum(Transaction.total_price).label("total_revenue"),
        )
        .group_by(func.date(Transaction.created_at))
        .all()
    )

    return [
        {"date": str(r.date), "total_revenue": r.total_revenue} for r in results
    ]


# total revenue all time (Owner Only)
@app.get("/api/v1/analytics/total-revenue")
async def total_revenue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"])),
):
    total = db.query(func.sum(Transaction.total_price)).scalar() or 0
    return {"total_revenue": total}


# total transactions all time (Owner Only)
@app.get("/api/v1/analytics/total-transactions")
async def total_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"])),
):
    count = db.query(func.count(Transaction.id)).scalar() or 0
    return {"total_transactions": count}


# best selling menu (Owner Only)
@app.get("/api/v1/analytics/best-selling-menu")
async def best_selling_menu(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"])),
):
    results = (
        db.query(Menu.name, func.sum(TransactionDetail.qty).label("total_sold"))
        .join(TransactionDetail, Menu.id == TransactionDetail.menu_id)
        .group_by(Menu.id)
        .order_by(func.sum(TransactionDetail.qty).desc())
        .limit(5)
        .all()
    )

    return [{"menu_name": r.name, "total_sold": r.total_sold} for r in results]


# total sold per menu (Owner Only)
@app.get("/api/v1/analytics/total-sold-per-menu")
async def total_sold_per_menu(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["owner"])),
):
    results = (
        db.query(Menu.name, func.sum(TransactionDetail.qty).label("total_sold"))
        .join(TransactionDetail, Menu.id == TransactionDetail.menu_id)
        .group_by(Menu.id)
        .all()
    )

    return [{"menu_name": r.name, "total_sold": r.total_sold} for r in results]