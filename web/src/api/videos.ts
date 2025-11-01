import { apiClient } from './client';

// Types matching backend models
export interface Video {
  id: number;
  title: string;
  description: string;
  video_url: string;
  thumbnail_url: string | null;
  duration_seconds: number;
  subject: string;
  system: string;
  topic: string | null;
  instructor: string | null;
  difficulty: string;
  tags: string | null;
  view_count: number;
  created_at: string;
  updated_at: string;
}

export interface Playlist {
  id: number;
  user_id: number | null;
  name: string;
  description: string | null;
  is_official: boolean;
  video_count: number;
  created_at: string;
  updated_at: string;
}

export interface VideoProgress {
  id: number;
  user_id: number;
  video_id: number;
  progress_seconds: number;
  completed: boolean;
  last_watched: string;
}

export interface Bookmark {
  id: number;
  user_id: number;
  video_id: number;
  timestamp_seconds: number;
  note: string | null;
  created_at: string;
}

export interface VideoCreate {
  title: string;
  description: string;
  video_url: string;
  thumbnail_url?: string;
  duration_seconds: number;
  subject: string;
  system: string;
  topic?: string;
  instructor?: string;
  difficulty?: string;
  tags?: string;
}

export interface PlaylistCreate {
  name: string;
  description?: string;
}

export interface BookmarkCreate {
  video_id: number;
  timestamp_seconds: number;
  note?: string;
}

export interface ProgressUpdate {
  progress_seconds: number;
  completed: boolean;
}

const VIDEO_BASE = 'http://localhost:8007';

// Video operations
export async function listVideos(
  subject?: string,
  system?: string,
  difficulty?: string,
  limit?: number,
  token?: string
): Promise<Video[]> {
  const params = new URLSearchParams();
  if (subject) params.append('subject', subject);
  if (system) params.append('system', system);
  if (difficulty) params.append('difficulty', difficulty);
  if (limit) params.append('limit', limit.toString());

  const query = params.toString();
  const url = `${VIDEO_BASE}/videos${query ? `?${query}` : ''}`;

  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  return apiClient(url, { headers });
}

export async function getVideo(videoId: number, token?: string): Promise<Video> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  return apiClient(`${VIDEO_BASE}/videos/${videoId}`, { headers });
}

export async function createVideo(data: VideoCreate, token: string): Promise<Video> {
  return apiClient(`${VIDEO_BASE}/videos`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
}

export async function recordView(videoId: number, token?: string): Promise<void> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  await apiClient(`${VIDEO_BASE}/videos/${videoId}/view`, {
    method: 'POST',
    headers,
  });
}

// Playlist operations
export async function listPlaylists(
  officialOnly: boolean = false,
  token?: string
): Promise<Playlist[]> {
  const params = officialOnly ? '?official_only=true' : '';
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  return apiClient(`${VIDEO_BASE}/playlists${params}`, { headers });
}

export async function getPlaylist(playlistId: number, token?: string): Promise<Playlist> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  return apiClient(`${VIDEO_BASE}/playlists/${playlistId}`, { headers });
}

export async function createPlaylist(data: PlaylistCreate, token: string): Promise<Playlist> {
  return apiClient(`${VIDEO_BASE}/playlists`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
}

export async function deletePlaylist(playlistId: number, token: string): Promise<void> {
  await apiClient(`${VIDEO_BASE}/playlists/${playlistId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

export async function getPlaylistVideos(playlistId: number, token?: string): Promise<Video[]> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  return apiClient(`${VIDEO_BASE}/playlists/${playlistId}/videos`, { headers });
}

export async function addVideoToPlaylist(
  playlistId: number,
  videoId: number,
  token: string
): Promise<void> {
  await apiClient(`${VIDEO_BASE}/playlists/${playlistId}/videos`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ video_id: videoId }),
  });
}

export async function removeVideoFromPlaylist(
  playlistId: number,
  videoId: number,
  token: string
): Promise<void> {
  await apiClient(`${VIDEO_BASE}/playlists/${playlistId}/videos/${videoId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// Progress operations
export async function getProgress(videoId: number, token: string): Promise<VideoProgress | null> {
  try {
    return await apiClient(`${VIDEO_BASE}/progress/${videoId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  } catch (error) {
    // Return null if no progress found
    return null;
  }
}

export async function updateProgress(
  videoId: number,
  data: ProgressUpdate,
  token: string
): Promise<VideoProgress> {
  return apiClient(`${VIDEO_BASE}/progress`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ ...data, video_id: videoId }),
  });
}

// Bookmark operations
export async function getBookmarks(videoId: number, token: string): Promise<Bookmark[]> {
  return apiClient(`${VIDEO_BASE}/videos/${videoId}/bookmarks`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

export async function createBookmark(data: BookmarkCreate, token: string): Promise<Bookmark> {
  return apiClient(`${VIDEO_BASE}/bookmarks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
}

export async function deleteBookmark(bookmarkId: number, token: string): Promise<void> {
  await apiClient(`${VIDEO_BASE}/bookmarks/${bookmarkId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// Utility functions
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

export function formatProgress(current: number, total: number): number {
  return Math.round((current / total) * 100);
}
