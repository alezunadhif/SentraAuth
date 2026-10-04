from db import get_connection
from ui import tabel_audit_log, print_error, print_warning


def log_event(username: str, event_type: str, status: str, ip_or_host: str = "localhost-cli"):
    """
    Catat satu event ke tabel audit_log.
    Fungsi ini SENGAJA tidak melempar exception ke pemanggilnya kalau logging
    gagal (misal database down), karena kegagalan logging tidak boleh
    menghentikan proses utama (login, dsb). Cukup di-print sebagai warning.
    """
    conn = get_connection()
    if not conn:
        print("[WARNING] Audit log gagal dicatat: tidak bisa konek ke database.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_log (username, event_type, status, ip_or_host) VALUES (%s, %s, %s, %s)",
            (username, event_type, status, ip_or_host)
        )
        conn.commit()
        cursor.close()
    except Exception as err:
        print(f"[WARNING] Audit log gagal dicatat: {err}")
    finally:
        conn.close()


def lihat_log(limit: int = 20):
    """
    Tampilkan N event terakhir dari audit_log, urut dari yang terbaru.
    """
    conn = get_connection()
    if not conn:
        print_error("Tidak bisa terhubung ke database.")
        return

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT username, event_type, status, created_at FROM audit_log "
        "ORDER BY created_at DESC LIMIT %s", (limit,)
    )
    logs = cursor.fetchall()
    cursor.close()
    conn.close()

    tabel_audit_log(logs)

   