"""Local demo accounts: salted password hashes and opaque HttpOnly sessions."""
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from pathlib import Path
from fastapi import APIRouter,Request,Response,HTTPException
from pydantic import BaseModel,Field
from app.config import settings

router=APIRouter(prefix="/auth",tags=["accounts"])
COOKIE="daleel_session"
class Credentials(BaseModel):
    username:str=Field(pattern=r"^[a-zA-Z0-9_]{3,32}$")
    password:str=Field(min_length=8,max_length=128)
class ProfileUpdate(BaseModel):
    study_year:int=Field(ge=1,le=6)
    completed:list[str]=Field(default_factory=list,max_length=200)

class Accounts:
    def __init__(self,path):self.path=Path(path)
    def connect(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        con=sqlite3.connect(self.path,timeout=10);con.row_factory=sqlite3.Row
        con.executescript("""CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY,salt TEXT NOT NULL,password_hash TEXT NOT NULL,study_year INTEGER,completed TEXT NOT NULL DEFAULT '[]');
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,username TEXT NOT NULL,expires REAL NOT NULL);""")
        return con
    @staticmethod
    def password_hash(password,salt):return hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt),310000).hex()
    @staticmethod
    def profile(row):return {"username":row["username"],"study_year":row["study_year"],"completed":json.loads(row["completed"])}
    def register(self,username,password):
        salt=secrets.token_hex(16)
        try:
            with self.connect() as con:con.execute("INSERT INTO users(username,salt,password_hash) VALUES(?,?,?)",(username.lower(),salt,self.password_hash(password,salt)))
        except sqlite3.IntegrityError:raise HTTPException(409,"اسم المستخدم مستخدم بالفعل. اختر اسماً آخر أو سجّل الدخول.") from None
    def login(self,username,password):
        with self.connect() as con:row=con.execute("SELECT * FROM users WHERE username=?",(username.lower(),)).fetchone()
        salt=row["salt"] if row else "0"*32
        valid=hmac.compare_digest(self.password_hash(password,salt),row["password_hash"] if row else "0"*64)
        if not row or not valid:raise HTTPException(401,"اسم المستخدم أو كلمة المرور غير صحيحة.")
        token=secrets.token_urlsafe(32)
        with self.connect() as con:
            con.execute("DELETE FROM sessions WHERE expires<?",(time.time(),))
            con.execute("INSERT INTO sessions VALUES(?,?,?)",(hashlib.sha256(token.encode()).hexdigest(),row["username"],time.time()+7*86400))
        return token,self.profile(row)
    def current(self,token):
        digest=hashlib.sha256((token or "").encode()).hexdigest()
        with self.connect() as con:
            row=con.execute("SELECT users.* FROM users JOIN sessions USING(username) WHERE token_hash=? AND expires>?",(digest,time.time())).fetchone()
        if not row:raise HTTPException(401,"يرجى تسجيل الدخول للمتابعة.")
        return self.profile(row)
    def save(self,token,year,completed):
        user=self.current(token)
        with self.connect() as con:con.execute("UPDATE users SET study_year=?,completed=? WHERE username=?",(year,json.dumps(list(dict.fromkeys(completed))),user["username"]))
        return self.current(token)
    def logout(self,token):
        with self.connect() as con:con.execute("DELETE FROM sessions WHERE token_hash=?",(hashlib.sha256((token or "").encode()).hexdigest(),))

def store():return Accounts(settings().indexes/"accounts.sqlite")
def set_cookie(response,token):response.set_cookie(COOKIE,token,httponly=True,samesite="strict",max_age=7*86400,path="/")
@router.post("/register")
def register(body:Credentials,response:Response):
    db=store();db.register(body.username,body.password);token,user=db.login(body.username,body.password);set_cookie(response,token);return user
@router.post("/login")
def login(body:Credentials,response:Response):
    token,user=store().login(body.username,body.password);set_cookie(response,token);return user
@router.get("/me")
def me(request:Request):return store().current(request.cookies.get(COOKIE))
@router.post("/logout")
def logout(request:Request,response:Response):
    store().logout(request.cookies.get(COOKIE));response.delete_cookie(COOKIE,path="/");return {"status":"logged_out"}
@router.post("/profile")
def profile(body:ProfileUpdate,request:Request):
    token=request.cookies.get(COOKIE);store().current(token)
    from app.main import ready
    known={c["course_code"] for c in ready()[0].courses}
    if set(body.completed)-known:raise HTTPException(422,"تتضمن القائمة رمز مساق غير موجود في الخطة.")
    return store().save(token,body.study_year,body.completed)
