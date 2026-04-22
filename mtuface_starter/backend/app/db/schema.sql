CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  student_code VARCHAR(32) UNIQUE NOT NULL,
  full_name VARCHAR(128) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS embeddings (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  vector_json TEXT NOT NULL,
  model_version VARCHAR(64) NOT NULL DEFAULT 'insightface-buffalo_l',
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_embeddings_user_id ON embeddings(user_id);

CREATE TABLE IF NOT EXISTS attendance_logs (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  checked_at TIMESTAMP NOT NULL DEFAULT NOW(),
  confidence DOUBLE PRECISION NOT NULL,
  image_path VARCHAR(255)
);
CREATE INDEX IF NOT EXISTS ix_attendance_logs_user_checked_at ON attendance_logs(user_id, checked_at DESC);
