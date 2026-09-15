import React from 'react';

export default function Header({
  activeProvider,
  activeModel,
  onOpenProviderModal,
  hasActiveArtifact,
  isArtifactPaneOpen,
  onToggleArtifactPane
}) {
  const getProviderLabel = () => {
    switch (activeProvider) {
      case 'anthropic':
        return 'Claude 3.5 Sonnet';
      case 'openai':
        return 'GPT-4o-mini';
      case 'ollama':
        return 'Local Ollama';
      case 'simulated':
      default:
        return 'Offline Demo Mode';
    }
  };

  return (
    <header className="top-header">
      <div className="header-left">
        <div className="header-title-badge">
          <span>The Lenny Growth Assistant</span>
          <div className="grounded-tag">
            <span>●</span> 100% Grounded in Podcast Transcripts
          </div>
        </div>
      </div>

      <div className="header-right">
        <button
          className="provider-pill"
          onClick={onOpenProviderModal}
          id="btn-provider-toggle"
          title="Click to switch LLM Provider"
        >
          <div className={`provider-dot ${activeProvider === 'simulated' ? 'offline' : ''}`} />
          <span>Model: <strong>{getProviderLabel()}</strong></span>
          <span style={{ fontSize: '0.65rem', opacity: 0.7 }}>▼</span>
        </button>

        {hasActiveArtifact && (
          <button
            className={`icon-btn ${isArtifactPaneOpen ? 'active' : ''}`}
            onClick={onToggleArtifactPane}
            title={isArtifactPaneOpen ? 'Collapse Artifact' : 'View Artifact'}
            id="btn-toggle-artifact"
          >
            📋
          </button>
        )}
      </div>
    </header>
  );
}
