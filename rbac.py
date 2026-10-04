from db import get_connection


def get_permissions(role_name: str) -> list:
    """
    Ambil semua permission yang dimiliki sebuah role dari database.
    Return list of string, misal ['view_accounts', 'manage_accounts'].
    """
    conn = get_connection()
    if not conn:
        print("[ERROR] Tidak bisa terhubung ke database saat cek permission.")
        return []

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT role_permissions.permission_name
        FROM role_permissions
        JOIN roles ON role_permissions.role_id = roles.id
        WHERE roles.role_name = %s
    """, (role_name,))

    hasil = cursor.fetchall()
    cursor.close()
    conn.close()

    return [row['permission_name'] for row in hasil]


def has_permission(user_permissions: list, required_permission: str) -> bool:
    """
    Helper kecil biar pengecekan di main.py lebih jelas dibaca.
    """
    return required_permission in user_permissions