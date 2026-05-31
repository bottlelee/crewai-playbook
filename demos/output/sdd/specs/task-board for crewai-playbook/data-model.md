The comprehensive database schema design is provided below.

***

### Database Schema Design: Task Board Playbook Module

**To:** [Coworker/Recipient]
**From:** Tang Monk (Team Manager)
**Subject:** Comprehensive Database Schema for the Task Board Playbook Module

Dear Coworker,

Based on the implementation plan detailed in `plan.md`, I have led the team in designing a robust and highly scalable database schema. To ensure maximum data integrity and performance, our structure models users, projects, tasks, and the complex relationships between them (roles, dependencies, and assignments).

The schema is broken down into three parts: the Entity Relationship (ER) Description, the detailed Table Definitions, and the final SQL DDL.

---

### 1. Entity Relationship (ER) Description

The core of this system revolves around **Users** initiating **Projects**. Each Project contains multiple **Tasks**, and these tasks are assigned to specific team **Roles**. The relationships are complex, requiring several junction tables to maintain a many-to-many structure.

*   **User $\leftrightarrow$ Project:** Many-to-Many (A user can be involved in multiple projects, and a project has multiple users).
*   **Project $\leftrightarrow$ Task:** One-to-Many (A project contains many tasks).
*   **User $\leftrightarrow$ Task:** Many-to-Many (Multiple users can be assigned to a task, and a user can work on multiple tasks).
*   **Task $\leftrightarrow$ Role:** Many-to-Many (A task may require multiple roles, and a role applies to multiple tasks).
*   **Task $\leftrightarrow$ Task:** Many-to-Many (Tasks can have dependencies on other tasks, forming a network graph).
*   **Project $\leftrightarrow$ Status:** One-to-Many (A project has a current status).
*   **Task $\leftrightarrow$ Status:** One-to-Many (A task has a current status).

---

### 2. Table Definitions (Columns, Keys, Constraints)

#### `users` (The Team Members)
*   **Purpose:** Stores information about every user interacting with the system.
*   **Primary Key:** `user_id`
*   **Constraints:** `email` must be unique.

#### `projects` (The Missions)
*   **Purpose:** Defines the overarching project scope.
*   **Primary Key:** `project_id`
*   **Foreign Keys:** `owner_id` references `users(user_id)`.

#### `tasks` (The Milestones)
*   **Purpose:** Defines individual, actionable steps within a project.
*   **Primary Key:** `task_id`
*   **Foreign Keys:** `project_id` references `projects(project_id)`.

#### `project_members` (Project Membership Junction Table)
*   **Purpose:** Tracks which users are associated with which projects.
*   **Primary Key:** Composite (`project_id`, `user_id`)
*   **Foreign Keys:** `project_id` references `projects(project_id)`, `user_id` references `users(user_id)`.

#### `task_assignments` (Task Assignment Details)
*   **Purpose:** Links users to specific tasks, tracking who is responsible for what.
*   **Primary Key:** Composite (`task_id`, `assigned_user_id`)
*   **Foreign Keys:** `task_id` references `tasks(task_id)`, `assigned_user_id` references `users(user_id)`.

#### `roles` (The Expertise)
*   **Purpose:** Defines standard roles (e.g., Developer, QA, Designer).
*   **Primary Key:** `role_id`

#### `task_roles` (Task Role Junction Table)
*   **Purpose:** Links specific roles to specific tasks.
*   **Primary Key:** Composite (`task_id`, `role_id`)
*   **Foreign Keys:** `task_id` references `tasks(task_id)`, `role_id` references `roles(role_id)`.

#### `task_dependencies` (The Flow/Prerequisites)
*   **Purpose:** Defines the order of execution between tasks.
*   **Primary Key:** Composite (`task_id`, `prerequisite_task_id`)
*   **Foreign Keys:** `task_id` references `tasks(task_id)`, `prerequisite_task_id` references `tasks(task_id)`.

#### `statuses` (The State Tracking)
*   **Purpose:** Defines standard statuses (e.g., To Do, In Progress, Complete).
*   **Primary Key:** `status_id`

*Note: We use separate status tracking for Projects and Tasks for greater flexibility.*

---

### 3. Complete Schema in SQL DDL

```sql
-- ========================================================
-- SCHEMA DEFINITION: Task Board Playbook Module
-- Database: crewai_playbook
-- Goal: To manage projects, tasks, roles, and dependencies.
-- ========================================================

-- 1. Core Entities
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    join_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    status_id INTEGER NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE RESTRICT,
    FOREIGN KEY (status_id) REFERENCES statuses(status_id) ON DELETE RESTRICT
);

CREATE TABLE tasks (
    task_id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 3, -- 1 (High) to 5 (Low)
    due_date TIMESTAMP WITH TIME ZONE,
    status_id INTEGER NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (status_id) REFERENCES statuses(status_id) ON DELETE RESTRICT
);

-- 2. Lookup/Reference Tables
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE statuses (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) UNIQUE NOT NULL, -- e.g., 'To Do', 'In Progress', 'Completed', 'On Hold'
    is_final BOOLEAN DEFAULT FALSE
);

-- 3. Junction/Association Tables (Many-to-Many Relationships)

-- Project Members (Links users to projects)
CREATE TABLE project_members (
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role_in_project VARCHAR(100), -- Specific role within this project
    PRIMARY KEY (project_id, user_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Task Assignments (Links users to specific tasks)
CREATE TABLE task_assignments (
    task_id INTEGER NOT NULL,
    assigned_user_id INTEGER NOT NULL,
    assigned_by_id INTEGER NOT NULL, -- Tracks who assigned the task
    assigned_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, assigned_user_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by_id) REFERENCES users(user_id) ON DELETE RESTRICT
);

-- Task Roles (Links roles to tasks)
CREATE TABLE task_roles (
    task_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (task_id, role_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE
);

-- Task Dependencies (Links tasks to their prerequisites)
CREATE TABLE task_dependencies (
    task_id INTEGER NOT NULL, -- The dependent task
    prerequisite_task_id INTEGER NOT NULL, -- The task that must be completed first
    dependency_type VARCHAR(50) DEFAULT 'SEQUENTIAL', -- e.g., SEQUENTIAL, OPTIONAL
    PRIMARY KEY (task_id, prerequisite_task_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (prerequisite_task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

-- 4. Indexes for Performance Optimization
-- Indexing foreign keys and frequently queried columns significantly improves read performance.
CREATE INDEX idx_project_owner ON projects (owner_id);
CREATE INDEX idx_task_project ON tasks (project_id);
CREATE INDEX idx_task_due_date ON tasks (due_date);
CREATE INDEX idx_task_status ON tasks (status_id);
CREATE INDEX idx_project_member_user ON project_members (user_id);
CREATE INDEX idx_task_assignment_user ON task_assignments (assigned_user_id);
CREATE INDEX idx_task_dependency_prereq ON task_dependencies (prerequisite_task_id);
```