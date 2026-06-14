import React, { useState, useEffect, useRef } from 'react';

interface Song {
  title: string;
  path: string;
  popularity: number;
}

interface ArtistData {
  songs: Song[];
}

interface Manifest {
  artists: Record<string, ArtistData>;
}

const SongGuessingApp: React.FC = () => {
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [selectedArtist, setSelectedArtist] = useState<string>('');
  const [gameStarted, setGameStarted] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState<{
    target: Song;
    options: Song[];
  } | null>(null);
  const [score, setScore] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [feedback, setFeedback] = useState<'correct' | 'wrong' | null>(null);
  const [difficulty, setDifficulty] = useState<'Easy' | 'Medium' | 'Hard'>('Medium');
  
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Use import.meta.env.BASE_URL to ensure the path is correct on GitHub Pages
    fetch(`${import.meta.env.BASE_URL}songs.json`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then(data => setManifest(data))
      .catch(err => console.error("Error loading manifest:", err));
  }, []);

  const getSnippetLength = () => {
    switch (difficulty) {
      case 'Easy': return 10;
      case 'Medium': return 5;
      case 'Hard': return 2;
      default: return 5;
    }
  };

  const startNewQuestion = () => {
    if (!manifest || !selectedArtist) return;

    const artistSongs = manifest.artists[selectedArtist].songs;
    if (artistSongs.length < 4) {
      alert("Not enough songs for this artist to create a quiz!");
      return;
    }

    const targetIndex = Math.floor(Math.random() * artistSongs.length);
    const target = artistSongs[targetIndex];

    const others = artistSongs.filter((_, i) => i !== targetIndex);
    const shuffledOthers = others.sort(() => 0.5 - Math.random()).slice(0, 3);
    
    const options = [target, ...shuffledOthers].sort(() => 0.5 - Math.random());

    setCurrentQuestion({ target, options });
    setFeedback(null);
    
    playSnippet(target.path);
  };

  const playSnippet = (songPath: string) => {
    if (!audioRef.current) return;
    
    const audio = audioRef.current;
    // Ensure audio paths also use the BASE_URL if they are absolute
    const fullPath = songPath.startsWith('/') 
      ? `${import.meta.env.BASE_URL}${songPath.substring(1)}` 
      : songPath;
      
    audio.src = fullPath;
    
    audio.onloadedmetadata = () => {
      const duration = audio.duration;
      const snippetLen = getSnippetLength();
      const startTime = Math.random() * (duration - snippetLen);
      
      audio.currentTime = startTime;
      audio.play();
      
      setTimeout(() => {
        audio.pause();
      }, snippetLen * 1000);
    };
  };

  const handleGuess = (song: Song) => {
    if (!currentQuestion) return;

    if (song.title === currentQuestion.target.title) {
      setFeedback('correct');
      setScore(s => s + 1);
    } else {
      setFeedback('wrong');
    }
    setTotalQuestions(t => t + 1);

    setTimeout(() => {
      startNewQuestion();
    }, 1500);
  };

  if (!manifest) return <div className="flex items-center justify-center h-screen bg-slate-900 text-white">Loading library...</div>;

  return (
    <div className="min-h-screen bg-slate-900 text-white font-sans p-8 flex flex-col items-center">
      <audio ref={audioRef} />
      
      <h1 className="text-4xl font-bold mb-8 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600">
        Song Guessing Quiz
      </h1>

      {!gameStarted ? (
        <div className="bg-slate-800 p-8 rounded-2xl shadow-xl flex flex-col gap-6 w-full max-w-md border border-slate-700">
          <div>
            <label className="block text-sm font-medium mb-2 text-slate-400">Select Artist</label>
            <select 
              className="w-full p-3 rounded-lg bg-slate-700 border border-slate-600 focus:ring-2 focus:ring-purple-500 outline-none"
              value={selectedArtist}
              onChange={(e) => setSelectedArtist(e.target.value)}
            >
              <option value="">-- Choose an Artist --</option>
              {Object.keys(manifest.artists).map(artist => (
                <option key={artist} value={artist}>{artist}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-slate-400">Difficulty</label>
            <div className="flex gap-2">
              {['Easy', 'Medium', 'Hard'].map(level => (
                <button
                  key={level}
                  onClick={() => setDifficulty(level as any)}
                  className={`flex-1 py-2 rounded-lg transition-all ${
                    difficulty === level 
                    ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/30' 
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>

          <button 
            disabled={!selectedArtist}
            onClick={() => setGameStarted(true)}
            className="w-full py-4 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 font-bold text-lg hover:scale-105 transition-transform disabled:opacity-50 disabled:hover:scale-100"
          >
            Start Game
          </button>
        </div>
      ) : (
        <div className="w-full max-w-2xl flex flex-col items-center gap-8">
          <div className="flex justify-between w-full text-slate-400 font-medium px-4">
            <span>Artist: {selectedArtist}</span>
            <span>Score: {score} / {totalQuestions}</span>
          </div>

          <div className="relative w-full aspect-video bg-slate-800 rounded-3xl border-4 border-slate-700 flex items-center justify-center overflow-hidden shadow-2xl">
            <div className={`absolute inset-0 transition-colors duration-300 ${
              feedback === 'correct' ? 'bg-green-500/20' : feedback === 'wrong' ? 'bg-red-500/20' : ''
            }`} />
            
            <div className="text-center z-10">
              <div className={`text-6xl mb-4 transition-transform duration-300 ${
                feedback === 'correct' ? 'scale-125' : feedback === 'wrong' ? 'shake' : ''
              }`}>
                {feedback === 'correct' ? '✅' : feedback === 'wrong' ? '❌' : '🎵'}
              </div>
              <p className="text-slate-400 animate-pulse">Listen closely...</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
            {currentQuestion?.options.map((song, i) => (
              <button
                key={i}
                onClick={() => handleGuess(song)}
                className="p-4 text-lg font-medium rounded-xl bg-slate-800 border border-slate-700 hover:bg-slate-700 hover:border-purple-500 transition-all text-left"
              >
                {song.title}
              </button>
            ))}
          </div>

          <button 
            onClick={() => {
              setGameStarted(false);
              setScore(0);
              setTotalQuestions(0);
            }}
            className="text-slate-500 hover:text-slate-300 underline underline-offset-4 text-sm transition-colors"
          >
            Quit to Menu
          </button>
        </div>
      )}
    </div>
  );
};

export default SongGuessingApp;
