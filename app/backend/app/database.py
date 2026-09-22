"""SQLite repository replacing AWS DynamoDB."""
import sqlite3, uuid
from datetime import datetime, timezone
from threading import Lock
from app.config import settings

def _now(): return datetime.now(timezone.utc).isoformat()

class SQLiteService:
    def __init__(self):
        self.path, self.lock = settings.DATABASE_PATH, Lock(); self._init()
    def _connect(self):
        con = sqlite3.connect(self.path, timeout=30); con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL"); con.execute("PRAGMA foreign_keys=ON"); return con
    def _init(self):
        with self._connect() as con: con.executescript("""
        CREATE TABLE IF NOT EXISTS users(email TEXT PRIMARY KEY,full_name TEXT NOT NULL,role TEXT NOT NULL,password_hash TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS advertisements(run_id TEXT PRIMARY KEY,user_id TEXT NOT NULL,name TEXT NOT NULL,desc TEXT NOT NULL,status TEXT NOT NULL,final_video_uri TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(email));
        CREATE INDEX IF NOT EXISTS ads_user_created ON advertisements(user_id,created_at DESC);""")
    def create_user(self, data):
        now=_now(); item={"email":data["email"].lower(),"full_name":data["full_name"],"role":data.get("role","creator"),"password_hash":data["password_hash"],"created_at":now,"updated_at":now}
        with self.lock,self._connect() as con: con.execute("INSERT INTO users VALUES (:email,:full_name,:role,:password_hash,:created_at,:updated_at)",item)
        return item
    def get_user_by_email(self,email):
        with self._connect() as con: row=con.execute("SELECT * FROM users WHERE email=?",(email.lower(),)).fetchone()
        return dict(row) if row else None
    def create_advertisement(self,user_id,data):
        now=_now(); item={"run_id":data.get("run_id") or str(uuid.uuid4()),"user_id":user_id,"name":data["name"],"desc":data["desc"],"status":data.get("status","DRAFT"),"final_video_uri":data.get("final_video_uri"),"created_at":now,"updated_at":now}
        with self.lock,self._connect() as con: con.execute("INSERT INTO advertisements VALUES (:run_id,:user_id,:name,:desc,:status,:final_video_uri,:created_at,:updated_at)",item)
        return item
    def get_advertisement(self,user_id,run_id):
        with self._connect() as con: row=con.execute("SELECT * FROM advertisements WHERE user_id=? AND run_id=?",(user_id,run_id)).fetchone()
        return dict(row) if row else None
    def get_user_advertisements(self,user_id):
        with self._connect() as con: return [dict(r) for r in con.execute("SELECT * FROM advertisements WHERE user_id=? ORDER BY created_at DESC",(user_id,))]
    def get_user_advertisements_by_status(self,user_id,status): return [x for x in self.get_user_advertisements(user_id) if x["status"]==status]
    def update_advertisement(self,user_id,run_id,updates):
        clean={k:v for k,v in updates.items() if k in {"status","final_video_uri"}}
        if not clean:return True
        clean["updated_at"]=_now(); assignments=",".join(f"{k}=?" for k in clean)
        with self.lock,self._connect() as con: cur=con.execute(f"UPDATE advertisements SET {assignments} WHERE user_id=? AND run_id=?",(*clean.values(),user_id,run_id))
        return cur.rowcount==1

dynamodb_service=SQLiteService()
