import React, { useState, useEffect, useCallback, useRef } from 'react';

// Spotify Color Palette
const SPOTIFY_GREEN = '#1DB954';
const SPOTIFY_BLACK = '#121212';
const SPOTIFY_DARK_GRAY = '#191414';
const SPOTIFY_TEXT_GRAY = '#b3b3b3';
const SPOTIFY_WHITE = '#FFFFFF';

// --- UI Components ---

const LoadingSpinner = () => (
  <div className="flex justify-center items-center p-4">
    <div className="w-8 h-8 border-4 border-t-transparent rounded-full animate-spin" style={{ borderColor: SPOTIFY_GREEN }}></div>
  </div>
);

const SongCard = ({ trackName, artists }) => (
  <div className="flex items-center p-3 rounded-lg hover:bg-white/10 transition-colors duration-200">
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={SPOTIFY_TEXT_GRAY} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle>
    </svg>
    <div className="ml-4">
      <p className="font-semibold text-white">{trackName}</p>
      <p className="text-sm" style={{ color: SPOTIFY_TEXT_GRAY }}>{artists}</p>
    </div>
  </div>
);

const RecommendationForm = ({ onSubmit, isLoading }) => {
  const [playlistId, setPlaylistId] = useState('405000');
  const [numRecs, setNumRecs] = useState('10');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(playlistId, numRecs);
  };

  return (
    <form onSubmit={handleSubmit} className="p-6 rounded-lg mb-8" style={{ backgroundColor: SPOTIFY_DARK_GRAY }}>
      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <label htmlFor="playlistId" className="block text-sm font-medium mb-2" style={{ color: SPOTIFY_TEXT_GRAY }}>Playlist ID</label>
          <input
            value={playlistId}
            onChange={(e) => setPlaylistId(e.target.value)}
            type="number"
            id="playlistId"
            className="w-full bg-white/10 p-3 rounded-md text-white border-0 focus:ring-2 focus:ring-inset focus:ring-[#1DB954]"
            placeholder="e.g., 405000"
            required
          />
        </div>
        <div>
          <label htmlFor="numRecs" className="block text-sm font-medium mb-2" style={{ color: SPOTIFY_TEXT_GRAY }}>Recommendations per page</label>
          <input
            value={numRecs}
            onChange={(e) => setNumRecs(e.target.value)}
            type="number"
            id="numRecs"
            className="w-full bg-white/10 p-3 rounded-md text-white border-0 focus:ring-2 focus:ring-inset focus:ring-[#1DB954]"
            placeholder="e.g., 10"
            required
          />
        </div>
      </div>
      <div className="mt-6">
        <button
          type="submit"
          disabled={isLoading}
          className="w-full font-bold py-3 px-4 rounded-full text-black transition-transform duration-200 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ backgroundColor: SPOTIFY_GREEN }}
        >
          {isLoading ? 'Loading...' : 'Get Recommendations'}
        </button>
      </div>
    </form>
  );
};

// --- Main App Component ---
function App() {
  const [recommendations, setRecommendations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [formParams, setFormParams] = useState({ playlistId: null, recsPerPage: 10 });

  const fetchRecommendations = useCallback(async (currentParams, currentPage) => {
    if (isLoading || !currentParams.playlistId) return;
    setIsLoading(true);
    setError(null);
    try {
      // --- THIS IS THE REAL API CALL ---
      const apiResponse = await fetch('http://127.0.0.1:8000/recommendations/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          playlist_id: parseInt(currentParams.playlistId),
          page: currentPage,
          page_size: parseInt(currentParams.recsPerPage),
        }),
      });

      if (!apiResponse.ok) {
        const errData = await apiResponse.json();
        throw new Error(errData.detail || 'Failed to fetch data');
      }

      const response = await apiResponse.json();
      
      setRecommendations(prev => currentPage === 1 ? response.recommendations : [...prev, ...response.recommendations]);
      setHasMore(response.hasMore);
      setPage(currentPage + 1);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  const handleFormSubmit = (playlistId, recsPerPage) => {
    const newParams = { playlistId, recsPerPage };
    setFormParams(newParams);
    setRecommendations([]); 
    setPage(1);
    setHasMore(false);
    fetchRecommendations(newParams, 1);
  };

  const observer = useRef();
  const lastRecommendationElementRef = useCallback(node => {
    if (isLoading) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        fetchRecommendations(formParams, page);
      }
    });
    if (node) observer.current.observe(node);
  }, [isLoading, hasMore, fetchRecommendations, formParams, page]);

  return (
    <div className="min-h-screen text-white p-4 md:p-8" style={{ backgroundColor: SPOTIFY_BLACK }}>
      <div className="max-w-2xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-extrabold" style={{ color: SPOTIFY_GREEN }}>GNN Music Recommender</h1>
          <p className="mt-2" style={{ color: SPOTIFY_TEXT_GRAY }}>Enter a playlist ID to discover new music.</p>
        </header>

        <main>
          <RecommendationForm onSubmit={handleFormSubmit} isLoading={isLoading && page === 1} />
          
          {error && <div className="text-center text-red-400 p-4 bg-red-900/20 rounded-lg">{error}</div>}

          <div className="space-y-2">
            {recommendations.map((song, index) => {
              const elementKey = `${song.track_name_x}-${index}`;
              if (recommendations.length === index + 1) {
                return <div ref={lastRecommendationElementRef} key={elementKey}><SongCard trackName={song.track_name_x} artists={song.artists} /></div>;
              } else {
                return <SongCard key={elementKey} trackName={song.track_name_x} artists={song.artists} />;
              }
            })}
          </div>

          {isLoading && <LoadingSpinner />}
          
          {!isLoading && !hasMore && recommendations.length > 0 && (
            <p className="text-center p-4" style={{ color: SPOTIFY_TEXT_GRAY }}>You've reached the end of the recommendations!</p>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;

