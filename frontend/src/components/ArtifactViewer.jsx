import React, { useState } from 'react';

export default function ArtifactViewer({
  artifact,
  isOpen,
  onClose
}) {
  const [viewMode, setViewMode] = useState('preview'); // 'preview' | 'code'
  const [copied, setCopied] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  if (!isOpen || !artifact) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(artifact.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy', err);
    }
  };

  const handleDownload = () => {
    const ext = artifact.type === 'html' ? 'html' : 'md';
    const blob = new Blob([artifact.content], {
      type: artifact.type === 'html' ? 'text/html;charset=utf-8' : 'text/markdown;charset=utf-8'
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${artifact.title.replace(/\s+/g, '_').toLowerCase()}.${ext}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`artifact-pane ${isFullscreen ? 'fullscreen' : ''}`} id="artifact-viewer-pane">
      <div className="artifact-header">
        <div className="artifact-title-group">
          <span className="artifact-badge">{artifact.type}</span>
          <h3 title={artifact.title}>{artifact.title}</h3>
        </div>

        <div className="artifact-tabs">
          <button
            className={`artifact-tab-btn ${viewMode === 'preview' ? 'active' : ''}`}
            onClick={() => setViewMode('preview')}
          >
            Preview
          </button>
          <button
            className={`artifact-tab-btn ${viewMode === 'code' ? 'active' : ''}`}
            onClick={() => setViewMode('code')}
          >
            Code
          </button>
        </div>

        <div className="artifact-actions">
          <button
            className="icon-btn"
            onClick={handleCopy}
            title={copied ? 'Copied to clipboard!' : 'Copy source code'}
          >
            {copied ? '✓' : '📋'}
          </button>
          <button
            className="icon-btn"
            onClick={handleDownload}
            title="Download file"
          >
            ⬇
          </button>
          <button
            className="icon-btn"
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? '⤦' : '⤢'}
          </button>
          <button
            className="icon-btn"
            onClick={onClose}
            title="Close viewer"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="artifact-body">
        {viewMode === 'preview' ? (
          artifact.type === 'html' ? (
            <iframe
              title="Artifact Viewer"
              srcDoc={artifact.content}
              sandbox="allow-same-origin"
              className="sandboxed-iframe"
            />
          ) : (
            <div className="code-source-view" style={{ background: '#0f172a' }}>
              <pre>{artifact.content}</pre>
            </div>
          )
        ) : (
          <div className="code-source-view">
            <pre>{artifact.content}</pre>
          </div>
        )}
      </div>

      <div className="artifact-security-note">
        <span>🛡️</span>
        <div>
          <strong>Sandboxed Sandbox Isolation:</strong> Content is isolated via &lt;iframe sandbox="allow-same-origin"&gt;. Arbitrary script execution is prevented.
        </div>
      </div>
    </div>
  );
}
