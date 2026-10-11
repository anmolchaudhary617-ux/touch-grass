import { useState } from 'react';
import './adventureMode.css';

function AdventureMode({ mission, onEnd }) {
const [screen, setScreen] = useState('briefing');
const [observation, setObservation] = useState('');
const [nextClue, setNextClue] = useState('');
const [loading, setLoading] = useState(false);
const [error, setError] = useState('');

  const submitObservation = async () => {
    if (!observation.trim()) {
      setError('Please describe what you noticed.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(
        'http://127.0.0.1:8000/api/missions/next-clue',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            title: mission.title,
            type: mission.type,
            premise: mission.premise,
            objective: mission.objective,
            current_clue: nextClue || mission.first_clue,
            observation: observation.trim(),
          }),
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Error ${response.status}: ${errorText}`);
      }

      const data = await response.json();

      setNextClue(data.next_clue);
      setObservation('');
      setScreen('next-clue');
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  if (!mission) {
    return null;
  }

  return (
    <section className="adventure-mode">

      {/* Safety briefing */}
      {screen === 'briefing' && (
        <div className="adventure-card">
          <p className="adventure-label">BEFORE YOU START</p>

          <h2>Adventure Safety</h2>

          <p>{mission.safety_brief}</p>

          <ul>
            <li>Stay in safe and appropriate public areas.</li>
            <li>Do not enter restricted or dangerous areas.</li>
            <li>You can pause or end the adventure at any time.</li>
            <li>Your safety is more important than completing the mission.</li>
          </ul>

          <button
            type="button"
            onClick={() => setScreen('clue')}
          >
            Start Adventure
          </button>
        </div>
      )}

      {/* Current clue */}
      {screen === 'clue' && (
        <div className="adventure-card">
          <p className="adventure-label">YOUR FIRST CLUE</p>

          <h2>{mission.first_clue}</h2>

          <p className="phone-away">
            Put your phone away and explore your surroundings.
          </p>

          <button
            type="button"
            onClick={() => setScreen('return-menu')}
          >
            I'm Back
          </button>
        </div>
      )}

      {/* Return menu */}
      {screen === 'return-menu' && (
        <div className="adventure-card">
          <p className="adventure-label">WELCOME BACK</p>

          <h2>What would you like to do?</h2>

          <button
            type="button"
            onClick={() => setScreen('observation')}
          >
            What did you notice?
          </button>

          <button
            type="button"
            onClick={() => setScreen('break')}
          >
            Take a short break
          </button>

          <button
            type="button"
            onClick={() => setScreen('safety')}
          >
            Safety / Emergency
          </button>
        </div>
      )}

      {/* Observation */}
      {screen === 'observation' && (
        <div className="adventure-card">
          <p className="adventure-label">YOUR OBSERVATION</p>

          <h2>What did you notice?</h2>

          <textarea
            placeholder="Describe what you noticed..."
            rows="6"
            value={observation}
            onChange={(event) => setObservation(event.target.value)}
            disabled={loading}
          />

          {error && (
            <p className="adventure-error">
              {error}
            </p>
          )}

          <button
            type="button"
            onClick={submitObservation}
            disabled={loading}
          >
            {loading ? 'Thinking...' : 'Submit Observation'}
          </button>

          <button
            type="button"
            onClick={() => setScreen('return-menu')}
            disabled={loading}
          >
            Back
          </button>
        </div>
      )}

      {screen === 'next-clue' && (
        <div className="adventure-card">
          <p className="adventure-label">NEXT CLUE</p>

          <h2>{nextClue}</h2>

          <p className="phone-away">
            Put your phone away and continue exploring.
          </p>

          <button
            type="button"
            onClick={() => setScreen('return-menu')}
          >
            I'm Back
          </button>
        </div>
      )}
      {/* Break */}
      {screen === 'break' && (
        <div className="adventure-card">
          <p className="adventure-label">SHORT BREAK</p>

          <h2>Take a moment.</h2>

          <p>Choose how long you'd like to pause.</p>

          <button type="button">1 minute</button>

          <button type="button">3 minutes</button>

          <button type="button">5 minutes</button>

          <button
            type="button"
            onClick={() => setScreen('return-menu')}
          >
            Back
          </button>
        </div>
      )}

      {/* Safety / Emergency */}
      {screen === 'safety' && (
        <div className="adventure-card">
          <p className="adventure-label">SAFETY</p>

          <h2>Safety comes first.</h2>

          <p>
            If you feel unsafe or uncomfortable, stop the adventure.
            You never need to complete a mission at the expense of your safety.
          </p>

          <button
            type="button"
            onClick={() => setScreen('return-menu')}
          >
            Continue Adventure
          </button>

          <button
            type="button"
            onClick={onEnd}
          >
            End Adventure
          </button>
        </div>
      )}

    </section>
  );
}

export default AdventureMode;