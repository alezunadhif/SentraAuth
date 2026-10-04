import os
from datetime import datetime, timedelta
from db import get_connection
from auth import verify_password
from rich.table import Table
from rich.panel import Panel
from ui import console

DEFAULT_ADMIN_PASSWORD = "adminjuga"


def cek_kredensial_default() -> list:
    temuan = []
    conn = get_connection()
    if not conn:
        return temuan

    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT users.username, users.password_hash
        FROM users
        JOIN roles ON users.role_id = roles.id
        WHERE roles.role_name = 'admin'
    """)
    admin_list = cursor.fetchall()
    cursor.close()
    conn.close()

    for admin in admin_list:
        if verify_password(DEFAULT_ADMIN_PASSWORD, admin['password_hash']):
            temuan.append({
                "finding": "Kredensial Default Masih Aktif",
                "severity": "HIGH",
                "status": "FAIL",
                "detail": f"Akun '{admin['username']}' masih menggunakan password default seeding.",
                "rekomendasi": "Segera ganti password akun ini melalui menu Renew Password."
            })

    if not temuan:
        temuan.append({
            "finding": "Kredensial Default Masih Aktif",
            "severity": "HIGH",
            "status": "PASS",
            "detail": "Tidak ada akun admin yang menggunakan password default.",
            "rekomendasi": "-"
        })

    return temuan


def cek_mfa_admin() -> list:
    temuan = []
    conn = get_connection()
    if not conn:
        return temuan

    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT users.username, users.mfa_enabled
        FROM users
        JOIN roles ON users.role_id = roles.id
        WHERE roles.role_name = 'admin'
    """)
    admin_list = cursor.fetchall()
    cursor.close()
    conn.close()

    admin_tanpa_mfa = [a['username'] for a in admin_list if not a['mfa_enabled']]

    if admin_tanpa_mfa:
        temuan.append({
            "finding": "Admin Tanpa MFA",
            "severity": "MEDIUM",
            "status": "FAIL",
            "detail": f"Akun admin berikut belum mengaktifkan MFA: {', '.join(admin_tanpa_mfa)}",
            "rekomendasi": "Aktifkan MFA melalui menu 'Aktifkan MFA (2FA)' setelah login."
        })
    else:
        temuan.append({
            "finding": "Admin Tanpa MFA",
            "severity": "MEDIUM",
            "status": "PASS",
            "detail": "Semua akun admin sudah mengaktifkan MFA.",
            "rekomendasi": "-"
        })

    return temuan


def cek_gitignore() -> list:
    temuan = []
    gitignore_ada = os.path.exists(".gitignore")
    env_ter_exclude = False

    if gitignore_ada:
        with open(".gitignore", "r") as f:
            isi = f.read()
            if ".env" in isi:
                env_ter_exclude = True

    if not gitignore_ada or not env_ter_exclude:
        temuan.append({
            "finding": "File .env Tidak Ter-exclude dari Version Control",
            "severity": "HIGH",
            "status": "FAIL",
            "detail": "File .gitignore tidak ditemukan atau tidak mengandung entri '.env'.",
            "rekomendasi": "Tambahkan '.env' ke file .gitignore sebelum melakukan git commit."
        })
    else:
        temuan.append({
            "finding": "File .env Tidak Ter-exclude dari Version Control",
            "severity": "HIGH",
            "status": "PASS",
            "detail": "File .env sudah ter-exclude dengan benar di .gitignore.",
            "rekomendasi": "-"
        })

    return temuan


def cek_pola_bruteforce() -> list:
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    batas_waktu = datetime.now() - timedelta(hours=24)
    cursor.execute(
        "SELECT COUNT(*) FROM audit_log WHERE status='locked' AND created_at >= %s",
        (batas_waktu,)
    )
    jumlah = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    status = "INFO" if jumlah == 0 else "WARNING"
    return [{
        "finding": "Pola Brute-Force 24 Jam Terakhir",
        "severity": "INFO",
        "status": status,
        "detail": f"Tercatat {jumlah} kejadian lockout akun dalam 24 jam terakhir.",
        "rekomendasi": "Tidak ada tindakan diperlukan." if jumlah == 0 else "Investigasi username yang terkena lockout berulang."
    }]


def jalankan_security_audit():
    console.print(Panel("SENTRAAUTH SELF SECURITY AUDIT", style="bold magenta", expand=False))
    console.print("Menjalankan pengecekan konfigurasi keamanan internal...\n", style="dim italic")

    semua_temuan = []
    semua_temuan += cek_kredensial_default()
    semua_temuan += cek_mfa_admin()
    semua_temuan += cek_gitignore()
    semua_temuan += cek_pola_bruteforce()

    table = Table(title="Hasil Security Audit", show_lines=True)
    table.add_column("Finding", style="bold")
    table.add_column("Severity", justify="center")
    table.add_column("Status", justify="center")
    table.add_column("Detail")
    table.add_column("Rekomendasi")

    warna_severity = {"HIGH": "bold red", "MEDIUM": "bold yellow", "INFO": "bold cyan"}
    warna_status = {"PASS": "bold green", "FAIL": "bold red", "INFO": "cyan", "WARNING": "bold yellow"}

    jumlah_fail = 0
    for t in semua_temuan:
        if t['status'] in ('FAIL', 'WARNING'):
            jumlah_fail += 1
        sev_style = warna_severity.get(t['severity'], "white")
        stat_style = warna_status.get(t['status'], "white")
        table.add_row(
            t['finding'],
            f"[{sev_style}]{t['severity']}[/{sev_style}]",
            f"[{stat_style}]{t['status']}[/{stat_style}]",
            t['detail'],
            t['rekomendasi']
        )

    console.print(table)

    if jumlah_fail == 0:
        console.print("\n[bold green]Tidak ditemukan isu keamanan pada pengecekan ini.[/bold green]")
    else:
        console.print(f"\n[bold yellow]Ditemukan {jumlah_fail} isu yang perlu ditindaklanjuti.[/bold yellow]")


if __name__ == "__main__":
    jalankan_security_audit()