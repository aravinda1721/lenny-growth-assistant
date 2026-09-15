import React from 'react';

export default function CitationsDrawer({ citations, onClose }) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="citations-drawer" id="citations-drawer">
      <div className="drawer-header">
        <h4>
          <span>📚</span> Grounded Sources ({citations.length} Citations)
        </h4>
        <button className="icon-btn" onClick={onClose} title="Close inspector">
          ✕
        </button>
      </div>

      <div className="drawer-content">
        {citations.map((c, idx) => (
          <div key={idx} className="citation-card">
            <div className="citation-card-header">
              <div className="citation-guest">
                [{c.citation_id || idx + 1}] {c.guest} • <em>{c.episode_title}</em> ({c.timestamp})
              </div>
              {c.youtube_url && (
                <a
                  href={c.youtube_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="citation-yt-btn"
                  title="Watch segment on YouTube with exact timestamp"
                >
                  ▶ Watch ({c.timestamp})
                </a>
              )}
            </div>
            <div className="citation-quote">
              "{c.quote_snippet || c.text}"
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
