from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from jose import JWTError, jwt
import hashlib
import secrets
import traceback
import json
import random
import calendar

load_dotenv()

# ============================================================
# LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*80)
    print("🎆 KALUE FIREWORKS - DATA SCIENCE PROJECT")
    print("   Design and Development of a Data-Driven Sales and")
    print("   Inventory Analytics System for Revenue Leakage Control")
    print("="*80)
    print("📍 API: http://localhost:8000")
    print("📅 Data Period: June 1 - July 15, 2026 (45 days)")
    print("")
    print("👑 SUPERVISOR: supervisor@kalue.com / supervisor123")
    print("   → Full system access")
    print("   → Revenue leakage detection & analysis")
    print("   → Employee performance monitoring")
    print("   → Report generation")
    print("")
    print("📦 STORE KEEPERS (No Password):")
    print("   → KAL-001: shelui@kalue.com | Shelui")
    print("   → KAL-002: mwime@kalue.com | Mwime")
    print("   → KAL-003: zawadi@kalue.com | Zawadi")
    print("   → KAL-004: no5@kalue.com | No.5 & No.6")
    print("   → Record sales & inventory movements")
    print("="*80 + "\n")
    
    init_db()
    yield

app = FastAPI(
    title="KALUE FIREWORKS - Inventory Analytics System",
    description="Data-Driven Sales and Inventory Analytics for Revenue Leakage Control",
    version="4.2",
    lifespan=lifespan
)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/{rest_of_path:path}")
async def options_handler(request: Request):
    return JSONResponse(
        status_code=200,
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, Origin, X-Requested-With",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }
    )

# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.getenv("SECRET_KEY", "kalue-fireworks-data-science-project-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

security = HTTPBearer()

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return f"{salt}${hash_obj.hexdigest()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, hash_value = hashed_password.split('$')
        hash_obj = hashlib.sha256((salt + plain_password).encode())
        return hash_obj.hexdigest() == hash_value
    except:
        return False

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user_type = payload.get("type")
        user_stations = payload.get("stations", [])
        
        if user_type == "supervisor":
            return {"id": "SUP-001", "role": "supervisor", "stations": STATIONS_LIST, "name": "Supervisor KALUE"}
        else:
            col = get_collection('employees')
            user = find_one(col, {"id": user_id})
            if user is None:
                raise HTTPException(status_code=401, detail="User not found")
            return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_supervisor(current_user = Depends(get_current_user)):
    if current_user.get('role') != 'supervisor':
        raise HTTPException(status_code=403, detail="Supervisor access required")
    return current_user

# ============================================================
# MONGODB
# ============================================================

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "kalue_fireworks_ds"

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    client.admin.command('ping')
    print("✅ MongoDB connected")
except Exception as e:
    print(f"❌ MongoDB error: {e}")
    db = None

# ============================================================
# DATA - PRODUCTS & STATIONS
# ============================================================

PRODUCTS = [
    {"id": "futa_box", "name": "Futa (V6) Boxes", "unit": "Box", "category": "Explosives", "price": 240000},
    {"id": "futa_pcs", "name": "Futa Retail Pieces", "unit": "Pcs", "category": "Explosives", "price": 2000},
    {"id": "kamba_rollar", "name": "Kamba Moto Rollers", "unit": "Rollar", "category": "Fuses", "price": 280000},
    {"id": "nonel", "name": "Nonel Detonators", "unit": "Pcs", "category": "Detonators", "price": 6000},
    {"id": "kamba_moto", "name": "Safety Fuse (Kamba Moto)", "unit": "Meter", "category": "Fuses", "price": 3000},
    {"id": "plain_det_box", "name": "Plain Detonators (Box)", "unit": "Box", "category": "Detonators", "price": 150000},
    {"id": "plain_det_pcs", "name": "Plain Detonators (Pcs)", "unit": "Pcs", "category": "Detonators", "price": 2000},
    {"id": "cordtex_rollar", "name": "Cordtex Rollers", "unit": "Rollar", "category": "Detonating Cord", "price": 250000},
    {"id": "cordtex_meter", "name": "Cordtex (Meters)", "unit": "Meter", "category": "Detonating Cord", "price": 2000},
    {"id": "lp", "name": "LP Detonators", "unit": "Pcs", "category": "Detonators", "price": 7000},
    {"id": "eid", "name": "EID Detonators", "unit": "Pcs", "category": "Detonators", "price": 5000},
    {"id": "egneter", "name": "Egneter (Igniter Cord)", "unit": "Meter", "category": "Igniters", "price": 5000}
]

STATIONS_LIST = ["Shelui", "Mwime", "Zawadi", "No.5", "No.6"]

# ============================================================
# CURRENT BUSINESS DATE
# ============================================================
# The demo/historical dataset is generated for a fixed window: June 1 - July 15, 2026.
# Live transactions (adding/removing stock) must be recorded against this SAME fixed
# date - not the server's real system clock (datetime.now()) - otherwise a new,
# disconnected inventory document gets created every time the server's real date
# doesn't match the seeded window, and "current inventory" (which always shows the
# latest dated document) keeps displaying the old frozen snapshot instead of the
# just-recorded change. This is what "Incoming/Outgoing not updating" was.
CURRENT_BUSINESS_DATE = "2026-07-15"

# ============================================================
# USERS
# ============================================================

SUPERVISOR_USER = {
    "id": "SUP-001",
    "full_name": "Supervisor KALUE",
    "email": "supervisor@kalue.com",
    "password": hash_password("supervisor123"),
    "role": "supervisor",
    "stations": STATIONS_LIST,
    "status": "online",
    "last_active": datetime.now().isoformat(),
    "created_at": datetime.now().isoformat()
}

STORE_KEEPERS = [
    {
        "id": "KAL-001",
        "full_name": "John Mwangi",
        "email": "shelui@kalue.com",
        "phone": "0712345678",
        "position": "Store Keeper",
        "stations": ["Shelui"],
        "role": "store_keeper",
        "status": "online",
        "last_active": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "KAL-002",
        "full_name": "Mary Peter",
        "email": "mwime@kalue.com",
        "phone": "0723456789",
        "position": "Store Keeper",
        "stations": ["Mwime"],
        "role": "store_keeper",
        "status": "online",
        "last_active": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "KAL-003",
        "full_name": "Ali Hassan",
        "email": "zawadi@kalue.com",
        "phone": "0734567890",
        "position": "Store Keeper",
        "stations": ["Zawadi"],
        "role": "store_keeper",
        "status": "online",
        "last_active": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "KAL-004",
        "full_name": "Sarah Kim",
        "email": "no5@kalue.com",
        "phone": "0745678901",
        "position": "Store Keeper",
        "stations": ["No.5", "No.6"],
        "role": "store_keeper",
        "status": "online",
        "last_active": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat()
    }
]

# ============================================================
# REALISTIC DATA GENERATION - JUNE 1 TO JULY 15, 2026
# ============================================================

def generate_realistic_business_data():
    """Generate realistic business data for 45 days (June 1 - July 15, 2026)"""
    
    # Base stock levels per station (starting June 1)
    base_stock = {
        "futa_box": {"shelui": 45, "mwime": 25, "zawadi": 12, "no5": 20, "no6": 20},
        "futa_pcs": {"shelui": 150, "mwime": 80, "zawadi": 40, "no5": 60, "no6": 60},
        "kamba_rollar": {"shelui": 8, "mwime": 4, "zawadi": 2, "no5": 3, "no6": 3},
        "nonel": {"shelui": 120, "mwime": 60, "zawadi": 25, "no5": 40, "no6": 40},
        "kamba_moto": {"shelui": 200, "mwime": 100, "zawadi": 50, "no5": 80, "no6": 80},
        "plain_det_box": {"shelui": 10, "mwime": 5, "zawadi": 2, "no5": 4, "no6": 4},
        "plain_det_pcs": {"shelui": 100, "mwime": 50, "zawadi": 20, "no5": 35, "no6": 35},
        "cordtex_rollar": {"shelui": 6, "mwime": 3, "zawadi": 1, "no5": 2, "no6": 2},
        "cordtex_meter": {"shelui": 150, "mwime": 70, "zawadi": 30, "no5": 50, "no6": 50},
        "lp": {"shelui": 80, "mwime": 40, "zawadi": 15, "no5": 25, "no6": 25},
        "eid": {"shelui": 130, "mwime": 65, "zawadi": 30, "no5": 45, "no6": 45},
        "egneter": {"shelui": 50, "mwime": 25, "zawadi": 10, "no5": 15, "no6": 15}
    }
    
    station_volume = {
        "shelui": {"incoming_rate": 0.8, "outgoing_rate": 0.7},
        "mwime": {"incoming_rate": 0.5, "outgoing_rate": 0.4},
        "zawadi": {"incoming_rate": 0.3, "outgoing_rate": 0.2},
        "no5": {"incoming_rate": 0.4, "outgoing_rate": 0.35},
        "no6": {"incoming_rate": 0.4, "outgoing_rate": 0.35}
    }
    
    inventory = {}
    sales = {}
    expenses = {}
    leakage_events = []
    
    # Track stock per product per station
    current_stock = {}
    for product_id, stations in base_stock.items():
        current_stock[product_id] = {}
        for station_key, qty in stations.items():
            current_stock[product_id][station_key] = qty
    
    # Generate for each day (June 1 - July 15)
    start_date = datetime(2026, 6, 1)
    end_date = datetime(2026, 7, 15)
    current_date = start_date
    
    day_count = 0
    
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        day_count += 1
        
        # Day factors
        day_of_week = current_date.weekday()
        is_weekend = day_of_week >= 5
        day_of_month = current_date.day
        
        # Period multipliers
        if day_of_month <= 7:
            incoming_mult = 1.3
            outgoing_mult = 1.0
        elif day_of_month <= 21:
            incoming_mult = 1.0
            outgoing_mult = 1.0
        else:
            incoming_mult = 0.7
            outgoing_mult = 1.2
            
        # Weekend effect
        activity_mult = 0.5 if is_weekend else 1.0
        
        # Initialize day data
        inventory[date_str] = {
            "incoming": {},
            "outgoing": {},
            "remaining": {}
        }
        sales[date_str] = []
        expenses[date_str] = []
        
        # For each station
        for station_key, volume in station_volume.items():
            station_name = station_key.capitalize()
            if station_key == "no5":
                station_name = "No.5"
            elif station_key == "no6":
                station_name = "No.6"
            
            # For each product
            for product in PRODUCTS:
                product_id = product['id']
                
                # Skip if station doesn't have this product
                if station_key not in current_stock.get(product_id, {}):
                    continue
                
                # Calculate incoming (stock delivery)
                base_qty = base_stock.get(product_id, {}).get(station_key, 0)
                if base_qty > 0:
                    incoming = int(base_qty * 0.15 * volume["incoming_rate"] * incoming_mult * activity_mult)
                    incoming = max(0, min(incoming, 30))
                else:
                    incoming = 0
                
                # Calculate outgoing (sales/usage)
                if base_qty > 0:
                    outgoing = int(base_qty * 0.12 * volume["outgoing_rate"] * outgoing_mult * activity_mult)
                    outgoing = max(0, min(outgoing, 25))
                else:
                    outgoing = 0
                
                # Update stock
                current_qty = current_stock.get(product_id, {}).get(station_key, 0)
                new_qty = current_qty + incoming - outgoing
                new_qty = max(0, new_qty)
                
                # Store data
                if product_id not in inventory[date_str]["incoming"]:
                    inventory[date_str]["incoming"][product_id] = {}
                if product_id not in inventory[date_str]["outgoing"]:
                    inventory[date_str]["outgoing"][product_id] = {}
                if product_id not in inventory[date_str]["remaining"]:
                    inventory[date_str]["remaining"][product_id] = {}
                
                inventory[date_str]["incoming"][product_id][station_key] = incoming
                inventory[date_str]["outgoing"][product_id][station_key] = outgoing
                inventory[date_str]["remaining"][product_id][station_key] = new_qty
                
                # Update current stock
                if product_id not in current_stock:
                    current_stock[product_id] = {}
                current_stock[product_id][station_key] = new_qty
                
                # Generate sales if outgoing > 0
                if outgoing > 0 and random.random() > 0.3:
                    price = product.get('price', 5000)
                    total = outgoing * price
                    sales[date_str].append({
                        "station": station_name,
                        "product_id": product_id,
                        "product_name": product['name'],
                        "quantity": outgoing,
                        "price": price,
                        "total": total,
                        "employee_id": random.choice(["KAL-001", "KAL-002", "KAL-003", "KAL-004"]),
                        "timestamp": f"{date_str}T{random.randint(8, 17):02d}:{random.randint(0, 59):02d}:00"
                    })
                
                # Check for revenue leakage
                expected_revenue = outgoing * product.get('price', 5000)
                actual_revenue = expected_revenue * random.uniform(0.85, 1.0)
                
                if actual_revenue < expected_revenue * 0.9:
                    leakage_events.append({
                        "date": date_str,
                        "station": station_name,
                        "product": product['name'],
                        "expected_revenue": expected_revenue,
                        "actual_revenue": actual_revenue,
                        "discrepancy": expected_revenue - actual_revenue,
                        "discrepancy_percentage": ((expected_revenue - actual_revenue) / expected_revenue * 100),
                        "employee_id": random.choice(["KAL-001", "KAL-002", "KAL-003", "KAL-004"]),
                        "detected": datetime.now().isoformat(),
                        "status": "pending"
                    })
            
            # Generate expenses
            num_expenses = random.randint(1, 3)
            expense_types = ["Transport", "Electricity", "Water", "Fuel", "Staff Meals", "Motorcycle", "Equipment", "Office Supplies", "Communication", "Maintenance"]
            for _ in range(num_expenses):
                expenses[date_str].append({
                    "description": random.choice(expense_types),
                    "amount": random.randint(5000, 75000),
                    "station": station_name,
                    "employee_id": random.choice(["KAL-001", "KAL-002", "KAL-003", "KAL-004"]),
                    "timestamp": f"{date_str}T{random.randint(8, 17):02d}:{random.randint(0, 59):02d}:00"
                })
        
        current_date += timedelta(days=1)
    
    print(f"✅ Generated {day_count} days of data (June 1 - July 15, 2026)")
    print(f"   - {len(inventory)} days of inventory data")
    print(f"   - {sum(len(s) for s in sales.values())} sales records")
    print(f"   - {sum(len(e) for e in expenses.values())} expense records")
    print(f"   - {len(leakage_events)} potential revenue leakage events detected")
    
    return {
        "inventory": inventory,
        "sales": sales,
        "expenses": expenses,
        "leakage": leakage_events
    }

# ============================================================
# PYDANTIC MODELS
# ============================================================

class SupervisorLoginRequest(BaseModel):
    email: str
    password: str

class StoreKeeperLoginRequest(BaseModel):
    email: str
    employee_id: str

class InventoryUpdateSupervisor(BaseModel):
    station: str
    product_id: str
    incoming: int
    note: Optional[str] = ""
    
    @field_validator('incoming')
    @classmethod
    def validate_incoming(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Quantity must be greater than 0')
        if v > 100:
            raise ValueError('Cannot add more than 100 per product')
        return v

class InventoryUpdateStoreKeeper(BaseModel):
    station: str
    product_id: str
    outgoing: int
    note: Optional[str] = ""
    
    @field_validator('outgoing')
    @classmethod
    def validate_outgoing(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Quantity must be greater than 0')
        return v

class SaleCreate(BaseModel):
    station: str
    product_id: str
    quantity: int
    price: float
    total: float
    date: Optional[str] = None

class ExpenseCreate(BaseModel):
    description: str
    amount: float
    station: str
    date: Optional[str] = None

class ReportRequest(BaseModel):
    station: str
    date: str

# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_collection(name):
    if db is not None:
        return db[name]
    if not hasattr(get_collection, 'fallback'):
        get_collection.fallback = {}
    if name not in get_collection.fallback:
        get_collection.fallback[name] = []
    return get_collection.fallback[name]

def find(collection, query={}):
    if db is not None:
        return list(collection.find(query, {'_id': 0}))
    result = []
    for item in collection:
        match = True
        for k, v in query.items():
            if item.get(k) != v:
                match = False
                break
        if match:
            result.append(item)
    return result

def find_one(collection, query):
    if db is not None:
        return collection.find_one(query, {'_id': 0})
    for item in collection:
        match = True
        for k, v in query.items():
            if item.get(k) != v:
                match = False
                break
        if match:
            return item
    return None

def update_one(collection, query, update_data):
    if db is not None:
        return collection.update_one(query, update_data)
    for item in collection:
        match = True
        for k, v in query.items():
            if item.get(k) != v:
                match = False
                break
        if match:
            for k, v in update_data.get('$set', {}).items():
                item[k] = v
            return True
    return False

def insert_one(collection, data):
    if db is not None:
        return collection.insert_one(data)
    collection.append(data)
    return True

# ============================================================
# ACTIVITY LOG
# ============================================================

def log_activity(action: str, actor: dict, station: str, product_id: str, quantity: int, new_remaining: int, note: str = ""):
    """Log every stock change for audit trail"""
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    product_name = product['name'] if product else product_id

    entry = {
        "activity_id": f"ACT-{int(datetime.now().timestamp() * 1000)}-{secrets.token_hex(3)}",
        "action": action,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "timestamp": datetime.now().isoformat(),
        "station": station,
        "product_id": product_id,
        "product_name": product_name,
        "quantity": quantity,
        "new_remaining": new_remaining,
        "actor_id": actor.get('id'),
        "actor_name": actor.get('full_name') or actor.get('name') or 'Unknown',
        "actor_role": actor.get('role'),
        "note": note
    }

    col = get_collection('activity_log')
    insert_one(col, entry)
    
    return entry

def get_activity_logs(date: Optional[str] = None, station: Optional[str] = None, limit: int = 500):
    col = get_collection('activity_log')

    if db is not None:
        query: Dict[str, Any] = {}
        if date:
            query['date'] = date
        if station:
            query['station'] = station
        cursor = col.find(query, {'_id': 0}).sort('timestamp', -1).limit(limit)
        return list(cursor)

    results = list(col)
    if date:
        results = [r for r in results if r.get('date') == date]
    if station:
        results = [r for r in results if r.get('station') == station]
    results.sort(key=lambda r: r.get('timestamp', ''), reverse=True)
    return results[:limit]

# ============================================================
# INIT DATABASE
# ============================================================

def init_db():
    try:
        products_col = get_collection('products')
        if db is not None and products_col.count_documents({}) == 0:
            products_col.insert_many(PRODUCTS)
            print("✅ Products inserted")

        stations_col = get_collection('stations')
        if db is not None and stations_col.count_documents({}) == 0:
            stations_col.insert_many([{"name": s} for s in STATIONS_LIST])
            print("✅ Stations inserted")

        supervisor_col = get_collection('supervisor')
        if db is not None and supervisor_col.count_documents({}) == 0:
            supervisor_col.insert_one(SUPERVISOR_USER)
            print("✅ Supervisor created")

        employees_col = get_collection('employees')
        if db is not None and employees_col.count_documents({}) == 0:
            employees_col.insert_many(STORE_KEEPERS)
            print("✅ Store Keepers created")

        data = generate_realistic_business_data()
        
        inv_col = get_collection('daily_inventory')
        if db is not None and inv_col.count_documents({}) == 0:
            for date, inv_data in data['inventory'].items():
                inv_data['_id'] = date
                inv_col.insert_one(inv_data)
            print(f"✅ Inventory data inserted ({len(data['inventory'])} days)")

        sales_col = get_collection('daily_sales')
        if db is not None and sales_col.count_documents({}) == 0:
            for date, sales_data in data['sales'].items():
                sales_col.insert_one({
                    "_id": date,
                    "date": date,
                    "sales": sales_data
                })
            print(f"✅ Sales data inserted ({len(data['sales'])} days)")

        exp_col = get_collection('daily_expenses')
        if db is not None and exp_col.count_documents({}) == 0:
            for date, exp_data in data['expenses'].items():
                exp_col.insert_one({
                    "_id": date,
                    "date": date,
                    "expenses": exp_data
                })
            print(f"✅ Expenses data inserted ({len(data['expenses'])} days)")

        leakage_col = get_collection('leakage_events')
        if db is not None and leakage_col.count_documents({}) == 0:
            for event in data['leakage']:
                leakage_col.insert_one(event)
            print(f"✅ Leakage events inserted ({len(data['leakage'])} events)")

        print("✅ Database initialized with realistic June-July 2026 data!")
        print("   📅 Data Range: June 1 - July 15, 2026 (45 days)")
        print("   🎯 Revenue Leakage Detection Active")
        
    except Exception as e:
        print(f"❌ Database init error: {e}")
        traceback.print_exc()

# ============================================================
# AUTH ENDPOINTS
# ============================================================

@app.post("/api/auth/supervisor/login")
def supervisor_login(login_data: SupervisorLoginRequest):
    try:
        col = get_collection('supervisor')
        user = find_one(col, {"email": login_data.email})
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not verify_password(login_data.password, user.get('password', '')):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token_data = {"sub": "SUP-001", "type": "supervisor", "stations": STATIONS_LIST}
        token = create_access_token(token_data)
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": "SUP-001",
                "name": "Supervisor KALUE",
                "role": "supervisor",
                "stations": STATIONS_LIST
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Supervisor login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/api/auth/storekeeper/login")
def storekeeper_login(login_data: StoreKeeperLoginRequest):
    try:
        col = get_collection('employees')
        user = find_one(col, {"id": login_data.employee_id, "email": login_data.email})
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or employee ID")
        
        update_one(col, {"id": user['id']}, {"$set": {"last_active": datetime.now().isoformat(), "status": "online"}})
        
        token_data = {
            "sub": user['id'],
            "type": "store_keeper",
            "stations": user.get('stations', [])
        }
        token = create_access_token(token_data)
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user['id'],
                "name": user['full_name'],
                "email": user['email'],
                "role": "store_keeper",
                "stations": user.get('stations', []),
                "phone": user.get('phone', ''),
                "position": user.get('position', '')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Store keeper login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/api/auth/logout")
def logout(current_user = Depends(get_current_user)):
    if current_user.get('role') == 'store_keeper':
        col = get_collection('employees')
        update_one(col, {"id": current_user['id']}, {"$set": {"status": "offline"}})
    return {"success": True, "message": "Logged out successfully"}

# ============================================================
# CURRENT INVENTORY ENDPOINT (NO DATE SELECTION)
# ============================================================

@app.get("/api/inventory/current")
def get_current_inventory(current_user = Depends(get_current_user)):
    """Get current inventory - always reflects CURRENT_BUSINESS_DATE, the same
    fixed date that add/remove-stock write to. This guarantees reads and writes
    always target the exact same document, so stock changes are always visible
    immediately, regardless of any other dated records that may exist."""
    col = get_collection('daily_inventory')

    latest = find_one(col, {"_id": CURRENT_BUSINESS_DATE})

    if not latest:
        # Fallback: extremely unlikely (means the seed data was never inserted),
        # but avoid a hard failure - show whatever the most recent record is.
        all_inv = find(col, {})
        if not all_inv:
            return {
                "incoming": {},
                "outgoing": {},
                "remaining": {},
                "hasData": False,
                "message": "No inventory data available"
            }
        latest = sorted(all_inv, key=lambda x: x.get('_id', ''), reverse=True)[0]
    
    if current_user.get('role') == 'supervisor':
        return {
            "date": latest.get('_id'),
            "incoming": latest.get("incoming", {}),
            "outgoing": latest.get("outgoing", {}),
            "remaining": latest.get("remaining", {}),
            "hasData": True
        }
    
    # Store Keeper - filter by their stations
    user_stations = current_user.get('stations', [])
    station_keys = [s.lower().replace(".", "") for s in user_stations]
    
    filtered = {
        "date": latest.get('_id'),
        "hasData": True,
        "incoming": {},
        "outgoing": {},
        "remaining": {}
    }
    
    for field in ['incoming', 'outgoing', 'remaining']:
        for product_id, stations in latest.get(field, {}).items():
            for station_key in station_keys:
                if station_key in stations:
                    if product_id not in filtered[field]:
                        filtered[field][product_id] = {}
                    filtered[field][product_id][station_key] = stations[station_key]
    
    return filtered

# ============================================================
# INVENTORY ENDPOINTS (WITH DATE)
# ============================================================

@app.get("/api/inventory/{date}")
def get_inventory_by_date(date: str, current_user = Depends(get_current_user)):
    col = get_collection('daily_inventory')
    result = find_one(col, {"_id": date})
    
    if not result:
        return {
            "date": date, 
            "incoming": {}, 
            "outgoing": {}, 
            "remaining": {}, 
            "hasData": False,
            "message": "No inventory data for this date"
        }
    
    if current_user.get('role') == 'supervisor':
        return {
            "date": date,
            "incoming": result.get("incoming", {}),
            "outgoing": result.get("outgoing", {}),
            "remaining": result.get("remaining", {}),
            "hasData": True
        }
    
    user_stations = current_user.get('stations', [])
    station_keys = [s.lower().replace(".", "") for s in user_stations]
    
    filtered = {"date": date, "hasData": True, "incoming": {}, "outgoing": {}, "remaining": {}}
    
    for field in ['incoming', 'outgoing', 'remaining']:
        for product_id, stations in result.get(field, {}).items():
            for station_key in station_keys:
                if station_key in stations:
                    if product_id not in filtered[field]:
                        filtered[field][product_id] = {}
                    filtered[field][product_id][station_key] = stations[station_key]
    
    return filtered

# ============================================================
# ADD INVENTORY - SUPERVISOR ONLY (IMEREKEBISHWA)
# ============================================================

@app.post("/api/inventory/supervisor")
def update_inventory_supervisor(inv_update: InventoryUpdateSupervisor, current_user = Depends(require_supervisor)):
    station_key = inv_update.station.lower().replace(".", "")
    product_id = inv_update.product_id
    incoming = inv_update.incoming
    note = inv_update.note or ""
    
    if incoming <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
    
    if incoming > 100:
        raise HTTPException(status_code=400, detail="Cannot add more than 100 per product")
    
    col = get_collection('daily_inventory')
    today = CURRENT_BUSINESS_DATE
    existing = find_one(col, {"_id": today})
    
    if not existing:
        yesterday = (datetime.strptime(CURRENT_BUSINESS_DATE, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_inv = find_one(col, {"_id": yesterday})
        
        new_inv = {
            "_id": today,
            "date": today,
            "incoming": {},
            "outgoing": {},
            "remaining": {}
        }
        
        if yesterday_inv:
            new_inv["remaining"] = yesterday_inv.get("remaining", {})
        
        if db is not None:
            col.insert_one(new_inv)
        existing = new_inv
    
    current_remaining = 0
    if product_id in existing.get("remaining", {}):
        if station_key in existing["remaining"][product_id]:
            current_remaining = existing["remaining"][product_id][station_key]

    existing_incoming = 0
    if product_id in existing.get("incoming", {}):
        if station_key in existing["incoming"][product_id]:
            existing_incoming = existing["incoming"][product_id][station_key]
    
    new_remaining = current_remaining + incoming
    new_incoming_total = existing_incoming + incoming
    
    if db is not None:
        update_query = {
            "$set": {}
        }
        
        # Accumulate today's incoming total, don't overwrite previous deliveries
        incoming_path = f"incoming.{product_id}.{station_key}"
        update_query["$set"][incoming_path] = new_incoming_total
        
        remaining_path = f"remaining.{product_id}.{station_key}"
        update_query["$set"][remaining_path] = new_remaining
        
        col.update_one({"_id": today}, update_query)
    
    log_activity(
        action="incoming",
        actor=current_user,
        station=inv_update.station,
        product_id=product_id,
        quantity=incoming,
        new_remaining=new_remaining,
        note=f"Supervisor added {incoming} units. {note}"
    )
    
    return {
        "success": True, 
        "message": f"Stock added: +{incoming} {product_id} at {inv_update.station}",
        "date": today,
        "product": product_id,
        "station": inv_update.station,
        "incoming": incoming,
        "new_remaining": new_remaining
    }
# ============================================================
# REMOVE INVENTORY - STORE KEEPER ONLY (IMEREKEBISHWA)
# ============================================================

@app.post("/api/inventory/storekeeper")
def update_inventory_storekeeper(inv_update: InventoryUpdateStoreKeeper, current_user = Depends(get_current_user)):
    if current_user.get('role') != 'store_keeper':
        raise HTTPException(status_code=403, detail="Store keeper access required")
    
    user_stations = current_user.get('stations', [])
    if inv_update.station not in user_stations:
        raise HTTPException(status_code=403, detail=f"Cannot manage {inv_update.station}. Your stations: {', '.join(user_stations)}")
    
    # Get station key
    station_key = inv_update.station.lower().replace(".", "")
    product_id = inv_update.product_id
    outgoing = inv_update.outgoing
    note = inv_update.note or ""
    
    if outgoing <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
    
    col = get_collection('daily_inventory')
    today = CURRENT_BUSINESS_DATE
    existing = find_one(col, {"_id": today})
    
    # If no inventory for today, create from yesterday
    if not existing:
        # Try to get yesterday's inventory
        yesterday = (datetime.strptime(CURRENT_BUSINESS_DATE, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_inv = find_one(col, {"_id": yesterday})
        
        new_inv = {
            "_id": today,
            "date": today,
            "incoming": {},
            "outgoing": {},
            "remaining": {}
        }
        
        if yesterday_inv:
            new_inv["remaining"] = yesterday_inv.get("remaining", {})
        
        if db is not None:
            col.insert_one(new_inv)
        existing = new_inv
    
    # Check current remaining stock for this product and station
    current_remaining = 0
    if product_id in existing.get("remaining", {}):
        if station_key in existing["remaining"][product_id]:
            current_remaining = existing["remaining"][product_id][station_key]

    # Get today's existing outgoing total so we can accumulate rather than overwrite it
    existing_outgoing = 0
    if product_id in existing.get("outgoing", {}):
        if station_key in existing["outgoing"][product_id]:
            existing_outgoing = existing["outgoing"][product_id][station_key]
    
    # Check if enough stock is available
    if current_remaining < outgoing:
        raise HTTPException(
            status_code=400, 
            detail=f"Not enough stock. Available: {current_remaining}, Requested: {outgoing}"
        )
    
    # Update the inventory
    new_remaining = current_remaining - outgoing
    new_outgoing_total = existing_outgoing + outgoing

    if db is not None:
        # Use $set to handle nested fields properly
        update_query = {
            "$set": {}
        }
        
        # Update outgoing (accumulate today's total, don't overwrite previous removals)
        outgoing_path = f"outgoing.{product_id}.{station_key}"
        update_query["$set"][outgoing_path] = new_outgoing_total
        
        # Update remaining
        remaining_path = f"remaining.{product_id}.{station_key}"
        update_query["$set"][remaining_path] = new_remaining
        
        col.update_one({"_id": today}, update_query)
    
    # Log the activity
    log_activity(
        action="outgoing",
        actor=current_user,
        station=inv_update.station,
        product_id=product_id,
        quantity=outgoing,
        new_remaining=new_remaining,
        note=f"Store keeper removed {outgoing} units. {note}"
    )
    
    return {
        "success": True,
        "message": f"Stock removed: -{outgoing} {product_id} at {inv_update.station}",
        "date": today,
        "product": product_id,
        "station": inv_update.station,
        "outgoing": outgoing,
        "new_remaining": new_remaining
    }
# ============================================================
# ACTIVITY FEED ENDPOINT
# ============================================================

@app.get("/api/activity")
def get_activity(date: Optional[str] = None, station: Optional[str] = None, limit: int = 500, current_user = Depends(get_current_user)):
    if current_user.get('role') == 'supervisor':
        logs = get_activity_logs(date=date, station=station, limit=limit)
    else:
        user_stations = current_user.get('stations', [])
        if station and station in user_stations:
            logs = get_activity_logs(date=date, station=station, limit=limit)
        else:
            # Get logs for all user's stations
            all_logs = []
            for st in user_stations:
                st_logs = get_activity_logs(date=date, station=st, limit=limit // len(user_stations) if user_stations else limit)
                all_logs.extend(st_logs)
            all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            logs = all_logs[:limit]

    return {"activity": logs, "total": len(logs)}

# ============================================================
# REPORTS ENDPOINT
# ============================================================

@app.get("/api/reports/station")
def get_station_report(station: str, date: Optional[str] = None, current_user = Depends(require_supervisor)):
    """Generate report for a specific station and date"""
    
    # Validate station exists
    if station not in STATIONS_LIST:
        raise HTTPException(status_code=400, detail=f"Station '{station}' not found")
    
    station_key = station.lower().replace(".", "")
    
    # Get inventory data for the date
    if date:
        inv_data = get_inventory_by_date(date, current_user)
    else:
        inv_data = get_current_inventory(current_user)
    
    # Get activity logs for the station
    logs = get_activity_logs(date=date, station=station, limit=500)
    
    # Calculate totals
    total_incoming = 0
    total_outgoing = 0
    remaining_stock = {}
    
    if inv_data.get('hasData'):
        incoming = inv_data.get('incoming', {})
        outgoing = inv_data.get('outgoing', {})
        remaining = inv_data.get('remaining', {})
        
        # Calculate totals for this station
        for product_id, stations in incoming.items():
            if station_key in stations:
                total_incoming += stations[station_key]
        
        for product_id, stations in outgoing.items():
            if station_key in stations:
                total_outgoing += stations[station_key]
        
        # Get remaining stock
        for product_id, stations in remaining.items():
            if station_key in stations:
                product = next((p for p in PRODUCTS if p['id'] == product_id), None)
                remaining_stock[product_id] = {
                    "name": product['name'] if product else product_id,
                    "quantity": stations[station_key],
                    "unit": product['unit'] if product else 'Pcs'
                }
    
    # Get sales for the station
    sales_data = []
    sales_col = get_collection('daily_sales')
    if date:
        day_sales = find_one(sales_col, {"_id": date})
        if day_sales:
            sales_data = [s for s in day_sales.get('sales', []) if s.get('station') == station]
    else:
        all_sales = find(sales_col, {})
        for day in all_sales:
            for sale in day.get('sales', []):
                if sale.get('station') == station:
                    sale['date'] = day.get('_id')
                    sales_data.append(sale)
    
    # Calculate total revenue from sales
    total_revenue = sum(s.get('total', 0) for s in sales_data)
    
    # Get expenses for the station
    expenses_data = []
    exp_col = get_collection('daily_expenses')
    if date:
        day_exp = find_one(exp_col, {"_id": date})
        if day_exp:
            expenses_data = [e for e in day_exp.get('expenses', []) if e.get('station') == station]
    else:
        all_exp = find(exp_col, {})
        for day in all_exp:
            for exp in day.get('expenses', []):
                if exp.get('station') == station:
                    exp['date'] = day.get('_id')
                    expenses_data.append(exp)
    
    total_expenses = sum(e.get('amount', 0) for e in expenses_data)
    
    return {
        "station": station,
        "date": date if date else "Current",
        "total_incoming": total_incoming,
        "total_outgoing": total_outgoing,
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_income": total_revenue - total_expenses,
        "remaining_stock": remaining_stock,
        "sales": sales_data[:100],
        "expenses": expenses_data[:100],
        "activity_logs": logs[:100],
        "generated_at": datetime.now().isoformat()
    }

# ============================================================
# PRODUCTS ENDPOINT
# ============================================================

@app.get("/api/products")
def get_products(current_user = Depends(get_current_user)):
    col = get_collection('products')
    return find(col)

@app.get("/api/stations")
def get_stations(current_user = Depends(get_current_user)):
    if current_user.get('role') == 'supervisor':
        col = get_collection('stations')
        return [item['name'] for item in find(col)]
    else:
        return current_user.get('stations', [])

@app.get("/api/employees")
def get_employees(current_user = Depends(get_current_user)):
    col = get_collection('employees')
    
    if current_user.get('role') == 'supervisor':
        employees = find(col, {})
    else:
        user_stations = current_user.get('stations', [])
        employees = find(col, {"stations": {"$in": user_stations}})
    
    for emp in employees:
        emp.pop('password', None)
    
    return employees

@app.get("/api/employees/credentials")
def get_employee_credentials(current_user = Depends(require_supervisor)):
    col = get_collection('employees')
    employees = find(col, {})
    
    for emp in employees:
        emp.pop('password', None)
        emp['login_method'] = "Email + Employee ID (No password)"
        emp['login_hint'] = f"Email: {emp.get('email')} | ID: {emp.get('id')}"
    
    return employees

# ============================================================
# SALES ENDPOINTS
# ============================================================

@app.get("/api/sales/{date}")
def get_sales_by_date(date: str, current_user = Depends(get_current_user)):
    col = get_collection('daily_sales')
    result = find_one(col, {"_id": date})
    
    if not result:
        return {"date": date, "sales": [], "hasData": False}
    
    sales = result.get("sales", [])
    
    if current_user.get('role') == 'supervisor':
        return {
            "date": date,
            "sales": sales,
            "hasData": True
        }
    
    user_stations = current_user.get('stations', [])
    filtered_sales = [s for s in sales if s.get('station') in user_stations]
    
    return {
        "date": date,
        "sales": filtered_sales,
        "hasData": True
    }

@app.post("/api/sales")
def create_sale(sale: SaleCreate, current_user = Depends(get_current_user)):
    if current_user.get('role') != 'store_keeper':
        raise HTTPException(status_code=403, detail="Store keeper access required")
    
    user_stations = current_user.get('stations', [])
    if sale.station not in user_stations:
        raise HTTPException(status_code=403, detail=f"Cannot sell at {sale.station}. Your stations: {', '.join(user_stations)}")
    
    date_str = sale.date or datetime.now().strftime("%Y-%m-%d")
    new_sale = {
        "station": sale.station,
        "product_id": sale.product_id,
        "quantity": sale.quantity,
        "price": sale.price,
        "total": sale.total,
        "employee_id": current_user.get('id'),
        "employee_name": current_user.get('full_name'),
        "timestamp": datetime.now().isoformat()
    }
    
    col = get_collection('daily_sales')
    existing = find_one(col, {"_id": date_str})
    
    if existing:
        if db is not None:
            col.update_one({"_id": date_str}, {"$push": {"sales": new_sale}})
    else:
        if db is not None:
            col.insert_one({"_id": date_str, "date": date_str, "sales": [new_sale]})
    
    employees_col = get_collection('employees')
    update_one(employees_col, {"id": current_user['id']}, {"$set": {"last_active": datetime.now().isoformat(), "status": "online"}})
    
    return {"success": True, "sale": new_sale, "date": date_str}

# ============================================================
# EXPENSES ENDPOINTS
# ============================================================

@app.get("/api/expenses/{date}")
def get_expenses_by_date(date: str, current_user = Depends(get_current_user)):
    col = get_collection('daily_expenses')
    result = find_one(col, {"_id": date})
    
    if not result:
        return {"date": date, "expenses": [], "hasData": False}
    
    expenses = result.get("expenses", [])
    
    if current_user.get('role') == 'supervisor':
        return {
            "date": date,
            "expenses": expenses,
            "hasData": True
        }
    
    user_stations = current_user.get('stations', [])
    filtered_expenses = [e for e in expenses if e.get('station') in user_stations]
    
    return {
        "date": date,
        "expenses": filtered_expenses,
        "hasData": True
    }

@app.post("/api/expenses")
def create_expense(expense: ExpenseCreate, current_user = Depends(get_current_user)):
    if current_user.get('role') != 'store_keeper':
        raise HTTPException(status_code=403, detail="Store keeper access required")
    
    user_stations = current_user.get('stations', [])
    if expense.station not in user_stations:
        raise HTTPException(status_code=403, detail=f"Cannot add expenses at {expense.station}. Your stations: {', '.join(user_stations)}")
    
    date_str = expense.date or datetime.now().strftime("%Y-%m-%d")
    new_expense = {
        "description": expense.description,
        "amount": expense.amount,
        "station": expense.station,
        "employee_id": current_user.get('id'),
        "employee_name": current_user.get('full_name'),
        "timestamp": datetime.now().isoformat()
    }
    
    col = get_collection('daily_expenses')
    existing = find_one(col, {"_id": date_str})
    
    if existing:
        if db is not None:
            col.update_one({"_id": date_str}, {"$push": {"expenses": new_expense}})
    else:
        if db is not None:
            col.insert_one({"_id": date_str, "date": date_str, "expenses": [new_expense]})
    
    employees_col = get_collection('employees')
    update_one(employees_col, {"id": current_user['id']}, {"$set": {"last_active": datetime.now().isoformat(), "status": "online"}})
    
    return {"success": True, "expense": new_expense, "date": date_str}

# ============================================================
# LEAKAGE ENDPOINTS
# ============================================================

@app.get("/api/leakage/detect")
def detect_leakage(date: Optional[str] = None, current_user = Depends(require_supervisor)):
    """Detect potential revenue leakage events"""
    col = get_collection('leakage_events')
    events = find(col, {})
    
    if date:
        events = [e for e in events if e.get('date') == date]
    
    return {
        "total": len(events),
        "events": events[:100],
        "date_range": date if date else "All dates"
    }

@app.get("/api/leakage/events")
def get_leakage_events(status: Optional[str] = None, date: Optional[str] = None, current_user = Depends(require_supervisor)):
    col = get_collection('leakage_events')
    
    query = {}
    if status:
        query['status'] = status
    if date:
        query['date'] = date
    
    events = find(col, query)
    events.sort(key=lambda x: x.get('detected', ''), reverse=True)
    
    return {
        "total": len(events),
        "events": events[:100]
    }

# ============================================================
# RESOLVE LEAKAGE (IMEREKEBISHWA)
# ============================================================

@app.put("/api/leakage/{event_id}/resolve")
def resolve_leakage(event_id: str, data: dict, current_user = Depends(require_supervisor)):
    col = get_collection('leakage_events')
    
    # Try to find by _id or activity_id
    event = None
    
    # Try by _id first
    try:
        from bson import ObjectId
        event = find_one(col, {"_id": ObjectId(event_id)})
    except:
        pass
    
    if not event:
        # Try by activity_id
        event = find_one(col, {"activity_id": event_id})
    
    if not event:
        # Try by string _id
        event = find_one(col, {"_id": event_id})
    
    if not event:
        raise HTTPException(status_code=404, detail="Leakage event not found")
    
    if db is not None:
        col.update_one(
            {"_id": event["_id"]}, 
            {"$set": {
                "status": "resolved",
                "resolved_by": current_user.get('name', 'Supervisor'),
                "resolution_notes": data.get('notes', ''),
                "resolved_at": datetime.now().isoformat()
            }}
        )
    
    return {"success": True, "message": "Leakage event resolved"}

@app.get("/api/leakage/summary")
def get_leakage_summary(current_user = Depends(require_supervisor)):
    col = get_collection('leakage_events')
    all_events = find(col, {})
    
    total_events = len(all_events)
    pending = len([e for e in all_events if e.get('status') == 'pending'])
    resolved = len([e for e in all_events if e.get('status') == 'resolved'])
    total_discrepancy = sum(e.get('discrepancy', 0) for e in all_events)
    
    return {
        "total_events": total_events,
        "pending": pending,
        "resolved": resolved,
        "total_discrepancy": total_discrepancy
    }

# ============================================================
# ALERTS ENDPOINT
# ============================================================

@app.get("/api/alerts")
def get_alerts(current_user = Depends(get_current_user)):
    """Get current alerts for low stock and other issues"""
    inv_data = get_current_inventory(current_user)
    alerts = []
    
    remaining = inv_data.get('remaining', {})
    
    if current_user.get('role') == 'supervisor':
        stations_to_check = STATIONS_LIST
    else:
        stations_to_check = current_user.get('stations', [])
    
    station_keys = [s.lower().replace(".", "") for s in stations_to_check]
    
    for product_id, stations in remaining.items():
        for station_key, qty in stations.items():
            if station_key in station_keys:
                station_name = station_key.capitalize()
                if station_key == "no5":
                    station_name = "No.5"
                elif station_key == "no6":
                    station_name = "No.6"
                
                product = next((p for p in PRODUCTS if p['id'] == product_id), None)
                product_name = product['name'] if product else product_id
                
                if qty == 0:
                    alerts.append({
                        "type": "critical",
                        "title": "Out of Stock!",
                        "message": f"{product_name} is completely out at {station_name}",
                        "station": station_name,
                        "product": product_name,
                        "quantity": 0
                    })
                elif qty <= 10:
                    alerts.append({
                        "type": "warning",
                        "title": "Low Stock Alert!",
                        "message": f"{product_name} is running low at {station_name} (Only {qty} left)",
                        "station": station_name,
                        "product": product_name,
                        "quantity": qty
                    })
    
    return {"alerts": alerts, "total": len(alerts)}

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db is not None else "fallback",
        "version": "4.2",
        "date_range": "June 1 - July 15, 2026",
        "total_days": 45,
        "features": [
            "Current Inventory View",
            "Revenue Leakage Detection",
            "Employee Performance Tracking",
            "Automated Reconciliation",
            "Real-time Monitoring",
            "Audit Trail",
            "Report Generation"
        ]
    }

@app.get("/")
@app.get("/api")
def root():
    return {
        "status": "online",
        "project": "DESIGN AND DEVELOPMENT OF A DATA-DRIVEN SALES AND INVENTORY ANALYTICS SYSTEM FOR REVENUE LEAKAGE CONTROL",
        "company": "KALUE FIREWORKS - Singida, Tanzania",
        "version": "4.2",
        "data_period": "June 1 - July 15, 2026 (45 days)",
        "features": [
            "Current Inventory View (No date selection needed)",
            "Revenue Leakage Detection",
            "Employee Performance Monitoring",
            "Automated Reconciliation",
            "Real-time Alerts",
            "Audit Trail with Timestamps",
            "Report Generation with Print"
        ],
        "users": {
            "supervisor": {
                "email": "supervisor@kalue.com",
                "role": "Supervisor",
                "access": "Full system access"
            },
            "store_keepers": [
                {"name": "John Mwangi", "stations": ["Shelui"], "email": "shelui@kalue.com", "id": "KAL-001"},
                {"name": "Mary Peter", "stations": ["Mwime"], "email": "mwime@kalue.com", "id": "KAL-002"},
                {"name": "Ali Hassan", "stations": ["Zawadi"], "email": "zawadi@kalue.com", "id": "KAL-003"},
                {"name": "Sarah Kim", "stations": ["No.5", "No.6"], "email": "no5@kalue.com", "id": "KAL-004"}
            ]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)