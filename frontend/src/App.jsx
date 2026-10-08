import { useState } from 'react';
import './App.css';
import './missionSetup.css';

function App() {
  const [adventure, setAdventure] = useState('');
  const [duration, setDuration] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mission, setMission] = useState(null);

  const adventureOptions = [
    { value: 'investigate', label: 'Investigate' },
    { value: 'observe', label: 'Observe' },
    { value: 'discover', label: 'Discover' },
  ];
  const durationOptions = [
    { value: '10-15', label: '10–15 min' },
    { value: '20-30', label: '20–30 min' },
    { value: '30-45', label: '30–45 min' },
  ];

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://127.0.0.1:8000/api/missions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ adventure_type: adventure, duration }),
      });
      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`Error ${response.status}: ${errText}`);
      }
      const data = await response.json();
      setMission(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header>
        <h1>Touch Grass – Mission Setup</h1>
      </header>
      <section className="setup">
        <div className="option-group">
          <h2>Adventure Type</h2>
          <div className="options">
            {adventureOptions.map((opt) => (
              <button
                key={opt.value}
                className={`option-btn ${adventure === opt.value ? 'active' : ''}`}
                type="button"
                onClick={() => setAdventure(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="option-group">
          <h2>Duration</h2>
          <div className="options">
            {durationOptions.map((opt) => (
              <button
                key={opt.value}
                className={`option-btn ${duration === opt.value ? 'active' : ''}`}
                type="button"
                onClick={() => setDuration(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <button
          className="create-btn"
          onClick={handleSubmit}
          disabled={!adventure || !duration || loading}
        >
          {loading ? 'Creating...' : 'Create Mission'}
        </button>
        {error && <p className="error">Error: {error}</p>}
      </section>

      {mission && (
        <section className="preview">
          <h2>Mission Preview</h2>
          <h3>{mission.title}</h3>
          <p><strong>Estimated Time:</strong> {mission.estimated_time}</p>
          <p><strong>Premise:</strong> {mission.premise}</p>
          <p><strong>Objective:</strong> {mission.objective}</p>
          <p><strong>Safety Brief:</strong> {mission.safety_brief}</p>
          <p><strong>First Clue:</strong> {mission.first_clue}</p>
        </section>
      )}
    </div>
  );
}

export default App;