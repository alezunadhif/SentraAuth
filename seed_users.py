"""
Skrip ini HANYA untuk isi data awal (seed) ke tabel users.
Jalankan SEKALI SAJA setelah tabel dibuat. Kalau dijalankan berkali-kali,
akan gagal karena username sudah ada (UNIQUE constraint), itu wajar.
"""

from db import get_connection
from auth import hash_password

def seed():
    conn = get_connection()
    if not conn:
        print("[ERROR] Tidak bisa konek ke database.")
        return

    cursor = conn.cursor()

    # role_id: 1 = admin, 2 = user (sesuai INSERT roles yang kita jalanin di MySQL kemarin)
    data_default = [
        ("admin", hash_password("adminjuga"), 1),
        ("budi", hash_password("budi123"), 2),
    ]

    for username, pw_hash, role_id in data_default:
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role_id) VALUES (%s, %s, %s)",
                (username, pw_hash, role_id)
            )
            print(f"[OK] Akun '{username}' berhasil dibuat.")
        except Exception as err:
            print(f"[SKIP] Akun '{username}' gagal dibuat (kemungkinan sudah ada): {err}")

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    seed()
