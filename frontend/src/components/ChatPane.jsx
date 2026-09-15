import React, { useState, useRef, useEffect } from 'react';

// Lightweight markdown renderer without external heavy libraries
function renderMarkdown(content) {
  if (!content) return null;
  const lines = content.split('\n');
  const elements = [];
  let inList = false;
  let listItems = [];

  const flushList = () => {
    if (inList && listItems.length > 0) {
      elements.push(<ul key={`ul-${elements.length}`}>{listItems}</ul>);
      listItems = [];
      inList = false;
    }
  };

  const parseInline = (text) => {
    // Bold **text**
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();

    if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(<h3 key={index}>{parseInline(trimmed.slice(4))}</h3>);
    } else if (trimmed.startsWith('## ')) {
      flushList();
      elements.push(<h2 key={index}>{parseInline(trimmed.slice(3))}</h2>);
    } else if (trimmed.startsWith('# ')) {
      flushList();
      elements.push(<h1 key={index}>{parseInline(trimmed.slice(2))}</h1>);
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      inList = true;
      listItems.push(<li key={`li-${index}`}>{parseInline(trimmed.slice(2))}</li>);
    } else if (/^\d+\.\s+/.test(trimmed)) {
      flushList();
      const text = trimmed.replace(/^\d+\.\s+/, '');
      elements.push(<p key={index} style={{ marginLeft: '1rem' }}>{parseInline(trimmed)}</p>);
    } else if (trimmed === '---') {
      flushList();
      elements.push(<hr key={index} style={{ margin: '1rem 0', borderColor: 'var(--border-subtle)' }} />);
    } else if (trimmed.length > 0) {
      flushList();
      elements.push(<p key={index}>{parseInline(trimmed)}</p>);
    }
  });

  flushList();
  return elements;
}

export default function ChatPane({
  messages,
  isLoading,
  onSendMessage,
  onOpenCitations,
  onSelectArtifact,
  activeArtifact
}) {
  const [inputText, setInputText] = useState('');
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!inputText.trim() || isLoading) return;
    onSendMessage(inputText);
    setInputText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const suggestions = [
    {
      tag: 'Grounded Q&A',
      title: 'What is Brian Chesky’s philosophy on founder mode vs delegation?',
      prompt: 'What is Brian Chesky’s philosophy on founder mode and product management?'
    },
    {
      tag: 'PMF Framework',
      title: 'How do high-growth companies like Superhuman measure product-market fit?',
      prompt: 'How do top companies measure product-market fit based on the transcripts?'
    },
    {
      tag: 'Ship 30 for 30',
      title: 'Write a ~1,250-word Ship 30 essay on viral growth loops vs paid acquisition',
      prompt: 'Write a Ship 30 for 30 essay on why growth tactics cannot fix a leaky retention bucket'
    },
    {
      tag: 'Artifact Gen',
      title: 'Create an interactive Product Strategy & PMF Scorecard in HTML',
      prompt: 'Create a Product-Market Fit Scorecard artifact in HTML'
    }
  ];

  return (
    <div className="chat-pane">
      <div className="messages-scroll-area" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="welcome-hero">
            <div className="hero-badge">
              <span>🎙️</span> Lenny's Podcast Knowledge Engine
            </div>
            <h2>What product or growth challenge are you tackling?</h2>
            <p>
              Ask complex questions, generate structured Ship 30 for 30 essays, or create
              production-ready artifacts—grounded strictly in 568+ transcript chunks from Lenny Rachitsky's guests.
            </p>

            <div className="suggestions-grid">
              {suggestions.map((s, idx) => (
                <div
                  key={idx}
                  className="suggestion-card"
                  onClick={() => onSendMessage(s.prompt)}
                >
                  <span className="suggestion-tag">{s.tag}</span>
                  <div className="suggestion-title">{s.title}</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, idx) => (
            <div key={m.id || idx} className={`message-row ${m.role}`}>
              <div className={`avatar ${m.role}`}>
                {m.role === 'assistant' ? '🎙️' : '👤'}
              </div>
              <div className="message-bubble">
                {renderMarkdown(m.content)}

                {m.role === 'assistant' && (
                  <div className="message-meta-box">
                    {m.citations && m.citations.length > 0 && (
                      <button
                        className="citation-chip"
                        onClick={() => onOpenCitations(m.citations)}
                        title="Inspect grounded transcript citations"
                      >
                        <span>📚</span> {m.citations.length} Verified Sources
                      </button>
                    )}

                    {activeArtifact && (
                      <button
                        className="artifact-pill-btn"
                        onClick={() => onSelectArtifact(activeArtifact)}
                        title="Open interactive artifact in viewer"
                      >
                        <span>⚡</span> View Generated Artifact: {activeArtifact.title}
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="message-row assistant">
            <div className="avatar assistant">🎙️</div>
            <div className="message-bubble">
              <div className="typing-indicator">
                <span />
                <span />
                <span />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input-area">
        <form className="input-box-wrapper" onSubmit={handleSubmit}>
          <textarea
            className="chat-input-field"
            placeholder="Ask a question or request a Ship 30 essay (Enter to send, Shift+Enter for newline)..."
            rows={1}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            id="input-chat"
          />
          <button
            type="submit"
            className="send-btn"
            disabled={!inputText.trim() || isLoading}
            id="btn-send"
            title="Send message"
          >
            ↑
          </button>
        </form>
        <div className="input-footnote">
          Answers cite Brian Chesky, Shreyas Doshi, Marty Cagan, Elena Verna, Gustaf Alstromer &amp; Lenny Rachitsky.
        </div>
      </div>
    </div>
  );
}
