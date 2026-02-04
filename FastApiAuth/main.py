from typing import Annotated
from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
import jwt
# Import necessary modules and classes
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

passwordHash=PasswordHash.recommended()
sqlite_file_name = "newDB.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    full_name: str | None = None
    email: str = Field(index=True)
    disabled: bool = False

# 2. Datenbank-Modell: So wird es in der DB gespeichert (inkl. ID & Passwort)
class UserDb(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str

# 3. API Response Modell: Was der Client zurückbekommt (mit ID, ohne Passwort)
class UserDbPublic(UserBase):
    id: int

# 4. API Request Modell: Was der Client sendet, wenn er einen User erstellt
class UserDbCreate(UserBase):
    hashed_password: str  # Hier im Klartext, wird vor dem Speichern gehasht

# 5. API Update Modell: Alle Felder optional für Teil-Updates (PATCH)
class UserDbUpdate(SQLModel):
    username: str | None = None
    full_name: str | None = None
    email: str | None = None
    password: str | None = None # Falls das Passwort geändert werden soll
    disabled: bool | None = None

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TodoItem(BaseModel):
    title: Annotated[str, Query(min_length=1)]
    description: str | None = None
    completed: bool = False


class TodoItemDB(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    content: str | None = None
    completed: bool = False
    owner_id: int | None = Field(default=2, foreign_key="userdb.id")

app = FastAPI()


SECRETKEY = "0b451f23b7a8a9aaa19b24f36e22a90a87c6b9d83c63b8db26d8529b6f1ddb0d"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


async def get_current_user(session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]):
    falscheEingabe_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRETKEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise falscheEingabe_exception
    except:
        raise falscheEingabe_exception
    user = get_user(session, username=username)
    if user is None:
        raise falscheEingabe_exception
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)],):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user





@app.patch("/users/{user_id}", response_model=UserDbPublic)
def read_user(user_id: int,hero: UserDbUpdate, session: SessionDep):
    user = session.get(UserDb, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = hero.model_dump(exclude_unset=True)
    if "password" in user_data:
        hashed_password = get_password_hash(user_data.pop("password"))
        user.hashed_password = hashed_password

    user.sqlmodel_update(user_data)


    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, session: SessionDep):
    user = session.get(UserDb, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"ok": True}



@app.post("/create_user/", response_model=UserDbPublic)
def create_user(user: UserDbCreate, session: SessionDep):
    user = UserDb.model_validate(user)
    user.hashed_password = get_password_hash(user.hashed_password)


    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.get("/users/", response_model=list[UserDbPublic])
def read_users(session: SessionDep):
    users = session.exec(select(UserDb)).all()
    return users


@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/todo/")
async def create_todo_item(
        item: TodoItem,current_user: Annotated[UserDb, Depends(get_current_active_user)],
        session: SessionDep):
    # Wir nehmen die Daten vom Item und fügen die owner_id des Users hinzu
    db_item = TodoItemDB(**item.model_dump(), owner_id=current_user.id)

    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@app.get("/items/{item_id}")
async def read_item(
        item_id: int,
        current_user: Annotated[UserDb, Depends(get_current_active_user)],
        session: SessionDep
):
    statement = select(TodoItemDB).where(
        TodoItemDB.id == item_id,
        TodoItemDB.owner_id == current_user.id  # Sicherstellen, dass es dem User gehört
    )
    item = session.exec(statement).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item nicht gefunden oder Zugriff verweigert")
    return item




@app.get("/items/")
async def read_items(
        current_user: Annotated[UserDb, Depends(get_current_active_user)],
        session: SessionDep
):
    # Wichtig: Wir filtern hier mit .where() nach der ID des aktuellen Users
    statement = select(TodoItemDB).where(TodoItemDB.owner_id == current_user.id)
    items = session.exec(statement).all()

    if items:
        return items
    else:
        return {"error": "Keine Items gefunden"}





def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRETKEY, algorithm=ALGORITHM)

    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return passwordHash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return passwordHash.hash(password)


def get_user(session: Session, username: str):
    statement = select(UserDb).where(UserDb.username == username)


    return session.exec(statement).first()


def authenticate_user(session: Session, username: str, password: str):
    user = get_user(session, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user




def decodeToken(token: str):
    try:
        payload = jwt.decode(token, SECRETKEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        return None
    return token_data





@app.post("/token")
async def login_for_access_token(
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="falscher username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")





@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user