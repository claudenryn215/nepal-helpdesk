CREATE TABLE IF NOT EXISTS views (
  post_id TEXT PRIMARY KEY,
  count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id TEXT NOT NULL,
  parent_id INTEGER DEFAULT NULL,
  name TEXT NOT NULL,
  body TEXT NOT NULL,
  approved INTEGER NOT NULL DEFAULT 0,
  seed_key TEXT UNIQUE,
  upvotes INTEGER NOT NULL DEFAULT 0,
  downvotes INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id, approved);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(post_id, parent_id);

CREATE TABLE IF NOT EXISTS comment_votes (
  comment_id INTEGER NOT NULL,
  voter TEXT NOT NULL,
  direction INTEGER NOT NULL,
  PRIMARY KEY (comment_id, voter)
);
