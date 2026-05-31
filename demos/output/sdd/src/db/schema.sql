```sql
CREATE TABLE crewai_playbook (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  user_id INTEGER REFERENCES users (id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE crewai_playbook_cards (
  id SERIAL PRIMARY KEY,
  playbook_id INTEGER REFERENCES crewai_playbook (id),
  card_id INTEGER REFERENCES cards (id),
  sequence_number SMALLINT NOT NULL DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE crewai_playbook_items (
  id SERIAL PRIMARY KEY,
  playbook_id INTEGER REFERENCES crewai_playbook (id),
  item_id INTEGER REFERENCES items (id),
  sequence_number SMALLINT NOT NULL DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cards (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  quantity INTEGER DEFAULT 1,
  cost INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE items (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  quantity INTEGER DEFAULT 1,
  cost INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  password VARCHAR(255) NOT NULL,
  email VARCHAR(100) NOT NULL,
  first_name VARCHAR(50),
  last_name VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed data for core tables
INSERT INTO users (username, password, email, first_name, last_name) VALUES ('admin', 'password123', 'admin@example.com', 'Admin', 'User');
INSERT INTO cards (name, description, quantity, cost) VALUES ('Card 1', 'This is the first card', 10, 5);
INSERT INTO items (name, description, quantity, cost) VALUES ('Item 1', 'This is the first item', 5, 10);

-- Indexes for foreign key columns
CREATE INDEX idx_playbook_id_cards ON crewai_playbook_cards (playbook_id);
CREATE INDEX idx_card_id_cards ON crewai_playbook_cards (card_id);
CREATE INDEX idx_playbook_id_items ON crewai_playbook_items (playbook_id);
CREATE INDEX idx_item_id_items ON crewai_playbook_items (item_id);
```