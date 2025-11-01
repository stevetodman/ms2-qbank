import { Route, Routes } from 'react-router-dom';
import { VideoBrowser } from '../components/VideoBrowser';
import { PlaylistBrowser } from '../components/PlaylistBrowser';
import { PlaylistManager } from '../components/PlaylistManager';

export const VideosRoute = () => {
  return (
    <Routes>
      <Route index element={<VideoBrowser />} />
      <Route path="playlists" element={<PlaylistBrowser />} />
      <Route path="playlists/:playlistId" element={<PlaylistManager />} />
    </Routes>
  );
};
