import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Load semua variabel dari file .env ke environment
load_dotenv()

def get_connection():
    """
    Bikin koneksi baru ke database MySQL.
    Kredensial diambil dari .env, BUKAN hardcode di sini.
    Return None kalau gagal connect, biar pemanggil bisa handle error-nya.
    """
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return conn
    except Error as err:
        print(f"[ERROR] Gagal konek ke database: {err}")
        return None


# Blok ini cuma jalan kalau db.py dijalanin langsung (bukan diimport),
# fungsinya buat testing koneksi doang
if __name__ == "__main__":
    conn = get_connection()
    if conn and conn.is_connected():
        print("[OK] Koneksi ke database berhasil!")
        print(f"Server version: {conn.server_info}")
        conn.close()
    else:
        print("[FAIL] Koneksi gagal, cek lagi .env atau MySQL service.")