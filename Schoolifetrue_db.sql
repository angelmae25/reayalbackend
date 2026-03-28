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
-- ORGANIZATIONS
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

-- =============================================================================
-- ROLES
-- =============================================================================
CREATE TABLE IF NOT EXISTS roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  role_name VARCHAR(60) NOT NULL UNIQUE
);

-- =============================================================================
-- ROLE ASSIGNMENTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS role_assignments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  organization_id INT NOT NULL,
  student_id INT NOT NULL,
  role_name VARCHAR(60) NOT NULL,
  assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  assigned_by INT,

  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================================================
-- NEWS
-- =============================================================================
CREATE TABLE IF NOT EXISTS news (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  body TEXT NOT NULL,

  category ENUM('all','health','academic','campus','sports') DEFAULT 'all',

  organization_id INT,

  published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_featured TINYINT(1) DEFAULT 0,

  image_url VARCHAR(300),
  author_name VARCHAR(100),

  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL
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

  organization_id INT,

  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL
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
-- CHAT
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
-- LEADERBOARD VIEW
-- =============================================================================
CREATE OR REPLACE VIEW leaderboard AS
SELECT
  s.id,
  CONCAT(s.first_name,' ',s.last_name) AS full_name,
  s.course,
  s.year_level,
  s.points,
  s.avatar_url,
  RANK() OVER (ORDER BY s.points DESC) AS rank
FROM students s
WHERE s.status = 'ACTIVE';