import React from 'react';

export default function Sidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  chunkCount
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-group">
          <div className="logo-icon">🎙️</div>
          <div className="logo-text">
            <h1>Lenny Assistant</h1>
            <span>Grounded Growth AI</span>
          </div>
        </div>
      </div>

      <button className="new-chat-btn" onClick={onNewChat} id="btn-new-chat">
        <span>+</span> New Conversation
      </button>

      <div className="sidebar-sessions">
        <div className="session-section-label">Conversations</div>
        {sessions.length === 0 ? (
          <div style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem', textAlign: 'center' }}>
            No past sessions yet.<br />Start a new conversation!
          </div>
        ) : (
          sessions.map((s) => (
            <div
              key={s.id}
              className={`session-item ${s.id === currentSessionId ? 'active' : ''}`}
              onClick={() => onSelectSession(s.id)}
            >
              <span className="session-title" title={s.title}>
                {s.title || 'Untitled Chat'}
              </span>
              <button
                className="delete-session-btn"
                title="Delete session"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(s.id);
                }}
              >
                ✕
              </button>
            </div>
          ))
        )}
      </div>

      <div className="sidebar-footer">
        <div className="knowledge-badge">
          <span>Grounding Corpus</span>
          <strong>{chunkCount || 568} Chunks</strong>
        </div>
      </div>
    </aside>
  );
}
