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
  const [gameEnded, setGameEnded] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState<{\n    target: Song;\n    options: Song[];\n    startTime: number;\n  } | null>(null);
  const [score, setScore] = useState(0);
  const [questionCount, setQuestionCount] = useState(0);
  const [feedback, setFeedback] = useState<'correct' | 'wrong' | null>(null);
  const [difficulty, setDifficulty] = useState<'Easy' | 'Medium' | 'Hard' | 'Very Hard'>('Medium');
  
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const playbackTimerRef = useRef<NodeJS.Timeout | null>(null);
  const nextQuestionTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
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
      case 'Hard': return 1;
      case 'Very Hard': return 0.5;
      default: return 5;
    }
  };

  const playSnippet = (songPath: string, durationOverride?: number, startTimeOverride?: number) => {
    if (!audioRef.current) return;
    const audio = audioRef.current;
    
    // Clear old timers and listeners
    if (playbackTimerRef.current) {
      clearTimeout(playbackTimerRef.current);
    }
    audio.onloadedmetadata = null;
    audio.onseeked = null;

    const cleanPath = songPath.startsWith('/') ? songPath.substring(1) : songPath;
    const fullPath = `${import.meta.env.BASE_URL}${cleanPath}`;
    
    // 1. Mute immediately to prevent hearing the start of the track
    audio.volume = 0;
    audio.src = fullPath;
    
    // 2. Call play() SYNCHRONOUSLY to satisfy strict browser autoplay policies
    const playPromise = audio.play();
    
    audio.onloadedmetadata = () => {
      const duration = audio.duration;
      const snippetLen = durationOverride !== undefined ? durationOverride : getSnippetLength();
      const safeDuration = Math.max(0, duration - snippetLen);
      
      // 3. Use provided startTime or generate a random one
      const startTime = startTimeOverride !== undefined 
        ? startTimeOverride 
        : Math.max(0.001, Math.random() * safeDuration);
        
      audio.currentTime = startTime;

      // Persist the start time so Replay can use the exact same snippet
      if (startTimeOverride === undefined) {
        setCurrentQuestion(prev => prev ? { ...prev, startTime } : null);
      }
    };

    audio.onseeked = () => {
      // 4. 'seeked' means the browser successfully jumped to the random timestamp and buffered
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            audio.volume = 1; // Unmute
            console.log("Playback and seek successful");
            
            const finalLen = durationOverride !== undefined ? durationOverride : getSnippetLength();
            playbackTimerRef.current = setTimeout(() => {
              audio.pause();
            }, finalLen * 1000);
          })
          .catch(e => console.error("Playback failed:", e));
      }
    };
  };

  const startNewQuestion = () => {
    if (!manifest || !selectedArtist) return;

    const artistSongs = manifest.artists[selectedArtist].songs;
    if (artistSongs.length < 4) {
      alert("Not enough songs for this artist to create a quiz!");
      setGameStarted(false);
      return;
    }

    const targetIndex = Math.floor(Math.random() * artistSongs.length);
    const target = artistSongs[targetIndex];

    const others = artistSongs.filter((_, i) => i !== targetIndex);
    const shuffledOthers = others.sort(() => 0.5 - Math.random()).slice(0, 3);
    
    const options = [target, ...shuffledOthers].sort(() => 0.5 - Math.random());

    // We'll generate the startTime inside playSnippet on first call, 
    // but for the Replay to work, we need to persist it.
    // Since we don't know the actual duration until loadedmetadata, 
    // we'll let playSnippet return it or store it after the first seek.
    
    setCurrentQuestion({ 
      target, 
      options, 
      startTime: 0 // placeholder, will be updated by playSnippet
    });
    setFeedback(null);
    
    playSnippet(target.path);
  };

  const handleStartGame = () => {
    // We completely removed the hacky unlock promise block here. 
    // The synchronous play() inside playSnippet handles it cleanly now.
    setGameStarted(true);
    setGameEnded(false);
    setScore(0);
    setQuestionCount(0);
    startNewQuestion();
  };

  const handleGuess = (song: Song) => {
    if (!currentQuestion) return;

    const isCorrect = song.title === currentQuestion.target.title;
    setFeedback(isCorrect ? 'correct' : 'wrong');
    
    if (isCorrect) setScore(s => s + 1);
    
    const newCount = questionCount + 1;
    setQuestionCount(newCount);

    // Play the correct answer for 5 seconds as a reveal
    playSnippet(currentQuestion.target.path, 5);

    setTimeout(() => {
      if (newCount >= 10) {
        setGameEnded(true);
        if (audioRef.current) audioRef.current.pause();
        if (playbackTimerRef.current) clearTimeout(playbackTimerRef.current);
      } else {
        nextQuestionTimerRef.current = setTimeout(() => {
          startNewQuestion();
        }, 6000);
      }
    }, 6000); // Increased to 6s to allow the 5s reveal to play fully
  };

  useEffect(() => {
    return () => {
      if (playbackTimerRef.current) clearTimeout(playbackTimerRef.current);
      if (nextQuestionTimerRef.current) clearTimeout(nextQuestionTimerRef.current);
    };
  }, []);

  if (!manifest) return <div className="flex items-center justify-center min-h-[100dvh] bg-slate-950 text-white">Loading library...</div>;

  return (
    <div className="min-h-[100dvh] bg-slate-950 text-slate-50 font-sans p-4 sm:p-8 flex flex-col items-center justify-center selection:bg-purple-500/30">
      <audio ref={audioRef} />
      
      <h1 className="text-3xl sm:text-4xl font-extrabold mb-8 text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-fuchsia-500 tracking-tight text-center">
        Song Guessing Quiz
      </h1>

      {!gameStarted ? (
        <div className="bg-white/5 backdrop-blur-xl p-6 sm:p-8 rounded-[2rem] shadow-2xl flex flex-col gap-6 w-full max-w-md border border-white/10 relative overflow-hidden">
          <div className="absolute -top-24 -right-24 w-48 h-48 bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />
          
          <div className="relative z-10">
            <label className="block text-sm font-medium mb-2 text-slate-300 ml-1">Select Artist</label>
            <select 
              className="w-full h-14 px-4 rounded-2xl bg-white/5 border border-white/10 focus:ring-2 focus:ring-violet-500 outline-none text-base appearance-none bg-[url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%2394a3b8%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E')] bg-[length:24px] bg-[position:right_16px_center] bg-no-repeat"
              value={selectedArtist}
              onChange={(e) => setSelectedArtist(e.target.value)}
            >
              <option value="" className="bg-slate-900">-- Choose an Artist --</option>
              {Object.keys(manifest.artists).map(artist => (
                <option key={artist} value={artist} className="bg-slate-900">{artist}</option>
              ))}
            </select>
          </div>

          <div className="relative z-10">
            <label className="block text-sm font-medium mb-2 text-slate-300 ml-1">Difficulty</label>
            <select 
              className="w-full h-14 px-4 rounded-2xl bg-white/5 border border-white/10 focus:ring-2 focus:ring-violet-500 outline-none text-base appearance-none bg-[url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%2394a3b8%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E')] bg-[length:24px] bg-[position:right_16px_center] bg-no-repeat"
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value as any)}
            >
              <option value="Easy" className="bg-slate-900">Easy (10s)</option>
              <option value="Medium" className="bg-slate-900">Medium (5s)</option>
              <option value="Hard" className="bg-slate-900">Hard (1s)</option>
              <option value="Very Hard" className="bg-slate-900">Very Hard (0.5s)</option>
            </select>
          </div>

          <button 
            disabled={!selectedArtist}
            onClick={handleStartGame}
            className="w-full h-14 mt-2 rounded-2xl bg-gradient-to-r from-violet-600 to-fuchsia-600 font-bold text-lg active:scale-95 transition-all disabled:opacity-50 disabled:active:scale-100 shadow-[0_0_20px_rgba(139,92,246,0.3)] hover:shadow-[0_0_25px_rgba(139,92,246,0.5)] z-10"
          >
            Start Game
          </button>
        </div>
      ) : gameEnded ? (
        <div className="bg-white/5 backdrop-blur-xl p-8 rounded-[2rem] shadow-2xl flex flex-col items-center gap-6 w-full max-w-md border border-white/10 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-violet-500/10 to-transparent pointer-events-none" />
          <div className="text-7xl mb-2 drop-shadow-lg z-10">🏆</div>
          <h2 className="text-3xl font-bold z-10">Quiz Finished!</h2>
          <p className="text-slate-300 text-lg z-10">You got <span className="text-white font-extrabold text-2xl">{score}</span> out of 10 correct!</p>
          <button 
            onClick={() => setGameStarted(false)}
            className="w-full h-14 mt-4 rounded-2xl bg-gradient-to-r from-violet-600 to-fuchsia-600 font-bold text-lg active:scale-95 transition-all shadow-[0_0_20px_rgba(139,92,246,0.3)] z-10"
          >
            Play Again
          </button>
        </div>
      ) : (
        <div className="w-full max-w-md flex flex-col items-center gap-6">
          <div className="flex justify-between items-center w-full bg-white/5 backdrop-blur-md border border-white/10 rounded-full px-5 py-3 text-sm font-medium text-slate-300 shadow-sm">
            <span className="truncate max-w-[100px]">{selectedArtist}</span>
            <span className="bg-white/10 px-3 py-1 rounded-full text-white">{Math.min(questionCount + 1, 10)} / 10</span>
            <span className="flex items-center gap-1">★ {score}</span>
          </div>

          <div className="relative w-full aspect-square max-h-64 bg-slate-900 rounded-3xl border border-white/10 flex items-center justify-center overflow-hidden shadow-2xl">
            <div className={`absolute inset-0 transition-all duration-500 ${
              feedback === 'correct' ? 'bg-emerald-500/20 opacity-100' : feedback === 'wrong' ? 'bg-rose-500/20 opacity-100' : 'bg-violet-500/5 opacity-50'
            }`} />
            
            <div className="text-center z-10 flex flex-col items-center">
              <div className={`text-7xl mb-4 transition-transform duration-500 drop-shadow-xl ${
              feedback === 'correct' ? 'scale-125' : feedback === 'wrong' ? 'animate-bounce' : 'animate-pulse'
              }`}>
                {feedback === 'correct' ? '✅' : feedback === 'wrong' ? '❌' : '🎵'}
              </div>
              <p className="text-slate-300 font-medium tracking-wide">
                {feedback === null ? 'Listen closely...' : feedback === 'correct' ? 'Correct!' : 'Incorrect'}
              </p>
            </div>
          </div>

          <button 
            disabled={!currentQuestion}
            onClick={() => {
              if (feedback) {
                // Clear any pending auto-next timers before jumping
                if (nextQuestionTimerRef.current) {
                  clearTimeout(nextQuestionTimerRef.current);
                }
                startNewQuestion();
              } else {
                playSnippet(
                  currentQuestion.target.path, 
                  undefined, 
                  currentQuestion.startTime
                );
              }
            }}
            className="flex items-center justify-center gap-2 w-full h-12 rounded-2xl bg-white/5 border border-white/10 text-slate-300 font-medium transition-all active:scale-95 disabled:opacity-30 hover:bg-white/10"
          >
            <span className="text-lg">{feedback ? '⏭️' : '🔄'}</span> {feedback ? 'Next Question' : 'Replay Snippet'}
          </button>

          <div className="flex flex-col gap-3 w-full mt-2">
            {currentQuestion?.options.map((song, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleGuess(song)}
                disabled={feedback !== null}
                className={`w-full min-h-[4rem] px-5 py-4 text-base sm:text-lg font-medium rounded-2xl border transition-all active:scale-95 text-left flex items-center ${
                  feedback === null 
                  ? 'bg-white/5 border-white/10 hover:bg-white/10' 
                  : song.title === currentQuestion.target.title
                    ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-200' 
                    : 'bg-white/5 border-white/10 opacity-40'
                }`}
              >
                {song.title}
              </button>
            ))}
          </div>

          <button 
            onClick={() => setGameStarted(false)}
            className="mt-4 text-slate-500 hover:text-slate-300 text-sm font-medium transition-colors active:scale-95 px-6 py-2"
          >
            Quit to Menu
          </button>
        </div>
      )}
    </div>
  );
};

export default SongGuessingApp;
