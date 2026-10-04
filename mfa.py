import pyotp
import qrcode
from db import get_connection
from audit import log_event

APP_NAME = "SentraAuth-CLI"


def generate_secret() -> str:
    """
    Generate secret key random base32, ini yang jadi 'kunci rahasia'
    yang dishare antara server dan app authenticator user.
    """
    return pyotp.random_base32()


def tampilkan_qr_terminal(secret: str, username: str):
    """
    Bikin URI provisioning standar (otpauth://...) dan render sebagai
    QR code ASCII langsung di terminal, tanpa perlu simpan file gambar.
    """
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=username, issuer_name=APP_NAME)

    qr = qrcode.QRCode()
    qr.add_data(uri)
    qr.make()
    qr.print_ascii(invert=True)

    print(f"\nAtau masukkan manual di app authenticator:")
    print(f"Secret Key: {secret}")


def verifikasi_kode(secret: str, kode_input: str) -> bool:
    """
    Cek apakah kode 6 digit yang diinput user cocok dengan yang
    dihasilkan dari secret + waktu sekarang.
    valid_window=1 memberi toleransi pergeseran waktu +/- 30 detik.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(kode_input, valid_window=1)


def setup_mfa(username: str):
    """
    Alur enrollment MFA. Secret BARU DISIMPAN ke database setelah user
    berhasil membuktikan bisa generate kode yang benar dari app-nya.
    """
    conn = get_connection()
    if not conn:
        print("[ERROR] Tidak bisa terhubung ke database.")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT mfa_enabled FROM users WHERE username=%s", (username,))
    row = cursor.fetchone()

    if row and row[0] == 1:
        print("[INFO] MFA sudah aktif untuk akun ini.")
        cursor.close()
        conn.close()
        return

    print("\n=== SETUP MFA (Two-Factor Authentication) ===")
    print("Scan QR code di bawah ini menggunakan Google Authenticator, Authy, atau app sejenis.\n")

    secret_sementara = generate_secret()
    tampilkan_qr_terminal(secret_sementara, username)

    print("\nSetelah discan, masukkan kode 6 digit yang muncul di app Anda untuk konfirmasi.")
    kode_konfirmasi = input("Kode OTP: ").strip()

    if verifikasi_kode(secret_sementara, kode_konfirmasi):
        cursor.execute(
            "UPDATE users SET mfa_secret=%s, mfa_enabled=1 WHERE username=%s",
            (secret_sementara, username)
        )
        conn.commit()
        print("\n[BERHASIL] MFA berhasil diaktifkan untuk akun Anda.")
        log_event(username, "mfa_enrollment", "success")
    else:
        print("\n[GAGAL] Kode tidak cocok. Setup MFA dibatalkan, silakan coba lagi.")
        log_event(username, "mfa_enrollment", "failed")

    cursor.close()
    conn.close()


def get_mfa_status(username: str):
    """
    Return tuple (mfa_enabled: bool, mfa_secret: str atau None).
    Dipakai di auth.py saat proses login untuk cek apakah perlu
    minta kode OTP tambahan.
    """
    conn = get_connection()
    if not conn:
        return False, None

    cursor = conn.cursor()
    cursor.execute("SELECT mfa_enabled, mfa_secret FROM users WHERE username=%s", (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return False, None

    return bool(row[0]), row[1]