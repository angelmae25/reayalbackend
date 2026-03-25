-- =============================================================================
-- SCHOLIFE UNIFIED DATABASE (WEB + MOBILE)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS Schoolifetrue_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE Schoolifetrue_db;

-- =============================================================================
-- STUDENTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS students (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id VARCHAR(30) NOT NULL UNIQUE,
  first_name VARCHAR(80) NOT NULL,
  last_name VARCHAR(80) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  course VARCHAR(100) DEFAULT '',
  year_level VARCHAR(30) DEFAULT '1st Year',
  contact VARCHAR(20),
  avatar_url VARCHAR(300),
  points INT DEFAULT 0,
  status ENUM('PENDING','ACTIVE','INACTIVE') DEFAULT 'PENDING',
  fcm_token VARCHAR(500),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =============================================================================
-- ADMIN USERS
-- =============================================================================
CREATE TABLE IF NOT EXISTS admin_users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  full_name VARCHAR(160) NOT NULL,
  email VARCHAR(150) NOT NULL,
  role ENUM('SUPER_ADMIN','OSA','ADAA','ADAF','DO') DEFAULT 'OSA',
  status ENUM('ACTIVE','INACTIVE') DEFAULT 'ACTIVE',
  office VARCHAR(100),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_login DATETIME
);

-- =============================================================================
-- NEWS
-- =============================================================================
CREATE TABLE IF NOT EXISTS news (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  body TEXT NOT NULL,
  category ENUM('all','health','academic','campus','sports') DEFAULT 'all',
  published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_featured TINYINT(1) DEFAULT 0,
  image_url VARCHAR(300),
  author_name VARCHAR(100) DEFAULT 'Scholife Editorial',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- EVENTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS events (
  id INT AUTO_INCREMENT PRIMARY KEY,
  short_name VARCHAR(20) NOT NULL,
  full_name VARCHAR(255) NOT NULL,
  date DATE NOT NULL,
  venue VARCHAR(150),
  category VARCHAR(50) DEFAULT 'General',
  color VARCHAR(10) DEFAULT '#8B1A1A',
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CLUBS
-- =============================================================================
CREATE TABLE IF NOT EXISTS clubs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  acronym VARCHAR(20),
  department VARCHAR(100),
  description TEXT,
  icon_name VARCHAR(50) DEFAULT 'groups',
  color VARCHAR(10) DEFAULT '#8B1A1A',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS club_memberships (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  club_id INT NOT NULL,
  joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_member (student_id, club_id),
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  FOREIGN KEY (club_id) REFERENCES clubs(id) ON DELETE CASCADE
);

-- =============================================================================
-- ORGANIZATIONS (ADMIN SIDE)
-- =============================================================================
CREATE TABLE IF NOT EXISTS organizations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  acronym VARCHAR(20),
  type VARCHAR(80),
  description TEXT,
  status ENUM('ACTIVE','INACTIVE') DEFAULT 'ACTIVE',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS org_roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  organization_id INT NOT NULL,
  student_id INT NOT NULL,
  role_name VARCHAR(60) NOT NULL,
  assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  assigned_by INT,
  UNIQUE KEY uq_org_role (organization_id, role_name),
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================================================
-- MARKETPLACE
-- =============================================================================
CREATE TABLE IF NOT EXISTS marketplace_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  description TEXT,
  condition_ VARCHAR(60) DEFAULT 'Good condition',
  price DECIMAL(10,2) DEFAULT 0.00,
  image_url VARCHAR(300),
  seller_id INT NOT NULL,
  is_sold TINYINT(1) DEFAULT 0,
  posted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (seller_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================================================
-- LOST & FOUND
-- =============================================================================
CREATE TABLE IF NOT EXISTS lost_found (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(150) NOT NULL,
  description TEXT,
  location VARCHAR(150),
  date DATE NOT NULL,
  status ENUM('lost','found') DEFAULT 'lost',
  reporter_id INT NOT NULL,
  image_url VARCHAR(300),
  is_resolved TINYINT(1) DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (reporter_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================================================
-- CHAT SYSTEM
-- =============================================================================
CREATE TABLE IF NOT EXISTS conversations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150),
  is_group TINYINT(1) DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_members (
  conversation_id INT,
  student_id INT,
  PRIMARY KEY (conversation_id, student_id),
  FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
  id INT AUTO_INCREMENT PRIMARY KEY,
  conversation_id INT NOT NULL,
  sender_id INT NOT NULL,
  text TEXT NOT NULL,
  sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
  FOREIGN KEY (sender_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================================================
-- REPORTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS reports (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  subject VARCHAR(200) NOT NULL,
  message TEXT NOT NULL,
  status ENUM('OPEN','IN_PROGRESS','RESOLVED') DEFAULT 'OPEN',
  admin_reply TEXT,
  replied_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================================================
-- EVENT ATTENDANCE
-- =============================================================================
CREATE TABLE IF NOT EXISTS event_attendance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_id INT NOT NULL,
  student_id INT NOT NULL,
  attended_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_event_student (event_id, student_id),
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================================================
-- ACTIVITY LOGS
-- =============================================================================
CREATE TABLE IF NOT EXISTS activity_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  admin_id INT NOT NULL,
  admin_name VARCHAR(160) NOT NULL,
  admin_role VARCHAR(30),
  action VARCHAR(60) NOT NULL,
  details TEXT,
  target_type VARCHAR(50),
  target_id INT,
  ip_address VARCHAR(50),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- LEADERBOARD VIEW
-- =============================================================================
CREATE OR REPLACE VIEW leaderboard AS
SELECT
  s.id,
  CONCAT(s.first_name, ' ', s.last_name) AS full_name,
  s.year_level,
  s.course,
  s.points,
  s.avatar_url,
  RANK() OVER (ORDER BY s.points DESC) AS `rank`
FROM students s
WHERE s.status = 'ACTIVE';

-- =============================================================================
-- SEED DATA
-- =============================================================================

-- STUDENTS
INSERT IGNORE INTO students
(student_id, first_name, last_name, email, password_hash, course, year_level, points, status)
VALUES
('2021-00001','Juan','dela Cruz','student@scholife.edu',
'$2b$12$KIXy6TdXrG6GWVPcF4IYmOvkWqFHVfq7tVr6mFjfP0c5bJn6H7k7m',
'BS Computer Science','3rd Year',3750,'ACTIVE');

-- ADMIN
INSERT IGNORE INTO admin_users
(username,password,full_name,email,role,office)
VALUES
('superadmin',
'$2a$10$N.zmdr9zkzoGtM.w3EeGq.bkJj/vqPr9jXiWjVtHWKoVLBlbXE/Vu',
'Super Administrator',
'superadmin@scholife.edu',
'SUPER_ADMIN',
'Main Office');