import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import * as videoApi from '../api/videos';
import '../styles/videos.css';

export function PlaylistBrowser() {
  const navigate = useNavigate();
  const { token } = useAuth();

  const [playlists, setPlaylists] = useState<videoApi.Playlist[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newPlaylistName, setNewPlaylistName] = useState('');
  const [newPlaylistDescription, setNewPlaylistDescription] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadPlaylists();
  }, [token]);

  const loadPlaylists = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await videoApi.listPlaylists(false, token || undefined);
      setPlaylists(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load playlists');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlaylist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setError('You must be logged in to create playlists');
      return;
    }

    try {
      setCreating(true);
      setError(null);

      const playlist = await videoApi.createPlaylist(
        {
          name: newPlaylistName,
          description: newPlaylistDescription || undefined,
        },
        token
      );

      setPlaylists([playlist, ...playlists]);
      setNewPlaylistName('');
      setNewPlaylistDescription('');
      setShowCreateForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create playlist');
    } finally {
      setCreating(false);
    }
  };

  const officialPlaylists = playlists.filter((p) => p.is_official);
  const userPlaylists = playlists.filter((p) => !p.is_official);

  return (
    <div className="playlist-browser">
      <div className="playlist-browser-header">
        <h1>Playlists</h1>
        <div className="header-actions">
          <button className="btn-secondary" onClick={() => navigate('/videos')}>
            Browse Videos
          </button>
          <button className="btn-primary" onClick={() => setShowCreateForm(true)}>
            + Create Playlist
          </button>
        </div>
      </div>

      {showCreateForm && (
        <div className="playlist-form-modal">
          <div className="playlist-form-content">
            <h2>Create New Playlist</h2>
            <form onSubmit={handleCreatePlaylist}>
              <div className="form-group">
                <label htmlFor="name">Playlist Name *</label>
                <input
                  type="text"
                  id="name"
                  value={newPlaylistName}
                  onChange={(e) => setNewPlaylistName(e.target.value)}
                  required
                  placeholder="e.g., Cardiology Essentials"
                  autoFocus
                />
              </div>

              <div className="form-group">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  value={newPlaylistDescription}
                  onChange={(e) => setNewPlaylistDescription(e.target.value)}
                  rows={3}
                  placeholder="Brief description of this playlist..."
                />
              </div>

              {error && <div className="form-error">{error}</div>}

              <div className="form-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowCreateForm(false)}
                  disabled={creating}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={creating}>
                  {creating ? 'Creating...' : 'Create Playlist'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading-state">Loading playlists...</div>
      ) : error ? (
        <div className="error-state">
          <p>Error: {error}</p>
          <button className="btn-primary" onClick={loadPlaylists}>
            Retry
          </button>
        </div>
      ) : (
        <>
          {officialPlaylists.length > 0 && (
            <section className="playlist-section">
              <h2>Official Playlists</h2>
              <div className="playlist-grid">
                {officialPlaylists.map((playlist) => (
                  <div
                    key={playlist.id}
                    className="playlist-card"
                    onClick={() => navigate(`/videos/playlists/${playlist.id}`)}
                  >
                    <div className="playlist-icon">📚</div>
                    <h3>{playlist.name}</h3>
                    {playlist.description && (
                      <p className="playlist-description-preview">{playlist.description}</p>
                    )}
                    <div className="playlist-stats">
                      <span className="badge badge-official">Official</span>
                      <span>{playlist.video_count} videos</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className="playlist-section">
            <h2>My Playlists</h2>
            {userPlaylists.length === 0 ? (
              <div className="empty-state">
                <p>You haven't created any playlists yet.</p>
                <button className="btn-primary" onClick={() => setShowCreateForm(true)}>
                  Create Your First Playlist
                </button>
              </div>
            ) : (
              <div className="playlist-grid">
                {userPlaylists.map((playlist) => (
                  <div
                    key={playlist.id}
                    className="playlist-card"
                    onClick={() => navigate(`/videos/playlists/${playlist.id}`)}
                  >
                    <div className="playlist-icon">📁</div>
                    <h3>{playlist.name}</h3>
                    {playlist.description && (
                      <p className="playlist-description-preview">{playlist.description}</p>
                    )}
                    <div className="playlist-stats">
                      <span>{playlist.video_count} videos</span>
                      <span className="text-muted">
                        {new Date(playlist.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
