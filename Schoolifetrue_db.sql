-- =============================================================================
-- Schoolifetrue_db.sql  —  Scholife MySQL Database
-- Run this in MySQL Workbench or PyCharm Database tool:
--   mysql -u root -p < Schoolifetrue_db.sql
-- =============================================================================

CREATE DATABASE IF NOT EXISTS Schoolifetrue_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE Schoolifetrue_db;

-- ─────────────────────────────────────────────────────────────────────────────
-- STUDENTS  (main user table)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS students (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  student_id    VARCHAR(30)  NOT NULL UNIQUE,
  first_name    VARCHAR(80)  NOT NULL,
  last_name     VARCHAR(80)  NOT NULL,
  email         VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  course        VARCHAR(100) DEFAULT '',
  year_level    VARCHAR(30)  DEFAULT '1st Year',
  contact       VARCHAR(20)  DEFAULT NULL,
  avatar_url    VARCHAR(300) DEFAULT NULL,
  points        INT          DEFAULT 0,
  status        ENUM('PENDING','ACTIVE','INACTIVE') DEFAULT 'PENDING',
  created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────────────────────────────────────
-- NEWS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS news (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  title        VARCHAR(255) NOT NULL,
  body         TEXT         NOT NULL,
  category     ENUM('all','health','academic','campus','sports') DEFAULT 'all',
  published_at DATETIME     DEFAULT CURRENT_TIMESTAMP,
  is_featured  TINYINT(1)   DEFAULT 0,
  image_url    VARCHAR(300) DEFAULT NULL,
  author_name  VARCHAR(100) DEFAULT 'Scholife Editorial',
  created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────────────────────────────────────
-- EVENTS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  short_name  VARCHAR(20)  NOT NULL,
  full_name   VARCHAR(255) NOT NULL,
  date        DATE         NOT NULL,
  venue       VARCHAR(150) DEFAULT '',
  category    VARCHAR(50)  DEFAULT 'General',
  color       VARCHAR(10)  DEFAULT '#8B1A1A',
  description TEXT         DEFAULT NULL,
  created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────────────────────────────────────
-- CLUBS / ORGANIZATIONS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS clubs (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(150) NOT NULL,
  acronym     VARCHAR(20)  DEFAULT '',
  department  VARCHAR(100) DEFAULT '',
  description TEXT         DEFAULT NULL,
  icon_name   VARCHAR(50)  DEFAULT 'groups',
  color       VARCHAR(10)  DEFAULT '#8B1A1A',
  created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- junction: student ↔ club membership
CREATE TABLE IF NOT EXISTS club_memberships (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  club_id    INT NOT NULL,
  joined_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_member (student_id, club_id),
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  FOREIGN KEY (club_id)    REFERENCES clubs(id)    ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────────────────────
-- MARKETPLACE ITEMS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS marketplace_items (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(150) NOT NULL,
  description TEXT         DEFAULT NULL,
  condition_  VARCHAR(60)  DEFAULT 'Good condition',
  price       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  image_url   VARCHAR(300) DEFAULT NULL,
  seller_id   INT          NOT NULL,
  is_sold     TINYINT(1)   DEFAULT 0,
  posted_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (seller_id) REFERENCES students(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────────────────────
-- LOST & FOUND
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lost_found (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  title       VARCHAR(150) NOT NULL,
  description TEXT         DEFAULT NULL,
  location    VARCHAR(150) DEFAULT '',
  date        DATE         NOT NULL,
  status      ENUM('lost','found') DEFAULT 'lost',
  reporter_id INT          NOT NULL,
  image_url   VARCHAR(300) DEFAULT NULL,
  is_resolved TINYINT(1)   DEFAULT 0,
  created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (reporter_id) REFERENCES students(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────────────────────
-- CHAT CONVERSATIONS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS conversations (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(150) DEFAULT NULL,  -- group name (NULL = direct)
  is_group    TINYINT(1)   DEFAULT 0,
  created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_members (
  conversation_id INT NOT NULL,
  student_id      INT NOT NULL,
  PRIMARY KEY (conversation_id, student_id),
  FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
  FOREIGN KEY (student_id)      REFERENCES students(id)      ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  conversation_id INT  NOT NULL,
  sender_id       INT  NOT NULL,
  text            TEXT NOT NULL,
  sent_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
  FOREIGN KEY (sender_id)       REFERENCES students(id)      ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────────────────────
-- LEADERBOARD VIEW  (auto-ranked by points)
-- ─────────────────────────────────────────────────────────────────────────────
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

-- ─────────────────────────────────────────────────────────────────────────────
-- SEED DATA — sample rows so the app has content on first run
-- ─────────────────────────────────────────────────────────────────────────────

-- Admin / test student (password: Admin@123)
INSERT IGNORE INTO students
  (student_id, first_name, last_name, email, password_hash, course, year_level, points, status)
VALUES
  ('2021-00001', 'Juan',  'dela Cruz', 'student@scholife.edu',
   '$2b$12$KIXy6TdXrG6GWVPcF4IYmOvkWqFHVfq7tVr6mFjfP0c5bJn6H7k7m',  -- Admin@123
   'BS Computer Science', '3rd Year', 3750, 'ACTIVE'),
  ('2021-00002', 'Maria', 'Santos',    'maria@scholife.edu',
   '$2b$12$KIXy6TdXrG6GWVPcF4IYmOvkWqFHVfq7tVr6mFjfP0c5bJn6H7k7m',
   'BS Nursing', '2nd Year', 4850, 'ACTIVE'),
  ('2021-00003', 'Jose',  'Reyes',     'jose@scholife.edu',
   '$2b$12$KIXy6TdXrG6GWVPcF4IYmOvkWqFHVfq7tVr6mFjfP0c5bJn6H7k7m',
   'BS Engineering', '4th Year', 4200, 'ACTIVE');

-- News
INSERT IGNORE INTO news (title, body, category, is_featured, author_name) VALUES
  ('COVID-19 UPDATE',
   'Important health protocols and vaccination requirements for the upcoming semester. All students must comply with updated health guidelines.',
   'health', 1, 'Health Office'),
  ('Enrollment Schedule Released',
   'Second semester enrollment is now open. Check the portal for your designated schedule.',
   'academic', 0, 'Registrar'),
  ('Library Extended Hours',
   'The library will extend operating hours until 10PM during finals week.',
   'campus', 0, 'Library Services'),
  ('Intramurals 2024 Registration',
   'Registration for the annual intramural sports competition is now open.',
   'sports', 0, 'Athletics Office'),
  ('Mental Health Week',
   'Join us for a week of wellness activities, counseling sessions, and community support.',
   'health', 0, 'Guidance Office');

-- Events
INSERT IGNORE INTO events (short_name, full_name, date, venue, category, color) VALUES
  ('BASD',   'Brigada ng Agham at Sining Dula',  '2025-03-15', 'Main Campus Gym',     'Cultural', '#8B0000'),
  ('MAAD',   'Music, Arts & Drama Day',           '2025-03-22', 'Open Air Auditorium', 'Cultural', '#6A1B9A'),
  ('TECH',   '5th Annual Technology Summit',      '2025-04-03', 'Engineering Hall',    'Academic', '#8B1A1A'),
  ('SPORTS', 'Intramural Sports Festival',         '2025-04-10', 'University Grounds',  'Sports',   '#1565C0');

-- Clubs
INSERT IGNORE INTO clubs (name, acronym, department, color) VALUES
  ('CS Society',   'CSS',  'Computer Science', '#8B1A1A'),
  ('Math Club',    'MC',   'Mathematics',      '#1565C0'),
  ('Art Circle',   'AC',   'Fine Arts',        '#6A1B9A'),
  ('Science Club', 'SCI',  'Natural Sciences', '#2E7D32'),
  ('Debate Team',  'DT',   'Liberal Arts',     '#E65100'),
  ('Photography',  'PHOTO','Media Arts',       '#37474F');

-- Lost & Found
INSERT IGNORE INTO lost_found (title, description, location, date, status, reporter_id) VALUES
  ('Black Wallet',          'Lost near the library on March 10.',     'Library Area',      '2025-03-10', 'lost',  1),
  ('Scientific Calculator', 'Casio FX-991. Lost in Engineering 204.', 'Engineering Bldg',  '2025-03-11', 'lost',  2),
  ('USB Flash Drive',       '16GB Kingston. Contains thesis files.',   'Computer Lab',      '2025-03-12', 'lost',  3),
  ('Red Umbrella',          'Found outside the cafeteria.',            'Cafeteria',         '2025-03-11', 'found', 2),
  ('Student ID (Maria S.)', 'Found on 2nd floor hallway.',             '2nd Floor Hallway', '2025-03-12', 'found', 3);

-- Marketplace
INSERT IGNORE INTO marketplace_items (name, condition_, price, seller_id) VALUES
  ('Calculus Textbook',     'Good condition', 150.00, 1),
  ('Scientific Calculator', 'Slightly used',  250.00, 2),
  ('Lab Coat (Size M)',      'Lightly worn',    80.00, 3),
  ('Nursing Complete Kit',  'Complete set',   500.00, 2),
  ('Pastel Art Supplies',   'Barely used',    200.00, 1),
  ('Foldable Laptop Stand', 'Like new',       120.00, 3);
