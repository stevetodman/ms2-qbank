-- Foreign key constraints for videos database

-- NOTE: user_id columns reference users.id in users.db (cross-database in SQLite)
-- These cannot be enforced as FKs in separate SQLite files
-- Application-level integrity must be maintained

-- Add check constraints for data validity
ALTER TABLE video_progress ADD CONSTRAINT chk_progress_user_id_positive
    CHECK (user_id > 0);

ALTER TABLE video_progress ADD CONSTRAINT chk_progress_seconds_non_negative
    CHECK (progress_seconds >= 0);

ALTER TABLE video_bookmarks ADD CONSTRAINT chk_bookmark_user_id_positive
    CHECK (user_id > 0);

ALTER TABLE video_bookmarks ADD CONSTRAINT chk_bookmark_timestamp_non_negative
    CHECK (timestamp_seconds >= 0);

-- Add composite unique constraint for video progress (one per user-video pair)
CREATE UNIQUE INDEX IF NOT EXISTS ux_video_progress_user_video
    ON video_progress(user_id, video_id);

-- Add composite unique constraint for playlist position (no duplicate positions)
CREATE UNIQUE INDEX IF NOT EXISTS ux_playlist_videos_playlist_position
    ON playlist_videos(playlist_id, position);

-- Note: Existing FKs in models (playlist_videos → playlists/videos, etc.) are already enforced
-- via SQLModel's foreign_key parameter, which creates FOREIGN KEY constraints
