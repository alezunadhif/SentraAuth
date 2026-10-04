from db import get_connection
from audit import log_event
from ui import console, print_success, print_error, print_info, tabel_findings


def submit_finding(username: str):
    console.print("\n=== SUBMIT TEMUAN BARU ===", style="bold cyan")
    title = input("Judul temuan: ").strip()
    description = input("Deskripsi: ").strip()

    print("Severity: 1=Critical, 2=High, 3=Medium, 4=Low")
    pilihan_severity = input("Pilih severity: ").strip()
    mapping_severity = {'1': 'Critical', '2': 'High', '3': 'Medium', '4': 'Low'}

    if pilihan_severity not in mapping_severity:
        print_error("Pilihan severity tidak valid.")
        return

    if not title:
        print_error("Judul tidak boleh kosong.")
        return

    severity = mapping_severity[pilihan_severity]

    conn = get_connection()
    if not conn:
        print_error("Tidak bisa terhubung ke database.")
        return

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO findings (title, description, severity, reported_by) VALUES (%s, %s, %s, %s)",
        (title, description, severity, username)
    )
    conn.commit()
    finding_id = cursor.lastrowid
    cursor.close()
    conn.close()

    print_success(f"Temuan #{finding_id} berhasil disubmit dengan status Open.")
    log_event(username, "finding_submitted", "success")


def lihat_findings_saya(username: str):
    conn = get_connection()
    if not conn:
        print_error("Tidak bisa terhubung ke database.")
        return

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, title, severity, status, assigned_to, created_at FROM findings "
        "WHERE reported_by=%s ORDER BY created_at DESC",
        (username,)
    )
    hasil = cursor.fetchall()
    cursor.close()
    conn.close()

    tabel_findings(hasil, judul="Temuan Saya")


def lihat_semua_findings():
    conn = get_connection()
    if not conn:
        print_error("Tidak bisa terhubung ke database.")
        return

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, title, severity, status, reported_by, assigned_to, created_at "
        "FROM findings ORDER BY "
        "FIELD(severity, 'Critical', 'High', 'Medium', 'Low'), created_at DESC"
    )
    hasil = cursor.fetchall()
    cursor.close()
    conn.close()

    tabel_findings(hasil, judul="Semua Temuan Sistem", tampilkan_reporter=True)


def update_status_finding(actor_username: str):
    console.print("\n=== UPDATE STATUS TEMUAN ===", style="bold cyan")
    finding_id = input("Masukkan ID temuan: ").strip()

    if not finding_id.isdigit():
        print_error("ID harus berupa angka.")
        return

    conn = get_connection()
    if not conn:
        print_error("Tidak bisa terhubung ke database.")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM findings WHERE id=%s", (finding_id,))
    if not cursor.fetchone():
        print_error(f"Temuan #{finding_id} tidak ditemukan.")
        cursor.close()
        conn.close()
        return

    print("Status baru: 1=Open, 2=In Progress, 3=Resolved")
    pilihan = input("Pilih status: ").strip()
    mapping_status = {'1': 'Open', '2': 'In Progress', '3': 'Resolved'}

    if pilihan not in mapping_status:
        print_error("Pilihan status tidak valid.")
        cursor.close()
        conn.close()
        return

    status_baru = mapping_status[pilihan]
    cursor.execute("UPDATE findings SET status=%s WHERE id=%s", (status_baru, finding_id))
    conn.commit()
    cursor.close()
    conn.close()

    print_success(f"Status temuan #{finding_id} diubah menjadi '{status_baru}'.")
    log_event(actor_username, "finding_status_updated", "success")


def assign_finding(actor_username: str):
    console.print("\n=== ASSIGN TEMUAN ===", style="bold cyan")
    finding_id = input("Masukkan ID temuan: ").strip()
    target_user = input("Assign ke username: ").strip()

    if not finding_id.isdigit():
        print_error("ID harus berupa angka.")
        return

    conn = get_connection()
    if not conn:
        print_error("Tidak bisa terhubung ke database.")
        return

    cursor = conn.cursor()

    cursor.execute("SELECT id FROM findings WHERE id=%s", (finding_id,))
    if not cursor.fetchone():
        print_error(f"Temuan #{finding_id} tidak ditemukan.")
        cursor.close()
        conn.close()
        return

    cursor.execute("SELECT username FROM users WHERE username=%s", (target_user,))
    if not cursor.fetchone():
        print_error(f"User '{target_user}' tidak ditemukan.")
        cursor.close()
        conn.close()
        return

    cursor.execute("UPDATE findings SET assigned_to=%s WHERE id=%s", (target_user, finding_id))
    conn.commit()
    cursor.close()
    conn.close()

    print_success(f"Temuan #{finding_id} berhasil di-assign ke '{target_user}'.")
    log_event(actor_username, "finding_assigned", "success")


def hapus_finding(actor_username: str):
    console.print("\n=== HAPUS TEMUAN ===", style="bold cyan")
    finding_id = input("Masukkan ID temuan yang akan dihapus: ").strip()

    if not finding_id.isdigit():
        print_error("ID harus berupa angka.")
        return

    conn = get_connection()
    if not conn:
        print_error("Tidak bisa terhubung ke database.")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM findings WHERE id=%s", (finding_id,))
    if not cursor.fetchone():
        print_error(f"Temuan #{finding_id} tidak ditemukan.")
        cursor.close()
        conn.close()
        return

    konfirmasi = input(f"Yakin hapus temuan #{finding_id}? (y/n): ").strip().lower()
    if konfirmasi == 'y':
        cursor.execute("DELETE FROM findings WHERE id=%s", (finding_id,))
        conn.commit()
        print_success(f"Temuan #{finding_id} berhasil dihapus.")
        log_event(actor_username, "finding_deleted", "success")
    else:
        print_info("Penghapusan dibatalkan.")

    cursor.close()
    conn.close()