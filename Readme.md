# SentraAuth-CLI

A hardened Command Line Interface (CLI) authentication and access control system with a role-based security finding tracker case study.

---

## Overview

SentraAuth-CLI addresses standard security flaws commonly found in introductory database scripts—such as plaintext password storage, lack of brute-force prevention, and hardcoded role checks—by implementing a defense-in-depth architecture directly within the terminal.

### Core Defenses
* **Password Hashing:** Passwords hashed with `bcrypt` using per-user random salt generation.
* **Account Lockout:** Locks account for 5 minutes after 5 consecutive failed attempts; status and timestamps are stored directly in MySQL.
* **Data-Driven RBAC:** Dynamic permission verification querying `roles` and `role_permissions` instead of hardcoded `if-else` blocks.
* **Multi-Factor Authentication (MFA):** RFC 6238 TOTP standard via `pyotp` with in-terminal ASCII QR code rendering via `qrcode`.
* **Fail-Silent Audit Logging:** Centralized tracking in `audit_log` for authentication, authorization, and administrative events.
* **Self-Security Check:** Built-in VAPT-style scanner checking for default credentials, active admin MFA, and `.env` exposure.
* **Security Finding Tracker:** Applied operational case study demonstrating data-driven RBAC separation between `admin` and `analyst` workflows.

---

## Database Architecture

The system uses a relational database schema (`sentra_auth`) containing five tables:

```text
  +-------+          +------------------+
  | roles |<---1:N---| role_permissions |
  +---+---+          +------------------+
      |
     1:N
      |
  +---+---+          +------------------+
  | users |----1:N---|     findings     |
  +---+---+          +------------------+
      :
     1:N (via username)
      :
  +---+---+
  | audit |
  +-------+
```
*(Audit logs track activity by username rather than a cascading foreign key to preserve historical audit trails if an account is deleted).*

---

## Installation & Setup

### 1. Prerequisites
* Python 3.10+
* MySQL Server (via Laragon, XAMPP, or standalone MySQL service)

### 2. Install Dependencies
```bash
pip install mysql-connector-python bcrypt pyotp qrcode python-dotenv rich
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=sentra_auth
```
*(Leave `DB_PASSWORD` blank if using default Laragon / XAMPP configurations).*

### 4. Database Setup
Save the schema below as `database_setup.sql`:

```sql
CREATE DATABASE IF NOT EXISTS sentra_auth;
USE sentra_auth;

-- Roles Table
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(20) UNIQUE NOT NULL
);

INSERT INTO roles (role_name) VALUES ('admin'), ('analyst');

-- Role Permissions Table
CREATE TABLE role_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL,
    permission_name VARCHAR(50) NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- Default Role Permissions Mapping
INSERT INTO role_permissions (role_id, permission_name) VALUES
(1, 'manage_accounts'),
(1, 'view_accounts'),
(1, 'change_own_password'),
(1, 'manage_findings'),
(2, 'view_accounts'),
(2, 'change_own_password'),
(2, 'submit_finding');

-- Users Table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    failed_attempts INT DEFAULT 0,
    locked_until DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    mfa_secret VARCHAR(32) DEFAULT NULL,
    mfa_enabled TINYINT(1) DEFAULT 0,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- Centralized Audit Trail Table
CREATE TABLE audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    event_type VARCHAR(30),
    status VARCHAR(20),
    ip_or_host VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Security Finding Tracker Case Study Table
CREATE TABLE findings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    severity ENUM('Critical', 'High', 'Medium', 'Low') NOT NULL,
    status ENUM('Open', 'In Progress', 'Resolved') DEFAULT 'Open',
    reported_by VARCHAR(50) NOT NULL,
    assigned_to VARCHAR(50) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

Import the schema into your MySQL service:
```bash
mysql -u root < database_setup.sql
```
*(If a password is set on your database user, append `-p`).*

### 5. Account Seeding
Populate initial accounts with bcrypt hashes directly via Python:
```bash
python seed_users.py
```

Default seeded accounts:
* `admin` / `adminjuga` (Role: Admin)
* `budi` / `budi123` (Role: Analyst)

---

## Running the Application

### Interactive CLI Menu
```bash
python main.py
```

### Self-Security Audit Scanner
Run the internal configuration and baseline scanner directly from the CLI:
```bash
python main.py --security-audit
```

---

## Access Control Matrix

| Feature / Capability | Admin Role | Analyst Role |
| :--- | :---: | :---: |
| Password Authentication & MFA Verification | Yes | Yes |
| Change Own Password | Yes | Yes |
| Enable / Manage Own MFA | Yes | Yes |
| View System Accounts | Yes | No |
| Add / Delete / Renew User Accounts | Yes | No |
| View System-Wide Audit Log | Yes | No |
| Run Self Security-Check Audit | Yes | No |
| Submit New Security Finding | No | Yes |
| View Personal Findings Only | No | Yes |
| View All System Findings | Yes | No |
| Update Status / Assign / Delete Findings | Yes | No |

---

## Known Limitations

* **Plaintext MFA Secrets:** TOTP secret keys are stored unencrypted in the database.
* **Session Expiry:** Sessions persist in terminal runtime memory without idle timeout revocation.
* **Independent TOTP Rate Limiting:** Account lockout applies to initial password verification, not consecutive invalid OTP code submissions.