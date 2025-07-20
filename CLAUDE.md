  This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

  Project Overview

  ClassComp Score is a comprehensive student computer usage scoring system designed for school information
  officers. It's a Flask-based web application with role-based access control (student/teacher/admin) supporting
  complete user management, data statistics, and secure authentication.

  Core Architecture

  Technology Stack

  - Backend: Flask, Flask-Login, SQLAlchemy (via raw SQL), PostgreSQL/SQLite
  - Frontend: Bootstrap 5, jQuery, DataTables, Chart.js
  - Export: Pandas, XlsxWriter for Excel reports
  - Security: bcrypt for password hashing, role-based permissions

  Key Features

  - Role-based system: students submit scores, teachers/admins manage data
  - Cyclic scoring: students score specific grades based on their own class
  - Data persistence: soft delete with history tracking via scores_history table
  - Excel exports: monthly reports with period-based aggregation
  - Real-time stats: dashboard with trends and analytics

  Database Schema

  Core Tables

  - users: id, username, password_hash, role, class_name, created_at
  - scores: id, user_id, evaluator_name/class, target_grade/class, score1-3, total, note, created_at
  - scores_history: audit trail for overwritten scores with complete metadata

  Scoring Logic

  - Score ranges: score1/2 (0-3), score3 (0-4), total (0-10 automatic)
  - Cyclic periods: 2-week scoring cycles preventing duplicate submissions
  - Grade mapping: 中预→初一, 初一→初二, 初二→中预, 高一↔高二, VCE↔VCE

  Development Commands

  Setup & Installation

  # Install dependencies
  pip install -r requirements.txt

  # Initialize database (creates tables + admin user)
  python init_db.py

  # Start development server
  python app.py

  # Windows quick start
  start.bat

  Database Management

  # Check database structure
  python tests/check_tables.py

  # View all users
  python tests/show_users.py

  # Debug data issues
  python tests/debug_detailed.py

  # Export test data
  python tests/test_excel_export.py

  Environment Configuration

  # Required .env variables
  DATABASE_URL=postgresql://user:pass@localhost:5432/classcomp_score
  SECRET_KEY=your-secret-key
  ADMIN_USERNAME=admin
  ADMIN_EMAIL=admin@school.com
  ADMIN_PASSWORD=admin123

  Key Code Locations

  Main Application Files

  - Entry point: app.py:846 - main Flask app with route handlers
  - Database layer: db.py:24-51 - connection pooling for PostgreSQL/SQLite
  - Models: models.py:6-262 - User and Score classes with business logic
  - Forms: forms.py:6-124 - WTForms validation for registration/login/scoring

  Critical Business Logic

  - Score creation: models.py:82-231 - cyclic period validation and history archiving
  - Grade mapping: app.py:43-64 - determines which grades students can score
  - Excel export: app.py:329-669 - complex period-based aggregation and formatting
  - Access control: @login_required + current_user.is_admin() decorators

  Route Structure

  - / - main scoring interface
  - /login, /logout - authentication
  - /admin - dashboard with stats and trends
  - /admin/users - user management (admin only)
  - /my_scores - personal score history
  - /submit_scores - API endpoint for score submission
  - /export_excel - monthly report generation

  Testing & Debugging

  Available Test Scripts

  - Data validation: tests/check_database_data.py, tests/verify_export_logic.py
  - Export testing: tests/test_excel_export.py, tests/test_final_export.py
  - Database tools: tests/check_tables.py, tests/migrate_database.py
  - Debug utilities: tests/debug_detailed.py, tests/show_users.py

  Common Debugging Tasks

  - Check data integrity: Run python tests/check_duplicates.py
  - Test exports: python tests/test_final_export.py generates sample Excel
  - Verify history: python tests/check_history_structure.py

  Production Considerations

  Deployment

  - Database: PostgreSQL recommended for production (SQLite for dev)
  - Server: Gunicorn for production (gunicorn app:app -b 0.0.0.0:5000)
  - Environment: Set DATABASE_URL and SECRET_KEY in production

  Security Notes

  - Passwords hashed with bcrypt
  - Role-based access control implemented
  - SQL injection prevention via parameterized queries
  - Input validation on both client and server sides

  Data Export Format

  Monthly Excel exports contain:
  - Period-based summaries (2-week cycles)
  - Grade-level score matrices
  - Complete audit trail including historical scores
  - Test data exclusion capability