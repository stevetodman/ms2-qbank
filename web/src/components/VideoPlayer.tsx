import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import * as videoApi from '../api/videos';
import { QuickNote } from './QuickNote';
import '../styles/videos.css';

interface VideoPlayerProps {
  video: videoApi.Video;
  onClose?: () => void;
}

export function VideoPlayer({ video, onClose }: VideoPlayerProps) {
  const { token } = useAuth();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [volume, setVolume] = useState(1);
  const [showBookmarkForm, setShowBookmarkForm] = useState(false);
  const [bookmarkNote, setBookmarkNote] = useState('');
  const [bookmarks, setBookmarks] = useState<videoApi.Bookmark[]>([]);
  const [progress, setProgress] = useState<videoApi.VideoProgress | null>(null);

  useEffect(() => {
    loadInitialData();
    recordView();
  }, [video.id, token]);

  useEffect(() => {
    // Auto-save progress every 10 seconds
    const interval = setInterval(() => {
      if (isPlaying && token) {
        saveProgress(false);
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [isPlaying, currentTime, token]);

  const loadInitialData = async () => {
    if (!token) return;

    try {
      // Load progress
      const prog = await videoApi.getProgress(video.id, token);
      if (prog) {
        setProgress(prog);
        if (videoRef.current) {
          videoRef.current.currentTime = prog.progress_seconds;
        }
      }

      // Load bookmarks
      const bmarks = await videoApi.getBookmarks(video.id, token);
      setBookmarks(bmarks);
    } catch (error) {
      console.error('Failed to load video data:', error);
    }
  };

  const recordView = async () => {
    try {
      await videoApi.recordView(video.id, token || undefined);
    } catch (error) {
      console.error('Failed to record view:', error);
    }
  };

  const saveProgress = async (completed: boolean) => {
    if (!token) return;

    try {
      await videoApi.updateProgress(
        video.id,
        {
          progress_seconds: Math.floor(currentTime),
          completed,
        },
        token
      );
    } catch (error) {
      console.error('Failed to save progress:', error);
    }
  };

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);

      // Mark as completed when 90% watched
      if (
        token &&
        !progress?.completed &&
        videoRef.current.currentTime / videoRef.current.duration > 0.9
      ) {
        saveProgress(true);
      }
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleSeek = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
    if (videoRef.current) {
      videoRef.current.playbackRate = speed;
    }
  };

  const handleVolumeChange = (vol: number) => {
    setVolume(vol);
    if (videoRef.current) {
      videoRef.current.volume = vol;
    }
  };

  const handleCreateBookmark = async () => {
    if (!token) return;

    try {
      const bookmark = await videoApi.createBookmark(
        {
          video_id: video.id,
          timestamp_seconds: Math.floor(currentTime),
          note: bookmarkNote || undefined,
        },
        token
      );

      setBookmarks([...bookmarks, bookmark]);
      setBookmarkNote('');
      setShowBookmarkForm(false);
    } catch (error) {
      console.error('Failed to create bookmark:', error);
    }
  };

  const handleDeleteBookmark = async (bookmarkId: number) => {
    if (!token) return;

    try {
      await videoApi.deleteBookmark(bookmarkId, token);
      setBookmarks(bookmarks.filter((b) => b.id !== bookmarkId));
    } catch (error) {
      console.error('Failed to delete bookmark:', error);
    }
  };

  const handleJumpToBookmark = (timestamp: number) => {
    handleSeek(timestamp);
  };

  const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="video-player-container">
      <div className="video-player-header">
        <div>
          <h2>{video.title}</h2>
          <div className="video-meta">
            <span className="badge">{video.subject}</span>
            <span className="badge">{video.system}</span>
            {video.instructor && <span className="badge">👤 {video.instructor}</span>}
            <span className="badge">⏱️ {videoApi.formatDuration(video.duration_seconds)}</span>
          </div>
        </div>
        {onClose && (
          <button className="btn-text" onClick={onClose}>
            ✕ Close
          </button>
        )}
      </div>

      <div className="video-wrapper">
        <video
          ref={videoRef}
          src={video.video_url}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onClick={handlePlayPause}
        />

        <div className="video-controls">
          <div className="progress-bar" onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / rect.width;
            handleSeek(pos * duration);
          }}>
            <div className="progress-fill" style={{ width: `${progressPercentage}%` }} />
            {bookmarks.map((bookmark) => {
              const position = (bookmark.timestamp_seconds / duration) * 100;
              return (
                <div
                  key={bookmark.id}
                  className="bookmark-marker"
                  style={{ left: `${position}%` }}
                  title={bookmark.note || 'Bookmark'}
                />
              );
            })}
          </div>

          <div className="controls-row">
            <button className="control-btn" onClick={handlePlayPause}>
              {isPlaying ? '⏸' : '▶'}
            </button>

            <span className="time-display">
              {videoApi.formatDuration(Math.floor(currentTime))} /{' '}
              {videoApi.formatDuration(Math.floor(duration))}
            </span>

            <div className="spacer" />

            <div className="control-group">
              <label>Speed:</label>
              <select
                value={playbackSpeed}
                onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
              >
                <option value="0.5">0.5x</option>
                <option value="0.75">0.75x</option>
                <option value="1">1x</option>
                <option value="1.25">1.25x</option>
                <option value="1.5">1.5x</option>
                <option value="2">2x</option>
              </select>
            </div>

            <div className="control-group">
              <label>🔊</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={volume}
                onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
              />
            </div>

            <button
              className="control-btn"
              onClick={() => setShowBookmarkForm(!showBookmarkForm)}
              title="Add bookmark"
            >
              🔖
            </button>
          </div>
        </div>
      </div>

      {showBookmarkForm && (
        <div className="bookmark-form">
          <input
            type="text"
            value={bookmarkNote}
            onChange={(e) => setBookmarkNote(e.target.value)}
            placeholder="Add a note for this bookmark..."
            autoFocus
          />
          <button className="btn-primary" onClick={handleCreateBookmark}>
            Add Bookmark at {videoApi.formatDuration(Math.floor(currentTime))}
          </button>
          <button className="btn-secondary" onClick={() => setShowBookmarkForm(false)}>
            Cancel
          </button>
        </div>
      )}

      <div className="video-details">
        <div className="video-description">
          <h3>Description</h3>
          <p>{video.description}</p>
        </div>

        <div className="video-notes-section">
          <QuickNote
            videoId={String(video.id)}
            timestamp={Math.floor(currentTime)}
            compact={true}
            onSuccess={() => {
              // Optionally reload notes or show success message
            }}
          />
        </div>

        {bookmarks.length > 0 && (
          <div className="bookmarks-section">
            <h3>Bookmarks ({bookmarks.length})</h3>
            <div className="bookmarks-list">
              {bookmarks.map((bookmark) => (
                <div key={bookmark.id} className="bookmark-item">
                  <button
                    className="bookmark-time"
                    onClick={() => handleJumpToBookmark(bookmark.timestamp_seconds)}
                  >
                    {videoApi.formatDuration(bookmark.timestamp_seconds)}
                  </button>
                  <span className="bookmark-note">{bookmark.note || '(no note)'}</span>
                  <button
                    className="btn-text btn-danger"
                    onClick={() => handleDeleteBookmark(bookmark.id)}
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
