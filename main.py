from findings import submit_finding, lihat_findings_saya, lihat_semua_findings, update_status_finding, assign_finding, hapus_finding
from security_check import jalankan_security_audit
import sys
from auth import login
from rbac import get_permissions, has_permission
from accounts import lihat_akun, tambah_akun, hapus_akun, renew_password, ganti_password_sendiri
from audit import lihat_log
from mfa import setup_mfa
from ui import console, banner, print_success, print_error, print_info, judul_bagian, tabel_menu



# Menyimpan sesi user yang sedang aktif.
current_session = {
    "username": None,
    "role": None,
    "permissions": []
}


def menu_kelola_akun():
    while True:
        judul_bagian("KELOLA AKUN SISTEM")
        console.print("0. Kembali ke Menu Utama")
        console.print("1. Lihat Semua Akun")
        console.print("2. Tambah Akun Baru")
        console.print("3. Hapus Akun")
        console.print("4. Renew Password Akun")
        console.print("5. Lihat Audit Log")
        console.print("6. Jalankan Security Audit")

        pilihan = input("Pilih menu: ").strip()

        if pilihan == '1':
            lihat_akun()
        elif pilihan == '2':
            tambah_akun(current_session['username'])
        elif pilihan == '3':
            hapus_akun(current_session['username'])
        elif pilihan == '4':
            renew_password(current_session['username'])
        elif pilihan == '5':
            lihat_log()
        elif pilihan == '6':
            jalankan_security_audit()
        elif pilihan == '0':
            break
        else:
            print_error("Pilihan tidak valid.")

def menu_findings_admin():
    while True:
        judul_bagian("KELOLA TEMUAN KEAMANAN")
        console.print("0. Kembali ke Menu Utama")
        console.print("1. Lihat Semua Temuan")
        console.print("2. Update Status Temuan")
        console.print("3. Assign Temuan")
        console.print("4. Hapus Temuan")

        pilihan = input("Pilih menu: ").strip()

        if pilihan == '1':
            lihat_semua_findings()
        elif pilihan == '2':
            update_status_finding(current_session['username'])
        elif pilihan == '3':
            assign_finding(current_session['username'])
        elif pilihan == '4':
            hapus_finding(current_session['username'])
        elif pilihan == '0':
            break
        else:
            print_error("Pilihan tidak valid.")


def menu_findings_user():
    while True:
        judul_bagian("TEMUAN SAYA")
        console.print("0. Kembali ke Menu Utama")
        console.print("1. Submit Temuan Baru")
        console.print("2. Lihat Temuan Saya")

        pilihan = input("Pilih menu: ").strip()

        if pilihan == '1':
            submit_finding(current_session['username'])
        elif pilihan == '2':
            lihat_findings_saya(current_session['username'])
        elif pilihan == '0':
            break
        else:
            print_error("Pilihan tidak valid.")


def menu_utama():
    while True:
        judul_bagian(f"MENU UTAMA ({current_session['role'].upper()})")
        console.print(f"Login sebagai: [bold]{current_session['username']}[/bold]")

        menu_tersedia = []

        if has_permission(current_session['permissions'], 'manage_accounts'):
            menu_tersedia.append(('kelola_akun', 'Kelola Akun Sistem'))
        if has_permission(current_session['permissions'], 'change_own_password'):
            menu_tersedia.append(('ganti_password', 'Ganti Password Saya'))
        menu_tersedia.append(('setup_mfa', 'Aktifkan MFA (2FA)'))
        if has_permission(current_session['permissions'], 'manage_findings'):
            menu_tersedia.append(('kelola_findings', 'Kelola Temuan Keamanan'))
        if has_permission(current_session['permissions'], 'submit_finding'):
            menu_tersedia.append(('findings_user', 'Temuan Saya'))

        tabel_menu(menu_tersedia)

        pilihan = input("Pilih menu: ").strip()

        if pilihan == '0':
            print_info("Logout berhasil...")
            current_session['username'] = None
            current_session['role'] = None
            current_session['permissions'] = []
            break

        if pilihan.isdigit() and 1 <= int(pilihan) <= len(menu_tersedia):
            kode_aksi = menu_tersedia[int(pilihan) - 1][0]

            if kode_aksi == 'kelola_akun':
                menu_kelola_akun()
            elif kode_aksi == 'ganti_password':
                berhasil = ganti_password_sendiri(current_session['username'])
                if berhasil:
                    current_session['username'] = None
                    current_session['role'] = None
                    current_session['permissions'] = []
                    print_info("Silakan login ulang dengan password baru.")
                    break
            elif kode_aksi == 'setup_mfa':
                setup_mfa(current_session['username'])
            elif kode_aksi == 'kelola_findings':
                menu_findings_admin()
            elif kode_aksi == 'findings_user':
                menu_findings_user()
        else:
            print_error("Pilihan tidak valid, atau Anda tidak memiliki akses ke menu ini.")


def proses_login():
    judul_bagian("FORM LOGIN")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    hasil = login(username, password)

    if hasil:
        current_session['username'] = hasil['username']
        current_session['role'] = hasil['role']
        current_session['permissions'] = get_permissions(hasil['role'])

        print_success(f"Selamat datang, {current_session['username']} "
                      f"(Role: {current_session['role'].upper()})")
        menu_utama()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--security-audit":
        jalankan_security_audit()
        sys.exit(0)

    banner()
    while True:
        judul_bagian("SENTRAAUTH CLI")
        console.print("1. Login")
        console.print("2. Keluar Aplikasi")
        opsi = input("Pilih: ").strip()

        if opsi == '1':
            proses_login()
        elif opsi == '2':
            console.print("Sampai jumpa.", style="dim italic")
            break
        else:
            print_error("Pilihan tidak valid.")


