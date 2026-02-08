import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from pydantic import BaseModel

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Konfigurasi dari https://my.telegram.org
API_ID = 30372921 
API_HASH = '92a808d306bb14ff5908b5f7c9f2194b'

# Kamus untuk menyimpan instance client yang sedang login
active_clients = {}

class LoginData(BaseModel):
    phone: str
    otp: str = None
    password: str = None # Untuk 2FA

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/send-otp")
async def send_otp(data: LoginData):
    # Pastikan folder sessions ada
    if not os.path.exists('sessions'): os.makedirs('sessions')
    
    # Buat client baru untuk nomor tersebut
    client = TelegramClient(f'sessions/{data.phone}', API_ID, API_HASH)
    await client.connect()
    
    # Minta kode OTP
    sent_code = await client.send_code_request(data.phone)
    
    # Simpan client di memori agar bisa digunakan saat verifikasi OTP
    active_clients[data.phone] = {
        "client": client,
        "hash": sent_code.phone_code_hash
    }
    return {"message": "OTP berhasil dikirim ke Telegram Anda"}

@app.post("/verify-login")
async def verify_login(data: LoginData):
    user_session = active_clients.get(data.phone)
    if not user_session:
        return {"error": "Sesi tidak ditemukan. Kirim OTP ulang."}
    
    client = user_session["client"]
    try:
        # Proses login
        await client.sign_in(data.phone, data.otp, phone_code_hash=user_session["hash"])
        return {"message": "Login Berhasil! Sesi telah disimpan di server."}
    
    except SessionPasswordNeededError:
        return {"error": "2FA aktif. Masukkan password akun Anda."}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
