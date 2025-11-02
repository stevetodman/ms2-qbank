-- Videos database indices for performance optimization

-- Unique index to ensure one progress record per user-video pair
-- Also speeds up lookups: "get progress for user X on video Y"
CREATE UNIQUE INDEX IF NOT EXISTS ux_progress_user_video
    ON video_progress(user_id, video_id);

-- Index for finding all bookmarks for a user, ordered by creation time
-- Supports queries like: "show recent bookmarks for user X"
CREATE INDEX IF NOT EXISTS idx_bookmark_user_time
    ON video_bookmarks(user_id, created_at DESC);

-- Index for finding all bookmarks within a specific video
-- Supports queries like: "get all bookmarks for video Y"
CREATE INDEX IF NOT EXISTS idx_bookmark_video_time
    ON video_bookmarks(video_id, timestamp_seconds);

-- Index for finding completed videos for a user
-- Supports queries like: "show all completed videos for user X"
CREATE INDEX IF NOT EXISTS idx_progress_completed
    ON video_progress(user_id, completed);

-- Index for playlist videos ordering
-- Ensures fast retrieval of videos in playlist order
CREATE INDEX IF NOT EXISTS idx_playlist_videos_order
    ON playlist_videos(playlist_id, position);

-- Index for finding all playlists for a user
-- Supports queries like: "show my playlists"
CREATE INDEX IF NOT EXISTS idx_playlist_user
    ON playlists(user_id, created_at DESC);
