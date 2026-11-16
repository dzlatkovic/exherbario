CREATE DATABASE IF NOT EXISTS herbarium CHARACTER SET utf8mb4;

-- Save the generated password for the runtime DB_PASSWORD setting.
CREATE USER 'fastapi'@'localhost' IDENTIFIED BY RANDOM PASSWORD;
GRANT SELECT, INSERT, UPDATE, DELETE ON herbarium.* TO 'fastapi'@'localhost';
