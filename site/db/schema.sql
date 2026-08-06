CREATE TABLE IF NOT EXISTS views (
  post_id TEXT PRIMARY KEY,
  count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id TEXT NOT NULL,
  name TEXT NOT NULL,
  body TEXT NOT NULL,
  approved INTEGER NOT NULL DEFAULT 0,
  seed_key TEXT UNIQUE,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id, approved);
