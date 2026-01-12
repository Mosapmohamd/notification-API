from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import requests
from datetime import datetime

app = FastAPI(title="Save Car API")

N8N_WEBHOOK_URL = "https://zeyadashraf.app.n8n.cloud/webhook-test/4a7b074f-237a-4444-bfad-ac6f4fc78211"

DB_CONFIG = {
    "host": "aws-1-ca-central-1.pooler.supabase.com",
    "dbname": "postgres",
    "user": "postgres.fyrinwxwprscqnfrllkq",
    "password": "a7GrPbgPVTssTRC1",
    "port": 5432,
}

class SaveCarRequest(BaseModel):
    ad_link: str


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_car_by_ad_link(ad_link: str):
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT
            title,
            price,
            ad_link,
            status,
            estValue,
            description,
            location,
            odometer,
            source
        FROM all
        WHERE ad_link = %s
        LIMIT 1
    """

    cur.execute(query, (ad_link,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    comments = []

    if row[5]:
        comments.append(row[5])

    if row[6]:
        comments.append(f"Location: {row[6]}")

    if row[7]:
        comments.append(f"KM: {row[7]}")

    if row[8]:
        comments.append(f"Source: {row[8]}")

    return {
        "vehicle_model": row[0],
        "listed_price": row[1],
        "listing_link": row[2],
        "status": row[3] or "New",
        "sells_for": row[4],
        "comments": " | ".join(comments),
    }


@app.post("/save-car")
def save_car(req: SaveCarRequest):
    car = get_car_by_ad_link(req.ad_link)

    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    payload = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "sent_by": "Website",
        "status": car["status"],
        "vehicle_model": car["vehicle_model"],
        "listing_link": car["listing_link"],
        "seller_phone": "",
        "sells_for": car["sells_for"],
        "listed_price": car["listed_price"],
        "target_buy_price": "",
        "seller_lowest_price": "",
        "comments": car["comments"],
    }

    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=10
        )
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="n8n request failed")

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="n8n webhook error")

    return {
        "success": True,
        "data": payload
    }

