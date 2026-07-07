-- Run this ONCE as MySQL root:  mysql -u root -p < sql/00_setup/00_create_database.sql
-- Replace CHANGE_ME with the same password you put in .env
CREATE DATABASE IF NOT EXISTS shopsphere_dw
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE USER IF NOT EXISTS 'shopsphere_app'@'localhost' IDENTIFIED BY 'CHANGE_ME';
CREATE USER IF NOT EXISTS 'shopsphere_app'@'127.0.0.1' IDENTIFIED BY 'CHANGE_ME';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER,
      CREATE VIEW, SHOW VIEW
  ON shopsphere_dw.* TO 'shopsphere_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER,
      CREATE VIEW, SHOW VIEW
  ON shopsphere_dw.* TO 'shopsphere_app'@'127.0.0.1';

FLUSH PRIVILEGES;
