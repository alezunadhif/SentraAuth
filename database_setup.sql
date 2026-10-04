CREATE DATABASE IF NOT EXISTS sentra_auth;
USE sentra_auth;

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(20) UNIQUE NOT NULL
);

INSERT INTO roles (role_name) VALUES ('admin'), ('analyst');

CREATE TABLE role_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL,
    permission_name VARCHAR(50) NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

INSERT INTO role_permissions (role_id, permission_name) VALUES
(1, 'manage_accounts'),
(1, 'view_accounts'),
(1, 'change_own_password'),
(1, 'manage_findings'),
(2, 'view_accounts'),
(2, 'change_own_password'),
(2, 'submit_finding');

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

CREATE TABLE audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    event_type VARCHAR(30),
    status VARCHAR(20),
    ip_or_host VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

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