import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatPane from './components/ChatPane';
import ArtifactViewer from './components/ArtifactViewer';
import CitationsDrawer from './components/CitationsDrawer';
import ProviderModal from './components/ProviderModal';

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeArtifact, setActiveArtifact] = useState(null);
  const [isArtifactPaneOpen, setIsArtifactPaneOpen] = useState(false);
  const [inspectedCitations, setInspectedCitations] = useState(null);

  // Provider config state
  const [activeProvider, setActiveProvider] = useState('simulated');
  const [activeModel, setActiveModel] = useState('offline-growth-synth-v1');
  const [providers, setProviders] = useState([]);
  const [isProviderModalOpen, setIsProviderModalOpen] = useState(false);
  const [chunkCount, setChunkCount] = useState(568);

  // Initial load
  useEffect(() => {
    fetchConfig();
    fetchSessions();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await fetch('/api/config');
      if (res.ok) {
        const data = await res.json();
        setActiveProvider(data.active_provider);
        setActiveModel(data.active_model);
        setProviders(data.available_providers || []);
      }
    } catch (err) {
      console.error('Error fetching config:', err);
    }
  };

  const fetchSessions = async () => {
    try {
      const res = await fetch('/api/sessions');
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
        if (data.length > 0 && !currentSessionId) {
          loadSession(data[0].id);
        }
      }
    } catch (err) {
      console.error('Error fetching sessions:', err);
    }
  };

  const loadSession = async (sessionId) => {
    try {
      const res = await fetch(`/api/sessions/${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        setCurrentSessionId(sessionId);
        setMessages(data.messages || []);
        if (data.artifacts && data.artifacts.length > 0) {
          const latestArt = data.artifacts[data.artifacts.length - 1];
          setActiveArtifact(latestArt);
          setIsArtifactPaneOpen(true);
        } else {
          setActiveArtifact(null);
          setIsArtifactPaneOpen(false);
        }
        setInspectedCitations(null);
      }
    } catch (err) {
      console.error(`Error loading session ${sessionId}:`, err);
    }
  };

  const handleNewChat = async () => {
    try {
      const res = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Conversation' })
      });
      if (res.ok) {
        const newSession = await res.json();
        setSessions([newSession, ...sessions]);
        setCurrentSessionId(newSession.id);
        setMessages([]);
        setActiveArtifact(null);
        setIsArtifactPaneOpen(false);
        setInspectedCitations(null);
      }
    } catch (err) {
      console.error('Error creating new session:', err);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      const res = await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
      if (res.ok) {
        const remaining = sessions.filter((s) => s.id !== sessionId);
        setSessions(remaining);
        if (sessionId === currentSessionId) {
          if (remaining.length > 0) {
            loadSession(remaining[0].id);
          } else {
            setCurrentSessionId(null);
            setMessages([]);
            setActiveArtifact(null);
            setIsArtifactPaneOpen(false);
          }
        }
      }
    } catch (err) {
      console.error(`Error deleting session ${sessionId}:`, err);
    }
  };

  const handleSendMessage = async (userText) => {
    if (!userText.trim() || isLoading) return;

    let targetSessionId = currentSessionId;
    if (!targetSessionId) {
      // Auto-create session if none active
      const createRes = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: userText.slice(0, 40) })
      });
      const newSession = await createRes.json();
      targetSessionId = newSession.id;
      setCurrentSessionId(newSession.id);
      setSessions([newSession, ...sessions]);
    }

    // Optimistic UI update
    const optimisticUserMsg = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userText,
      citations: []
    };
    setMessages((prev) => [...prev, optimisticUserMsg]);
    setIsLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: targetSessionId,
          message: userText,
          provider: activeProvider
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail?.message || 'Server error occurred');
      }

      const data = await res.json();
      setMessages((prev) => [...prev, data.message]);

      if (data.artifact) {
        setActiveArtifact(data.artifact);
        setIsArtifactPaneOpen(true);
      }

      // Refresh sessions to sync updated title
      fetchSessions();
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: `⚠️ **Error Processing Request**: ${err.message}\n\n*Tip: Try switching to the 'simulated' provider via the model button in the header.*`,
          citations: []
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSwitchProvider = async (newProviderName) => {
    try {
      const res = await fetch('/api/config/provider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: newProviderName })
      });
      if (res.ok) {
        const data = await res.json();
        setActiveProvider(data.active_provider);
        setActiveModel(data.model);
        setIsProviderModalOpen(false);
        fetchConfig();
      }
    } catch (err) {
      console.error('Error switching provider:', err);
    }
  };

  return (
    <div className="app-layout">
      {/* Sessions Navigation */}
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={loadSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        chunkCount={chunkCount}
      />

      {/* Main Content Pane */}
      <div className="main-area">
        <Header
          activeProvider={activeProvider}
          activeModel={activeModel}
          onOpenProviderModal={() => setIsProviderModalOpen(true)}
          hasActiveArtifact={Boolean(activeArtifact)}
          isArtifactPaneOpen={isArtifactPaneOpen}
          onToggleArtifactPane={() => setIsArtifactPaneOpen(!isArtifactPaneOpen)}
        />

        <div className="split-panes-wrapper">
          {/* Chat Pane */}
          <ChatPane
            messages={messages}
            isLoading={isLoading}
            onSendMessage={handleSendMessage}
            onOpenCitations={(cits) => setInspectedCitations(cits)}
            onSelectArtifact={(art) => {
              setActiveArtifact(art);
              setIsArtifactPaneOpen(true);
            }}
            activeArtifact={activeArtifact}
          />

          {/* Sandboxed Artifact Viewer Pane */}
          <ArtifactViewer
            artifact={activeArtifact}
            isOpen={isArtifactPaneOpen}
            onClose={() => setIsArtifactPaneOpen(false)}
          />
        </div>

        {/* Grounded Citations Drawer */}
        {inspectedCitations && (
          <CitationsDrawer
            citations={inspectedCitations}
            onClose={() => setInspectedCitations(null)}
          />
        )}
      </div>

      {/* Provider Switching Modal */}
      <ProviderModal
        isOpen={isProviderModalOpen}
        onClose={() => setIsProviderModalOpen(false)}
        providers={providers}
        activeProvider={activeProvider}
        onSelectProvider={handleSwitchProvider}
      />
    </div>
  );
}
