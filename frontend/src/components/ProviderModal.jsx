import React from 'react';

export default function ProviderModal({
  isOpen,
  onClose,
  providers,
  activeProvider,
  onSelectProvider
}) {
  if (!isOpen) return null;

  const providerDescriptions = {
    simulated: 'Offline Demonstration Mode. Zero external API keys or Ollama daemon required. Runs deterministic, grounded synthesis over podcast transcripts.',
    anthropic: 'Claude 3.5 Sonnet via Anthropic Messages API. Requires ANTHROPIC_API_KEY in .env.',
    openai: 'GPT-4o-mini via OpenAI Chat Completions API. Requires OPENAI_API_KEY in .env.',
    ollama: 'Local LLM (e.g. Llama 3.2) running natively via Ollama on http://localhost:11434.'
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="provider-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Configure LLM Provider</h3>
          <button className="icon-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Switch the active intelligence engine dynamically without restarting the server:
          </p>

          {providers.map((p) => {
            const isSelected = p.name === activeProvider;
            return (
              <div
                key={p.name}
                className={`provider-option-card ${isSelected ? 'selected' : ''}`}
                onClick={() => onSelectProvider(p.name)}
              >
                <div className="provider-info">
                  <h4>
                    <span>{isSelected ? '◉' : '○'}</span> {p.name.toUpperCase()}
                    {p.name === 'simulated' && (
                      <span style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)' }}>
                        (Recommended for instant testing)
                      </span>
                    )}
                  </h4>
                  <p>{providerDescriptions[p.name] || `Model: ${p.model}`}</p>
                </div>

                <div>
                  <span className={`status-indicator ${p.available ? 'ready' : 'missing'}`}>
                    {p.available ? 'Available' : 'No Key / Offline'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
