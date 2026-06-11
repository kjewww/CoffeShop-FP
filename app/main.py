from datetime import date, datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func
from app.database import SessionLocal, engine, get_db, Session
from app.schemas import MenuCreate, MenuResponse, MenuUpdate, MenuStockUpdate, TransactionCreate, Item, TransactionResponse
from app.models import Menu, Transaction, TransactionDetail
import app.models as models

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Hello World"}

# MENU ROUTES =====================================================================

# create menu
@app.post("/api/v1/menus", response_model=MenuResponse, status_code=201)
async def create_menu(
    payload: MenuCreate, 
    db: Session = Depends(get_db)
):
    menu = Menu(
        name=payload.name, 
        price=payload.price, 
        stock=payload.stock
    )
    db.add(menu)
    db.commit()
    db.refresh(menu)
    return menu

# read menu by id
@app.get("/api/v1/menus/{menu_id}", response_model=MenuResponse)
async def read_menu(
    menu_id: int, 
    db: Session = Depends(get_db)
):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu

# read all menus
@app.get("/api/v1/menus", response_model=list[MenuResponse])
async def read_menus(
    db: Session = Depends(get_db)
):
    menus = db.query(Menu).all()
    return menus

# update menu
@app.patch("/api/v1/menus/{menu_id}", response_model=MenuResponse)
async def update_menu(
    menu_id: int, 
    payload: MenuUpdate, 
    db: Session = Depends(get_db)
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

# update menu stock
@app.put("/api/v1/menus/{menu_id}/stock", response_model=MenuResponse)
async def update_menu_stock(
    menu_id: int, 
    payload: MenuStockUpdate, 
    db: Session = Depends(get_db)
):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    menu.stock = payload.stock
    db.commit()
    db.refresh(menu)
    return menu

# delete menu
@app.delete("/api/v1/menus/{menu_id}")
async def delete_menu(
    menu_id: int, 
    db: Session = Depends(get_db)
):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    db.delete(menu)
    db.commit()
    return {"message": "Menu deleted successfully"}

# TRANSACTION ROUTES =====================================================================

# create transaction and update stock
@app.post("/api/v1/transactions", status_code=201, response_model=TransactionResponse)
async def create_transaction(
    payload: TransactionCreate, 
    db: Session = Depends(get_db)
):
    total_price = 0
    transaction_details_to_add = []
    menus_to_update = []

    for item in payload.items:
        menu = db.query(Menu).filter(Menu.id == item.menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail=f"Menu ID {item.menu_id} not found")
        
        if menu.stock < item.qty:
            raise HTTPException(
                status_code=400, 
                detail=f"Stok tidak mencukupi untuk {menu.name}. Tersisa: {menu.stock}"
            )
        
        subtotal = menu.price * item.qty
        total_price += subtotal
        
        menu.stock -= item.qty
        menus_to_update.append(menu)
        
        detail = TransactionDetail(
            menu_id=item.menu_id, 
            qty=item.qty, 
            subtotal=subtotal
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

# read all transactions
@app.get("/api/v1/transactions", response_model=list[TransactionResponse])
async def read_all_transactions(
    db: Session = Depends(get_db)
):
    transactions = db.query(Transaction).all()
    return transactions

# read transaction by id for detail view
@app.get("/api/v1/transactions/{transaction_id}", response_model=TransactionResponse)
async def read_transaction(
    transaction_id: int, 
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    return transaction

# DASHBOARD ANALYTICS ROUTES =====================================================================

# summary (total revenue, total transactions, total menus) per day/week/month
@app.get("/api/v1/analytics/summary")
async def analytics_summary(
    db: Session = Depends(get_db)
):
    total_revenue = db.query(func.sum(Transaction.total_price)).scalar() or 0
    total_transactions = db.query(func.count(Transaction.id)).scalar() or 0
    total_menus = db.query(func.count(Menu.id)).scalar() or 0
    return {
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "total_menus": total_menus
    }

# total revenue per day
@app.get("/api/v1/analytics/revenue-per-day")
async def revenue_per_day(
    db: Session = Depends(get_db)
):
    results = db.query(
        func.date(Transaction.created_at).label("date"),
        func.sum(Transaction.total_price).label("total_revenue")
    ).group_by(func.date(Transaction.created_at)).all()
    
    return [{"date": str(r.date), "total_revenue": r.total_revenue} for r in results]

# total revenue all time
@app.get("/api/v1/analytics/total-revenue")
async def total_revenue(
    db: Session = Depends(get_db)
):
    total = db.query(func.sum(Transaction.total_price)).scalar() or 0
    return {"total_revenue": total}

# total transactions all time
@app.get("/api/v1/analytics/total-transactions")
async def total_transactions(
    db: Session = Depends(get_db)
):
    count = db.query(func.count(Transaction.id)).scalar() or 0
    return {"total_transactions": count}

# best selling menu
@app.get("/api/v1/analytics/best-selling-menu")
async def best_selling_menu(
    db: Session = Depends(get_db)
):
    results = db.query(
        Menu.name,
        func.sum(TransactionDetail.qty).label("total_sold")
    ).join(TransactionDetail, Menu.id == TransactionDetail.menu_id
    ).group_by(Menu.id
    ).order_by(func.sum(TransactionDetail.qty).desc()
    ).limit(5).all()
    
    return [{"menu_name": r.name, "total_sold": r.total_sold} for r in results]

# total sold per menu
@app.get("/api/v1/analytics/total-sold-per-menu")
async def total_sold_per_menu(
    db: Session = Depends(get_db)
):
    results = db.query(
        Menu.name,
        func.sum(TransactionDetail.qty).label("total_sold")
    ).join(TransactionDetail, Menu.id == TransactionDetail.menu_id
    ).group_by(Menu.id
    ).all()
    
    return [{"menu_name": r.name, "total_sold": r.total_sold} for r in results]