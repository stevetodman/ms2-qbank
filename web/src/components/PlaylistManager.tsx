import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import * as videoApi from '../api/videos';
import { VideoPlayer } from './VideoPlayer';
import '../styles/videos.css';

export function PlaylistManager() {
  const navigate = useNavigate();
  const { playlistId } = useParams<{ playlistId: string }>();
  const { token } = useAuth();

  const [playlist, setPlaylist] = useState<videoApi.Playlist | null>(null);
  const [videos, setVideos] = useState<videoApi.Video[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<videoApi.Video | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (playlistId) {
      loadPlaylistData(parseInt(playlistId));
    }
  }, [playlistId, token]);

  const loadPlaylistData = async (id: number) => {
    try {
      setLoading(true);
      setError(null);

      const [playlistData, videosData] = await Promise.all([
        videoApi.getPlaylist(id, token || undefined),
        videoApi.getPlaylistVideos(id, token || undefined),
      ]);

      setPlaylist(playlistData);
      setVideos(videosData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load playlist');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveVideo = async (videoId: number) => {
    if (!token || !playlistId) return;
    if (!confirm('Remove this video from the playlist?')) return;

    try {
      await videoApi.removeVideoFromPlaylist(parseInt(playlistId), videoId, token);
      setVideos(videos.filter((v) => v.id !== videoId));

      // Update playlist video count
      if (playlist) {
        setPlaylist({ ...playlist, video_count: playlist.video_count - 1 });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove video');
    }
  };

  const handleDeletePlaylist = async () => {
    if (!token || !playlistId) return;
    if (!confirm('Delete this entire playlist? This cannot be undone.')) return;

    try {
      await videoApi.deletePlaylist(parseInt(playlistId), token);
      navigate('/videos/playlists');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete playlist');
    }
  };

  if (selectedVideo) {
    return (
      <VideoPlayer
        video={selectedVideo}
        onClose={() => {
          setSelectedVideo(null);
          if (playlistId) loadPlaylistData(parseInt(playlistId));
        }}
      />
    );
  }

  if (loading) {
    return <div className="loading-state">Loading playlist...</div>;
  }

  if (error || !playlist) {
    return (
      <div className="error-state">
        <p>Error: {error || 'Playlist not found'}</p>
        <button className="btn-primary" onClick={() => navigate('/videos/playlists')}>
          Back to Playlists
        </button>
      </div>
    );
  }

  return (
    <div className="playlist-manager">
      <div className="playlist-header">
        <div>
          <h1>{playlist.name}</h1>
          {playlist.description && <p className="playlist-description">{playlist.description}</p>}
          <div className="playlist-meta">
            {playlist.is_official && <span className="badge badge-official">Official</span>}
            <span className="badge">{playlist.video_count} videos</span>
            <span className="text-muted">
              Created {new Date(playlist.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={() => navigate('/videos/playlists')}>
            Back to Playlists
          </button>
        </div>
      </div>

      {videos.length === 0 ? (
        <div className="empty-state">
          <h2>No videos in this playlist</h2>
          <p>Add videos from the video library to build your playlist.</p>
          <button className="btn-primary" onClick={() => navigate('/videos')}>
            Browse Videos
          </button>
        </div>
      ) : (
        <div className="playlist-videos">
          {videos.map((video, index) => (
            <div key={video.id} className="playlist-video-item">
              <div className="video-number">{index + 1}</div>

              <div
                className="video-thumbnail-small"
                onClick={() => setSelectedVideo(video)}
              >
                {video.thumbnail_url ? (
                  <img src={video.thumbnail_url} alt={video.title} />
                ) : (
                  <div className="thumbnail-placeholder">🎥</div>
                )}
                <div className="play-overlay">▶</div>
              </div>

              <div className="video-info" onClick={() => setSelectedVideo(video)}>
                <h3>{video.title}</h3>
                <p className="video-meta-text">
                  {video.subject} • {video.system} • {videoApi.formatDuration(video.duration_seconds)}
                </p>
                {video.instructor && <p className="video-instructor">👤 {video.instructor}</p>}
              </div>

              {!playlist.is_official && (
                <button
                  className="btn-text btn-danger"
                  onClick={() => handleRemoveVideo(video.id)}
                >
                  Remove
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {!playlist.is_official && (
        <div className="danger-zone">
          <h3>Danger Zone</h3>
          <p>Once you delete a playlist, there is no going back. Please be certain.</p>
          <button className="btn-danger" onClick={handleDeletePlaylist}>
            Delete This Playlist
          </button>
        </div>
      )}
    </div>
  );
}
