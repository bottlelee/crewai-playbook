```markdown
# 📜 Key Architectural Decisions Log (SDD)

**Document Author:** Documentation & Memory - 白龍馬
**Date Created:** [Current Date]
**Purpose:** This document serves as the authoritative, single source of truth for all major architectural and functional decisions made during the Software Design Document (SDD) process. It ensures that all team members understand not only *what* was chosen, but also *why* and *what* was considered instead.

---

## 💾 General Process Guidelines

*   **Mandatory Review:** All new decisions must be logged here immediately upon finalization.
*   **Structure:** Each decision follows the pattern: **[Decision Name]** -> **What**, **Alternatives**, **Rationale**, **Date**.

---

## 🚀 Core System Architecture Decisions

### 1. Technology Stack Selection (Backend/Frontend)

*   **What was chosen:**
    *   **Backend:** Python (FastAPI)
    *   **Frontend:** React.js (with TypeScript)
    *   **Database:** PostgreSQL
*   **Alternatives considered:**
    *   *Backend:* Node.js (Express) or Django.
    *   *Frontend:* Vue.js or plain JavaScript.
    *   *Database:* MongoDB (NoSQL).
*   **Rationale:** Python/FastAPI was selected for its high performance, modern asynchronous capabilities, and strong community support for data processing, aligning with our primary business logic needs. React/TypeScript provides robust typing and a mature ecosystem for complex, stateful UIs. PostgreSQL was chosen for its ACID compliance, structured data handling, and advanced querying capabilities, which are crucial for maintaining data integrity.
*   **Date:** [Date of Decision]

### 2. Authentication and Authorization Strategy

*   **What was chosen:**
    *   Implementation of JWT (JSON Web Tokens) for stateless authentication.
    *   Role-Based Access Control (RBAC) stored and enforced at the service layer.
*   **Alternatives considered:**
    *   Session-based authentication (Server-side sessions).
    *   OAuth 2.0 with complex third-party identity providers (e.g., Google/Okta as the sole provider).
*   **Rationale:** JWT provides a stateless approach, simplifying scaling and making API calls more resilient. RBAC is the industry standard for granular control and aligns perfectly with the project's need to segment user privileges (Admin, Editor, Viewer).
*   **Date:** [Date of Decision]

## ✨ Feature Implementation Decisions

### 3. Asynchronous Task Handling

*   **What was chosen:**
    *   Utilizing a dedicated message queue (e.g., Redis/Celery) for all long-running, non-critical tasks (e.g., image processing, report generation, notification sending).
    *   The main API thread will only enqueue the task and return an immediate status ID.
*   **Alternatives considered:**
    *   Running long tasks synchronously within the main API endpoint (blocking the user).
    *   Using background workers directly managed by the database.
*   **Rationale:** Synchronous execution would lead to poor user experience and API timeouts. By decoupling long tasks into a message queue, the system remains highly responsive, scalable, and can process background jobs reliably without blocking the main request thread.
*   **Date:** [Date of Decision]

### 4. State Management in the Frontend

*   **What was chosen:**
    *   Implementing a centralized state management library (e.g., Redux Toolkit or Zustand) to hold global application state.
    *   Local component state will only manage ephemeral UI changes (e.g., dropdown open/closed).
*   **Alternatives considered:**
    *   Passing props down through deep component trees (Prop Drilling).
    *   Using React Context API for all state.
*   **Rationale:** While Context API is simple, it can lead to performance bottlenecks and complexity when managing highly interconnected, global state. A dedicated state management library provides predictable state transitions, optimized performance, and clear separation of concerns, making the application more maintainable.
*   **Date:** [Date of Decision]

## ⚙️ Data Modeling Decisions

### 5. Handling Relationships and Data Integrity

*   **What was chosen:**
    *   Implementing Foreign Key Constraints at the database level (PostgreSQL) for all critical relationships.
    *   Using a combination of ORM migrations and application-level validation (e.g., Pydantic) for business logic checks.
*   **Alternatives considered:**
    *   Relying solely on application code logic for integrity checks.
    *   Using junction tables for all many-to-many relationships without explicit constraints.
*   **Rationale:** Relying only on application code is vulnerable to API bypasses or direct database manipulation. By enforcing constraints at the database level, we guarantee data integrity regardless of the entry point, making the system robust and reliable.
*   **Date:** [Date of Decision]
```