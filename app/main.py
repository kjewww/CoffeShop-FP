from fastapi import Depends, FastAPI, HTTPException
from app.database import SessionLocal, engine, get_db, Session
from app.schemas import MenuCreate, MenuResponse, MenuUpdate, MenuStockUpdate
from app.models import Menu, Transaction, TransactionDetail
import models

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

# menu routes

# create menu
@app.post("/api/v1/menus")
async def create_menu(
    menu: MenuCreate, 
    db: Session = Depends(get_db)
):
    menu = Menu(name=menu.name, price=menu.price, stock=menu.stock)
    db.add(menu)
    db.commit()
    db.refresh(menu)
    return menu

# read all menus
@app.get("/api/v1/menus")
async def read_menus(
    db: Session = Depends(get_db)
):
    menus = db.query(Menu).all()
    return menus

# update menu
@app.patch("/api/v1/menus/{menu_id}")
async def update_menu(
    menu_id: int, 
    menu_update: MenuUpdate, 
    db: Session = Depends(get_db)
):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    if menu_update.name is not None:
        menu.name = menu_update.name
    if menu_update.price is not None:
        menu.price = menu_update.price
    if menu_update.stock is not None:
        menu.stock = menu_update.stock
        
    db.commit()
    db.refresh(menu)
    return menu

# update menu stock
@app.put("/api/v1/menus/{menu_id}/stock")
async def update_menu_stock(
    menu_id: int, 
    menu_stock_update: MenuStockUpdate, 
    db: Session = Depends(get_db)
):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    menu.stock = menu_stock_update.stock
    db.commit()
    db.refresh(menu)
    return menu

