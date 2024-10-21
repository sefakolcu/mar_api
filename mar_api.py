from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import sqlite3

app = FastAPI()

def init_db():
    conn = sqlite3.connect("vessels.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS data (id INTEGER PRIMARY KEY, eta TEXT, ship_name TEXT, ship_type TEXT, port TEXT, port_loco TEXT, port_link_loco TEXT, ship_val_code TEXT);''')
    conn.close()

    conn = sqlite3.connect("usraccounts.db")
    conn.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY,
        username TEXT NULL, 
        apikey TEXT, 
        usrfingerprint TEXT NULL, 
        usedbefore TEXT DEFAULT 'notused'
    );''')
    conn.close()

    conn = sqlite3.connect("adminaccount.db")
    conn.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY, 
        username TEXT,
        adminkey TEXT, 
        usrfingerprint TEXT NULL, 
        adminpw TEXT NULL
    );''')
    conn.close()

init_db()


def authenticate(username: str, apikey: str, usrfingerprint: str):
    try:
        conn = sqlite3.connect("usraccounts.db")
        cursor = conn.cursor()
        cursor.execute("SELECT apikey, usrfingerprint FROM accounts WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            raise HTTPException(status_code=401, detail="User not found")

        stored_apikey, stored_usrfingerprint = result

        if apikey != stored_apikey or (stored_usrfingerprint and usrfingerprint != stored_usrfingerprint):
            raise HTTPException(status_code=401, detail="Invalid API key or fingerprint")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_current_user(
    username: str = Header(...),
    apikey: str = Header(...),
    usrfingerprint: str = Header(None)
):
    authenticate(username, apikey, usrfingerprint)


class Item(BaseModel):
    eta: str
    ship_name: str
    ship_type: str
    port: str
    port_loco: str
    port_link_loco: str
    ship_val_code: str


@app.post("/save_input/")
async def save_input(item: Item, user: dict = Depends(get_current_user)):
    try:
        conn = sqlite3.connect("vessels.db")
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO data (eta, ship_name, ship_type, port, port_loco, port_link_loco, ship_val_code) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (item.eta, item.ship_name, item.ship_type, item.port, item.port_loco, item.port_link_loco, item.ship_val_code))
        conn.commit()
        conn.close()
        return {"message": "Input saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_input/")
async def get_input(user: dict = Depends(get_current_user)):
    try:
        conn = sqlite3.connect("vessels.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data")
        rows = cursor.fetchall()
        conn.close()
        
        results = [
            {
                "id": row[0],
                "eta": row[1],
                "ship_name": row[2],
                "ship_type": row[3],
                "port": row[4],
                "port_loco": row[5],
                "port_link_loco": row[6],
                "ship_val_code": row[7]
            }
            for row in rows
        ]
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AdminAuth(BaseModel):
    username: str
    adminkey: str
    usrfingerprint: str
    adminpw: str

def generate_api_key(length: int = 16) -> str:
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

@app.post("/add_apikey/")
async def add_apikey(admin_auth: AdminAuth):
    try:
        conn = sqlite3.connect("adminaccount.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ? AND adminkey = ? AND usrfingerprint = ? AND adminpw = ?",
                       (admin_auth.username, admin_auth.adminkey, admin_auth.usrfingerprint, admin_auth.adminpw))
        admin = cursor.fetchone()
        conn.close()

        if not admin:
            raise HTTPException(status_code=401, detail="Invalid admin credentials")

        new_apikey = generate_api_key()

        conn = sqlite3.connect("usraccounts.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO accounts (username, apikey, usrfingerprint, usedbefore) VALUES (NULL, ?, NULL, 'notused')",
                       (new_apikey))
        conn.commit()
        conn.close()

        return {"message": "API key added successfully", "apikey": new_apikey}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))