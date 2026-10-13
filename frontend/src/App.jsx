
import { useState } from 'react';
import './App.css';
import './missionSetup.css';
import AdventureMode from './AdventureMode';

function App() {
  const [adventure, setAdventure] = useState('');
  const [duration, setDuration] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mission, setMission] = useState(null);
  const [adventureStarted, setAdventureStarted] = useState(false);

  const adventureOptions = [
    {
      value: 'investigate',
      label: 'Investigate',
      description: 'Follow clues and uncover details.',
    },
    {
      value: 'observe',
      label: 'Observe',
      description: 'Slow down and notice nature.',
    },
    {
      value: 'discover',
      label: 'Discover',
      description: 'Find something unexpected.',
    },
  ];

  const durationOptions = [
    { value: '10-15', label: '10–15 min' },
    { value: '20-30', label: '20–30 min' },
    { value: '30-45', label: '30–45 min' },
  ];

  const handleSubmit = async () => {
    if (!adventure || !duration || loading) return;

    setLoading(true);
    setError('');
    setMission(null);
    setAdventureStarted(false);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/missions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ adventure_type: adventure, duration }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Error ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      setMission(data);
    } catch (e) {
      setError(
        e.message.includes('Failed to fetch')
          ? 'Could not connect to the mission generator. Check that the backend and Ollama are running, then try again.'
          : e.message
      );
    } finally {
      setLoading(false);
    }
  };

  const resetApp = () => {
    setAdventure('');
    setDuration('');
    setMission(null);
    setAdventureStarted(false);
    setError('');
  };

  return (
    <div className="app-container">
      <header className="site-header">
        <button
          className="brand"
          type="button"
          onClick={resetApp}
          aria-label="Touch Grass home"
        >
          <span className="brand-icon">TG</span>
          <span>
            touch<span className="brand-light">grass</span>
          </span>
        </button>

        <span className="header-tag">
          <span className="status-dot" />
          YOUR OUTDOOR RESET
        </span>
      </header>

      <main>
        {!adventureStarted && (
          <section className="hero">
            <div className="hero-eyebrow">
              A LITTLE LESS SCREEN. A LITTLE MORE LIFE.
            </div>

            <h1>
              The world is waiting<span className="hero-period">.</span>
            </h1>

            <p className="hero-copy">
              Turn an ordinary walk into a small adventure. Let AI give you
              a mission. Then put your phone away and see what you discover.
            </p>

            <div className="hero-pills">
              <span>Get outside</span>
              <span>Notice more</span>
              <span>Be present</span>
            </div>
          </section>
        )}

        {!adventureStarted && (
          <section className="setup-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">YOUR NEXT ADVENTURE</p>
                <h2>Make today a little different.</h2>
              </div>

              <span className="step-badge">01 / PLAN</span>
            </div>

            <div className="option-group">
              <h3>What feels right today?</h3>

              <div className="options adventure-options">
                {adventureOptions.map((option) => (
                  <button
                    key={option.value}
                    className={`option-btn adventure-option ${
                      adventure === option.value ? 'active' : ''
                    }`}
                    type="button"
                    aria-pressed={adventure === option.value}
                    onClick={() => setAdventure(option.value)}
                  >
                    <span className="option-text">
                      <strong>{option.label}</strong>
                      <small>{option.description}</small>
                    </span>

                    <span className="option-check" aria-hidden="true">
                      {adventure === option.value ? 'Selected' : 'Select'}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div className="option-group duration-group">
              <h3>How much time do you have?</h3>

              <div className="options duration-options">
                {durationOptions.map((option) => (
                  <button
                    key={option.value}
                    className={`option-btn duration-option ${
                      duration === option.value ? 'active' : ''
                    }`}
                    type="button"
                    aria-pressed={duration === option.value}
                    onClick={() => setDuration(option.value)}
                  >
                    <span>{option.label}</span>
                    <small>
                      {duration === option.value ? 'Selected' : 'minutes'}
                    </small>
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}

            <button
              className="create-btn"
              type="button"
              onClick={handleSubmit}
              disabled={!adventure || !duration || loading}
            >
              {loading ? (
                <>
                  <span className="loading-spinner" />
                  Creating your mission...
                </>
              ) : (
                'Create my adventure'
              )}
            </button>

            <p className="setup-note">
              No rush. No leaderboard. Just you and the outside world.
            </p>
          </section>
        )}

        {mission && !adventureStarted && (
          <section className="preview">
            <div className="preview-topline">
              <p className="eyebrow">YOUR MISSION IS READY</p>
              <span className="mission-ready">READY TO GO</span>
            </div>

            <h2>{mission.title}</h2>
            <p className="mission-premise">{mission.premise}</p>

            <div className="mission-details">
              <div>
                <small>TIME</small>
                <strong>{mission.estimated_time || `${duration} min`}</strong>
              </div>

              <div>
                <small>STYLE</small>
                <strong>{adventure}</strong>
              </div>
            </div>

            <div className="mission-objective">
              <p className="eyebrow">YOUR OBJECTIVE</p>
              <p>{mission.objective}</p>
            </div>

            <div className="first-clue">
              <p className="eyebrow">YOUR FIRST CLUE</p>
              <p>{mission.first_clue}</p>
            </div>

            <button
              className="create-btn"
              type="button"
              onClick={() => setAdventureStarted(true)}
            >
              Let's get outside
            </button>

            <button className="text-btn" type="button" onClick={resetApp}>
              Make a different mission
            </button>
          </section>
        )}

        {adventureStarted && (
          <AdventureMode
            mission={mission}
            onEnd={() => {
              setAdventureStarted(false);
              setMission(null);
              setAdventure('');
              setDuration('');
              setError('');
            }}
          />
        )}
      </main>

      {!adventureStarted && (
        <footer className="site-footer">
          <span>MADE FOR THE MOMENTS BETWEEN SCREENS</span>
          <span>
            Take only memories. Leave nature as you found it.
          </span>
        </footer>
      )}
    </div>
  );
}

export default App;
