CREATE DATABASE IF NOT EXISTS dermosphere_db;
USE dermosphere_db;

CREATE TABLE IF NOT EXISTS roles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    metrics_access_status VARCHAR(20) DEFAULT 'REVOKED'
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- Multimodal Triage Ledger
CREATE TABLE IF NOT EXISTS scan_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    image_format VARCHAR(10),
    image_resolution VARCHAR(20),
    layer_analysis_depth INT DEFAULT 0,
    inference_latency_ms INT,
    patient_age INT,
    patient_sex VARCHAR(10),
    anatomy_site VARCHAR(50),
    fusion_confidence DECIMAL(5,2),
    xai_algorithm_used VARCHAR(30) DEFAULT 'Grad-CAM++',
    prediction_result VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- The Immutable Security Audit Ledger
CREATE TABLE IF NOT EXISTS system_audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    actor_username VARCHAR(100) NOT NULL,
    action_category VARCHAR(50) NOT NULL,
    action_details TEXT NOT NULL,
    threat_level VARCHAR(20) DEFAULT 'LOW',
    ip_address VARCHAR(45) DEFAULT '127.0.0.1',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);