import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import * as videoApi from '../api/videos';
import { VideoPlayer } from './VideoPlayer';
import '../styles/videos.css';

export function VideoBrowser() {
  const { token } = useAuth();
  const [videos, setVideos] = useState<videoApi.Video[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<videoApi.Video | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [subjectFilter, setSubjectFilter] = useState<string>('');
  const [systemFilter, setSystemFilter] = useState<string>('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('');

  const subjects = [
    'Anatomy',
    'Behavioral Science',
    'Biochemistry',
    'Biostatistics',
    'Immunology',
    'Microbiology',
    'Pathology',
    'Pharmacology',
    'Physiology',
  ];

  const systems = [
    'Cardiovascular',
    'Endocrine',
    'Gastrointestinal',
    'Hematologic/Lymphatic',
    'Musculoskeletal',
    'Nervous',
    'Renal',
    'Reproductive',
    'Respiratory',
    'Skin/Connective Tissue',
    'Multisystem',
  ];

  const difficulties = ['Easy', 'Medium', 'Hard'];

  useEffect(() => {
    loadVideos();
  }, [subjectFilter, systemFilter, difficultyFilter, token]);

  const loadVideos = async () => {
    try {
      setLoading(true);
      setError(null);

      const results = await videoApi.listVideos(
        subjectFilter || undefined,
        systemFilter || undefined,
        difficultyFilter || undefined,
        undefined,
        token || undefined
      );

      setVideos(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load videos');
    } finally {
      setLoading(false);
    }
  };

  const handleVideoClick = (video: videoApi.Video) => {
    setSelectedVideo(video);
  };

  const handleClosePlayer = () => {
    setSelectedVideo(null);
    // Reload videos to update view counts
    loadVideos();
  };

  if (selectedVideo) {
    return <VideoPlayer video={selectedVideo} onClose={handleClosePlayer} />;
  }

  return (
    <div className="video-browser">
      <div className="video-browser-header">
        <h1>Video Library</h1>
        <p>High-yield medical education videos organized by subject and system</p>
      </div>

      <div className="video-filters">
        <div className="filter-group">
          <label htmlFor="subject">Subject</label>
          <select
            id="subject"
            value={subjectFilter}
            onChange={(e) => setSubjectFilter(e.target.value)}
          >
            <option value="">All Subjects</option>
            {subjects.map((subject) => (
              <option key={subject} value={subject}>
                {subject}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="system">System</label>
          <select
            id="system"
            value={systemFilter}
            onChange={(e) => setSystemFilter(e.target.value)}
          >
            <option value="">All Systems</option>
            {systems.map((system) => (
              <option key={system} value={system}>
                {system}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="difficulty">Difficulty</label>
          <select
            id="difficulty"
            value={difficultyFilter}
            onChange={(e) => setDifficultyFilter(e.target.value)}
          >
            <option value="">All Difficulties</option>
            {difficulties.map((difficulty) => (
              <option key={difficulty} value={difficulty}>
                {difficulty}
              </option>
            ))}
          </select>
        </div>

        {(subjectFilter || systemFilter || difficultyFilter) && (
          <button
            className="btn-text"
            onClick={() => {
              setSubjectFilter('');
              setSystemFilter('');
              setDifficultyFilter('');
            }}
          >
            Clear Filters
          </button>
        )}
      </div>

      {loading ? (
        <div className="loading-state">Loading videos...</div>
      ) : error ? (
        <div className="error-state">
          <p>Error: {error}</p>
          <button className="btn-primary" onClick={loadVideos}>
            Retry
          </button>
        </div>
      ) : videos.length === 0 ? (
        <div className="empty-state">
          <h2>No videos found</h2>
          <p>Try adjusting your filters or check back later for new content.</p>
        </div>
      ) : (
        <>
          <div className="results-count">
            {videos.length} video{videos.length !== 1 ? 's' : ''} found
          </div>
          <div className="video-grid">
            {videos.map((video) => (
              <div
                key={video.id}
                className="video-card"
                onClick={() => handleVideoClick(video)}
              >
                {video.thumbnail_url ? (
                  <img
                    src={video.thumbnail_url}
                    alt={video.title}
                    className="video-thumbnail"
                  />
                ) : (
                  <div className="video-thumbnail-placeholder">
                    <span>🎥</span>
                  </div>
                )}

                <div className="video-card-content">
                  <h3>{video.title}</h3>
                  <p className="video-description-preview">
                    {video.description.substring(0, 100)}
                    {video.description.length > 100 ? '...' : ''}
                  </p>

                  <div className="video-metadata">
                    <span className="badge badge-subject">{video.subject}</span>
                    <span className="badge badge-system">{video.system}</span>
                    {video.difficulty && (
                      <span className={`badge badge-difficulty badge-${video.difficulty.toLowerCase()}`}>
                        {video.difficulty}
                      </span>
                    )}
                  </div>

                  <div className="video-stats">
                    <span>⏱️ {videoApi.formatDuration(video.duration_seconds)}</span>
                    {video.instructor && <span>👤 {video.instructor}</span>}
                    <span>👁️ {video.view_count} views</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
