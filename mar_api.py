from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

def init_db():
    conn = sqlite3.connect("vessels.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS data (id INTEGER PRIMARY KEY, eta TEXT, ship_name TEXT, ship_type TEXT, port TEXT, port_loco TEXT, port_link_loco TEXT, ship_val_code TEXT);''')
    conn.close()

init_db()

# Pydantic model for input
class Item(BaseModel):
    eta: str
    ship_name: str
    ship_type: str
    port: str
    port_loco: str
    port_link_loco: str
    ship_val_code: str

@app.post("/save_input/")
async def save_input(item: Item):
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
async def get_input():
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
