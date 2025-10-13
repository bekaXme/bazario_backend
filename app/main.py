from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel import SQLModel, Field, Session, create_engine, select
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import shutil

# -------------------- CONFIG --------------------
DATABASE_URL = "sqlite:///./bazario.db"
engine = create_engine(DATABASE_URL, echo=False)

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
SECRET_KEY = "CHANGE_THIS_SECRET_KEY_TO_ENV"  # replace with env var
ALGORITHM = "HS256"

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

app = FastAPI(title="Bazario Backend API")

# -------------------- MODELS --------------------
class UserBase(SQLModel):
    username: str
    full_name: Optional[str] = None
    is_admin: bool = False

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: Optional[str] = None
    hashed_password: str
    coins: int = 0

class UserCreate(SQLModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class Token(SQLModel):
    access_token: str
    token_type: str

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    price: int
    image_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CoinRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    amount: int
    image_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed: bool = False
    approved: Optional[bool] = None
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[int] = None

class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    title: str
    message: str
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# -------------------- DB INIT --------------------
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

create_db_and_tables()

# -------------------- UTILITIES --------------------
def get_session():
    with Session(engine) as session:
        yield session

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# -------------------- AUTH DEPENDENCIES --------------------
async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
    return user

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

# -------------------- AUTH ENDPOINTS --------------------
@app.post("/register", response_model=dict,)
def register(user_create: UserCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.username == user_create.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    user = User(
        username=user_create.username,
        email=user_create.email,
        phone_number=user_create.phone_number,
        full_name=user_create.full_name,
        hashed_password=get_password_hash(user_create.password),
        is_admin=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "username": user.username}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")

# -------------------- USER ENDPOINTS --------------------
@app.get("/users", response_model=List[UserBase])
def get_users(session: Session = Depends(get_session), admin: User = Depends(get_admin_user)):
    users = session.exec(select(User)).all()
    return [UserBase(username=u.username, full_name=u.full_name, is_admin=u.is_admin) for u in users]

@app.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "coins": current_user.coins,
        "is_admin": current_user.is_admin,
    }

# -------------------- PRODUCT ENDPOINTS --------------------
@app.post("/products", response_model=dict, tags=["products"])
def create_product(
    title: str = Form(...),
    price: int = Form(...),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    admin: User = Depends(get_admin_user),
):
    image_path = None
    if image:
        filename = f"{int(datetime.utcnow().timestamp())}_{image.filename}"
        dest = os.path.join(UPLOAD_DIR, filename)
        with open(dest, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_path = dest
    product = Product(title=title, price=price, description=description, image_path=image_path)
    session.add(product)
    session.commit()
    session.refresh(product)
    return {"id": product.id, "title": product.title}

@app.get("/products", response_model=List[Product], tags=["products"])
def list_products(session: Session = Depends(get_session)):
    prods = session.exec(select(Product)).all()
    return prods

@app.get("/products/{product_id}", response_model=Product, tags=["products"])
def get_product(product_id: int, session: Session = Depends(get_session)):
    prod = session.get(Product, product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod

@app.delete("/products/{product_id}", tags=["products"])
def delete_product(product_id: int, session: Session = Depends(get_session), admin: User = Depends(get_admin_user)):
    prod = session.get(Product, product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(prod)
    session.commit()
    return {"ok": True}

# -------------------- COIN PURCHASE FLOW --------------------
@app.post("/coins/request", response_model=dict)
def request_coins(amount: int = Form(...), image: UploadFile = File(...), current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # save image
    filename = f"coinreq_{current_user.id}_{int(datetime.utcnow().timestamp())}_{image.filename}"
    dest = os.path.join(UPLOAD_DIR, filename)
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    req = CoinRequest(user_id=current_user.id, amount=amount, image_path=dest)
    session.add(req)
    session.commit()
    session.refresh(req)
    # create notification for admins (for simplicity, create notifications for all admins)
    admins = session.exec(select(User).where(User.is_admin == True)).all()
    for a in admins:
        note = Notification(user_id=a.id, title="New coin request", message=f"User {current_user.username} requested {amount} coins. Request id: {req.id}")
        session.add(note)
    session.commit()
    return {"request_id": req.id, "status": "pending"}

@app.get("/coins/requests", response_model=List[CoinRequest])
def list_coin_requests(session: Session = Depends(get_session), admin: User = Depends(get_admin_user)):
    reqs = session.exec(select(CoinRequest)).all()
    return reqs

@app.post("/coins/requests/{req_id}/review", response_model=dict)
def review_coin_request(req_id: int, approve: bool = Form(...), current_admin: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    req = session.get(CoinRequest, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.reviewed:
        raise HTTPException(status_code=400, detail="Already reviewed")
    req.reviewed = True
    req.approved = approve
    req.reviewed_at = datetime.utcnow()
    req.reviewer_id = current_admin.id
    session.add(req)
    if approve:
        user = session.get(User, req.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.coins += req.amount
        session.add(user)
        # notify user
        note = Notification(user_id=user.id, title="Coin request approved", message=f"Your request #{req.id} for {req.amount} coins was approved.")
        session.add(note)
    else:
        user = session.get(User, req.user_id)
        note = Notification(user_id=user.id, title="Coin request rejected", message=f"Your request #{req.id} for {req.amount} coins was rejected.")
        session.add(note)
    session.commit()
    return {"ok": True, "approved": approve}

# -------------------- NOTIFICATIONS --------------------
@app.get("/notifications", response_model=List[Notification])
def get_notifications(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    notes = session.exec(select(Notification).where(Notification.user_id == current_user.id)).all()
    return notes

@app.post("/notifications/{note_id}/read")
def mark_notification_read(note_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    note = session.get(Notification, note_id)
    if not note or note.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    note.read = True
    session.add(note)
    session.commit()
    return {"ok": True}

# -------------------- ADMIN QUICK UTILITIES --------------------
@app.post("/admin/create-demo-admin")
def create_demo_admin(session: Session = Depends(get_session)):
    # convenience: create admin if not exists
    existing = session.exec(select(User).where(User.username == "admin")).first()
    if existing:
        return {"msg": "admin already exists"}
    admin = User(username="admin", hashed_password=get_password_hash("adminpass"), email=None, full_name="Admin", is_admin=True, coins=0)
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return {"id": admin.id, "username": admin.username}

# -------------------- STARTUP --------------------
@app.on_event("startup")
def startup_event():
    # ensure upload dir exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

# -------------------- END --------------------
