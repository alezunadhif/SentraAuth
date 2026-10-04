from mfa import get_mfa_status, verifikasi_kode
import bcrypt
from datetime import datetime, timedelta
from db import get_connection
from audit import log_event

# ==========================================
# KONFIGURASI KEAMANAN
# ==========================================
MAX_FAILED_ATTEMPTS = 5      # Batas maksimal gagal login sebelum akun dikunci
LOCKOUT_DURATION_MINUTES = 5  # Berapa lama akun dikunci setelah kena limit


# ==========================================
# BAGIAN 1: HASHING PASSWORD
# ==========================================
def hash_password(plain_password: str) -> str:
    """
    Hash password pakai bcrypt. Salt otomatis di-generate dan
    ditempel di dalam hash-nya, jadi kita gak perlu nyimpen salt
    terpisah di kolom lain.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Bandingin password yang diinput user dengan hash yang tersimpan.
    bcrypt otomatis ekstrak salt dari hashed_password.
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


# ==========================================
# BAGIAN 2: LOGIKA LOCKOUT (ANTI BRUTE FORCE)
# ==========================================
def is_account_locked(locked_until) -> bool:
    if locked_until is None:
        return False
    return datetime.now() < locked_until


def register_failed_attempt(cursor, conn, username: str, current_attempts: int):
    new_attempts = current_attempts + 1

    if new_attempts >= MAX_FAILED_ATTEMPTS:
        lock_time = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        cursor.execute(
            "UPDATE users SET failed_attempts=%s, locked_until=%s WHERE username=%s",
            (new_attempts, lock_time, username)
        )
    else:
        cursor.execute(
            "UPDATE users SET failed_attempts=%s WHERE username=%s",
            (new_attempts, username)
        )
    conn.commit()
    return new_attempts


def reset_failed_attempts(cursor, conn, username: str):
    cursor.execute(
        "UPDATE users SET failed_attempts=0, locked_until=NULL WHERE username=%s",
        (username,)
    )
    conn.commit()


# ==========================================
# BAGIAN 3: PROSES LOGIN UTAMA
# ==========================================
def login(username: str, password: str):
    """
    Return dict data user kalau berhasil, atau None kalau gagal.
    """
    conn = get_connection()
    if not conn:
        print("[ERROR] Tidak bisa terhubung ke database.")
        return None

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT users.id, users.username, users.password_hash,
               users.failed_attempts, users.locked_until,
               roles.role_name
        FROM users
        JOIN roles ON users.role_id = roles.id
        WHERE users.username = %s
    """, (username,))

    user = cursor.fetchone()

    # Sengaja pesan error SAMA PERSIS dengan pesan "password salah" di bawah,
    # supaya attacker gak bisa membedakan username valid vs tidak
    # (mencegah username enumeration).
    if not user:
        print("[GAGAL] Username atau password salah.")
        log_event(username, "login", "failed")
        cursor.close()
        conn.close()
        return None

    if is_account_locked(user['locked_until']):
        sisa_detik = (user['locked_until'] - datetime.now()).seconds
        print(f"[TERKUNCI] Akun ini dikunci karena terlalu banyak percobaan gagal. "
              f"Coba lagi dalam {sisa_detik // 60} menit {sisa_detik % 60} detik.")
        log_event(username, "login", "locked")
        cursor.close()
        conn.close()
        return None

    if verify_password(password, user['password_hash']):
        reset_failed_attempts(cursor, conn, username)
        cursor.close()
        conn.close()

        # Password benar, cek apakah akun ini punya MFA aktif
        mfa_enabled, mfa_secret = get_mfa_status(username)

        if mfa_enabled:
            print("\n[MFA] Akun ini dilindungi Two-Factor Authentication.")
            kode_otp = input("Masukkan kode 6 digit dari app authenticator: ").strip()

            if verifikasi_kode(mfa_secret, kode_otp):
                log_event(username, "login", "success")
                return {
                    "username": user['username'],
                    "role": user['role_name']
                }
            else:
                print("[GAGAL] Kode OTP salah atau kadaluarsa.")
                log_event(username, "mfa_verification", "failed")
                return None
        else:
            log_event(username, "login", "success")
            return {
                "username": user['username'],
                "role": user['role_name']
            }
    else:
        new_attempts = register_failed_attempt(cursor, conn, username, user['failed_attempts'])
        sisa_percobaan = MAX_FAILED_ATTEMPTS - new_attempts

        if sisa_percobaan <= 0:
            print(f"[TERKUNCI] Akun dikunci selama {LOCKOUT_DURATION_MINUTES} menit "
                  f"karena {MAX_FAILED_ATTEMPTS}x gagal berturut-turut.")
            log_event(username, "login", "locked")
        else:
            print(f"[GAGAL] Username atau password salah. Sisa percobaan: {sisa_percobaan}")
            log_event(username, "login", "failed")

        cursor.close()
        conn.close()
        return None