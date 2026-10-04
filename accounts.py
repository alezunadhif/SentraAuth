from db import get_connection
from auth import hash_password, verify_password
from audit import log_event
from ui import tabel_akun, print_success, print_error, print_warning, print_info


def lihat_akun():
    conn = get_connection()
    if not conn:
        print_error("Tidak bisa terhubung ke database.")
        return

    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT users.username, roles.role_name
        FROM users
        JOIN roles ON users.role_id = roles.id
        ORDER BY users.username
    """)
    akun_list = cursor.fetchall()
    cursor.close()
    conn.close()

    tabel_akun(akun_list)


def tambah_akun(actor_username: str):
    print("\n=== TAMBAH AKUN BARU ===")
    username = input("Username baru: ").strip()
    password = input("Password baru: ").strip()
    role_input = input("Role (admin/analyst): ").strip().lower()

    if role_input not in ['admin', 'analyst']:
        print("Gagal: Role tidak valid! Harus 'admin' atau 'analyst'.")
        return

    if len(password) < 8:
        print("Gagal: Password minimal 8 karakter.")
        return

    conn = get_connection()
    if not conn:
        print("[ERROR] Tidak bisa terhubung ke database.")
        return

    cursor = conn.cursor()

    cursor.execute("SELECT id FROM roles WHERE role_name = %s", (role_input,))
    role_row = cursor.fetchone()
    role_id = role_row[0]

    try:
        pw_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, role_id) VALUES (%s, %s, %s)",
            (username, pw_hash, role_id)
        )
        conn.commit()
        print(f"Berhasil! Akun [{username}] ditambahkan sebagai [{role_input.upper()}].")
        log_event(actor_username, "account_created", "success")
    except Exception as err:
        print(f"Gagal: Username '{username}' sudah terdaftar di Database!")
        log_event(actor_username, "account_created", "failed")
    finally:
        cursor.close()
        conn.close()


def hapus_akun(actor_username: str):
    print("\n=== HAPUS AKUN ===")
    target_user = input("Masukkan username yang akan dihapus: ").strip()

    if target_user == actor_username:
        print("Gagal: Anda tidak boleh menghapus akun sendiri saat sedang login!")
        return

    conn = get_connection()
    if not conn:
        print("[ERROR] Tidak bisa terhubung ke database.")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s", (target_user,))
    if not cursor.fetchone():
        print("Gagal: Username tidak ditemukan!")
        cursor.close()
        conn.close()
        return

    konfirmasi = input(f"Yakin ingin menghapus '{target_user}'? (y/n): ").strip().lower()
    if konfirmasi == 'y':
        cursor.execute("DELETE FROM users WHERE username=%s", (target_user,))
        conn.commit()
        print(f"Berhasil! Akun '{target_user}' telah dihapus.")
        log_event(actor_username, "account_deleted", "success")
    else:
        print("Penghapusan dibatalkan.")

    cursor.close()
    conn.close()


def renew_password(actor_username: str):
    print("\n=== RENEW PASSWORD ===")
    target_user = input("Masukkan username yang akan diubah passwordnya: ").strip()

    conn = get_connection()
    if not conn:
        print("[ERROR] Tidak bisa terhubung ke database.")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s", (target_user,))
    if not cursor.fetchone():
        print("Gagal: Username tidak ditemukan!")
        cursor.close()
        conn.close()
        return

    pass_baru = input(f"Masukkan password baru untuk '{target_user}': ").strip()
    pass_konfirmasi = input("Konfirmasi password baru: ").strip()

    if pass_baru != pass_konfirmasi:
        print("Gagal: Konfirmasi password tidak cocok! Silakan coba lagi.")
        cursor.close()
        conn.close()
        return

    if len(pass_baru) < 8:
        print("Gagal: Password minimal 8 karakter.")
        cursor.close()
        conn.close()
        return

    pw_hash = hash_password(pass_baru)
    cursor.execute(
        "UPDATE users SET password_hash=%s, failed_attempts=0, locked_until=NULL WHERE username=%s",
        (pw_hash, target_user)
    )
    conn.commit()
    print(f"Berhasil! Password untuk akun '{target_user}' telah diperbarui.")
    log_event(actor_username, "password_renewed", "success")

    cursor.close()
    conn.close()

def ganti_password_sendiri(username: str):
    """
    Self-service password change. Beda dari renew_password() (yang dipakai admin
    untuk mengubah password akun ORANG LAIN), function ini WAJIB verifikasi
    password lama dulu, supaya kalau ada sesi login yang belum di-logout,
    orang lain gak bisa asal ganti password pemilik akun.
    """
    print("\n=== GANTI PASSWORD SAYA ===")

    conn = get_connection()
    if not conn:
        print("[ERROR] Tidak bisa terhubung ke database.")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username=%s", (username,))
    row = cursor.fetchone()

    if not row:
        print("[ERROR] Akun tidak ditemukan.")
        cursor.close()
        conn.close()
        return

    password_lama_input = input("Masukkan password lama: ").strip()

    if not verify_password(password_lama_input, row[0]):
        print("Gagal: Password lama salah. Ganti password dibatalkan.")
        log_event(username, "self_password_change", "failed")
        cursor.close()
        conn.close()
        return

    password_baru = input("Masukkan password baru: ").strip()
    password_konfirmasi = input("Konfirmasi password baru: ").strip()

    if password_baru != password_konfirmasi:
        print("Gagal: Konfirmasi password tidak cocok.")
        cursor.close()
        conn.close()
        return

    if len(password_baru) < 8:
        print("Gagal: Password minimal 8 karakter.")
        cursor.close()
        conn.close()
        return

    pw_hash = hash_password(password_baru)
    cursor.execute(
        "UPDATE users SET password_hash=%s WHERE username=%s",
        (pw_hash, username)
    )
    conn.commit()
    print("Berhasil! Password Anda telah diperbarui. Silakan login ulang.")
    log_event(username, "self_password_change", "success")

    cursor.close()
    conn.close()    