import React, { useState, useEffect, useRef } from 'react';
import ChatInterface from '../../components/Chat/ChatInterface/ChatInterface';
import SessionPanel from '../../components/Panel/SessionPanel/SessionPanel';
import ManagePanel from '../../components/Panel/ManagePanel/ManagePanel';
import Header from '../../components/common/Header/Header';
import { v4 as uuidv4 } from 'uuid';
import api from '../../services/api';
import { useNavigate } from 'react-router-dom';
import './Home.scss';
import authService from '../../services/auth';
import Welcome from '../../components/Welcome/Welcome';
import chatService from '../../services/chat';
import WelcomeGuideModal from '../../components/common/WelcomeGuideModal/WelcomeGuideModal';

function Home() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [isPanelCollapsed, setIsPanelCollapsed] = useState(false);
  const [isManagePanelOpen, setIsManagePanelOpen] = useState(true);
  const [isManagePanelCollapsed, setIsManagePanelCollapsed] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedSources, setSelectedSources] = useState([]);

  // Add loading state for sessions
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);

  // Add ref to track initial load
  const initialLoadComplete = useRef(false);

  // Add state to control welcome screen visibility
  const [showWelcome, setShowWelcome] = useState(true);

  // Add new state for current session messages
  const [currentSessionMessages, setCurrentSessionMessages] = useState([]);
  const [progressMessage, setProgressMessage] = useState("");
  const [isThinking, setIsThinking] = useState(false);

  // Add new state
  const [showWelcomeGuide, setShowWelcomeGuide] = useState(false);

  useEffect(() => {
    // Only load sessions once
    if (!initialLoadComplete.current) {
      loadSessions();
      initialLoadComplete.current = true;
      // Always show welcome screen on initial load and clear any active session
      setShowWelcome(true);
      setActiveSessionId(null);
      setCurrentSessionMessages([]);
    }
  }, []); // Empty dependency array

  const loadSessions = async () => {
    if (isLoadingSessions) return;

    setIsLoadingSessions(true);
    try {
      const sessions = await chatService.loadSessions();
      setSessions(sessions);
      // Remove the automatic session selection
      // Keep only the sessions loading
    } catch (error) {
      console.error('Error loading sessions:', error);
    } finally {
      setIsLoadingSessions(false);
    }
  };

  const createNewSession = () => {
    // Check if there's already an empty session
    const emptySession = sessions.find(session => !session.preview && !session.topic);
    
    if (emptySession) {
      // If there's an empty session, just switch to it
      setActiveSessionId(emptySession.id);
      setCurrentSessionMessages([]); // Clear chat history
      setSelectedSources(emptySession.dataSourceIds || []);
      setShowWelcome(false);
      setShowWelcomeGuide(true);
      return;
    }

    // If no empty session exists, create a new one
    const newSession = chatService.createSession();
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    setCurrentSessionMessages([]); // Clear chat history
    setSelectedSources([]);
    setShowWelcome(false);
    setShowWelcomeGuide(true);
  };

  const reformMessages = (messages) => {
    const reformattedMessages = [];
    let currentUserMessage = null;
    let currentAssistantMessages = [];

    messages.forEach(message => {
      if (message.role === 'user') {
        // If there's a current user message, push it to the reformatted array
        if (currentUserMessage) {
          reformattedMessages.push(currentUserMessage);
        }
        // Push the current assistant messages if they exist
        if (currentAssistantMessages.length > 0) {
          reformattedMessages.push({
            role: 'assistant',
            agents: currentAssistantMessages
          });
          currentAssistantMessages = []; // Reset for the next user message
        }
        // Create a new user message
        currentUserMessage = { ...message, agents: [] }; // Initialize agents array
      } else if (message.role.match(/agent/)) {
        // If it's an agent message, add it to the current assistant messages array
        currentAssistantMessages.push(message);
      }
    });

    // Push the last user message if it exists
    if (currentUserMessage) {
      reformattedMessages.push(currentUserMessage);
    }

    // Push any remaining assistant messages if they exist
    if (currentAssistantMessages.length > 0) {
      reformattedMessages.push({
        role: 'assistant',
        agents: currentAssistantMessages
      });
    }
    return reformattedMessages;
  };

  const handleSelectSession = async (sessionId) => {
    setActiveSessionId(sessionId);

    // Only proceed if we have a valid sessionId
    if (sessionId) {
      try {
        const response = await chatService.getSession(sessionId);
        
        // Extract source IDs from the response and update selected sources
        const sourceIds = response.data.source_ids || [];
        setSelectedSources(sourceIds);

        // Update the session's data sources in the sessions state
        setSessions(prevSessions =>
          prevSessions.map(session =>
            session.id === sessionId
              ? { ...session, dataSourceIds: sourceIds }
              : session
          )
        );

        // Format and set messages
        const reformattedMessages = reformMessages(response.data.doc.messages);
        setCurrentSessionMessages(reformattedMessages);
      } catch (error) {
        console.error('Error loading session messages:', error);
      }

      // Hide welcome screen when a session is selected
      setShowWelcome(false);
    } else {
      // Clear messages when no session is selected
      setCurrentSessionMessages([]);
      setSelectedSources([]);
    }
  };

  const handleSendMessage = async (message, selectedSources, enableSOP, imageUrl) => {
    const userMessage = {
      role: 'user',
      markdowns: [message],
      message_id: uuidv4(),
      timestamp: new Date().toISOString(),
      is_error: false,
      error_message: "",
      jsons: [],
      thought_process: [],
      conversation_id: activeSessionId
    };

    const assistantMessage = {
      role: 'assistant',
      agents: [],
      message_id: uuidv4(),
      timestamp: new Date().toISOString(),
      conversation_id: activeSessionId
    };

    setIsLoading(true);

    // Add user message to UI immediately
    setCurrentSessionMessages(prev => [...prev, userMessage]);

    try {
      // Pass enableSOP to the chat service
      await chatService.sendMessage(
        message,
        imageUrl,
        activeSessionId,
        currentSessionMessages,
        selectedSources,
        enableSOP
      ).then((response) => {
        console.log(response);

        // Update activeSessionId and session if it's a new session
        if (activeSessionId === -1) {
          const newSessionId = response.conversation_id;
          setActiveSessionId(newSessionId);
          
          // Update sessions with the new ID and preview
          setSessions(prevSessions => {
            return prevSessions.map(session => {
              if (session.id === -1) {
                return {
                  ...session,
                  id: newSessionId,
                  topic: message // Set the preview to the first message
                };
              }
              return session;
            });
          });
        }

        // Create EventSource 
        const eventSource = new EventSource(`${import.meta.env.VITE_API_BASE_URL}/api/conversations/${response.chat_id}/luna2chat-sse`);
        
        // Handle incoming messages
        var messageInitialized = false;
        eventSource.onmessage = (event) => {
          setIsLoading(false);
          setIsThinking(true);

          const data = JSON.parse(event.data);
          console.log(data);

          if (data.content_type === "data" || data.content_type === "markdown" || data.content_type === "plot" || data.content_type === "error") {
            let agentResult = {
              role: data.role,
              markdowns: [],
              message_id: uuidv4(),
              timestamp: new Date().toISOString(),
              is_error: data.content_type === "error",
              error_message: data.content_type === "error" ? data.content : "",
              jsons: [],
              thought_process: [],
              conversation_id: activeSessionId
            };

            if (data.role === "sql-agent" && data.content.length > 0) {
              agentResult.jsons = data.content;
              agentResult.thought_process = data.thought_process;
              if (data.status === "failed") {
                agentResult.is_error = true;
                agentResult.markdowns.push(data.content);
              }
            } else if (data.role === "chat-agent") {
              agentResult.markdowns.push(data.content);
            } else if (data.role === "plot-agent" || data.role === "plotly-agent" || (data.role === "agent" && data.content_type === "plot")) {
              agentResult.role = "plotly-agent";
              agentResult.thought_process = data.content;
            } else if (data.role === "python-data-agent" && data.content.length > 0) {
              agentResult.jsons = data.content;
              agentResult.thought_process = data.thought_process;
            }
            assistantMessage.agents.push(agentResult);
          } else if (data.content_type === "signal" && data.content === "DONE") {
            setIsThinking(false);
            eventSource.close();
            setProgressMessage("");
            return;
          } else {
            setProgressMessage(typeof data.content === 'string' ? data.content : Array.isArray(data.content) && data.content.length > 0 ? data.content[0].instruction : null);
          }

          if (!messageInitialized) {
            setCurrentSessionMessages(prev => [...prev, assistantMessage]);
            messageInitialized = true;
          } else {
            // console.log("Updating assistant message");
            // console.log(assistantMessage);
            setCurrentSessionMessages(prev => [...prev.slice(0, -1), assistantMessage]);
          }


          // Only update preview if this is the first message in the session
          if (currentSessionMessages.length === 0) {
            setSessions(prevSessions =>
              prevSessions.map(session =>
                session.id === activeSessionId
                  ? {
                    ...session,
                    preview: message // Use the user's message as preview
                  }
                  : session
              )
            );
          }
        };

        // Handle errors
        eventSource.onerror = (error) => {
          console.error('SSE Error:', error);
          eventSource.close();
          setIsLoading(false);
          setIsThinking(false);
        };
      });
    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
      setIsThinking(false);
    }
  };

  const handleManageClick = () => {
    if (isManagePanelCollapsed) {
      setIsManagePanelCollapsed(false);
    } else {
      setIsManagePanelCollapsed(true);
    }
  };

  const handleCloseManagePanel = () => {
    setIsManagePanelOpen(false);
    setIsManagePanelCollapsed(true);
  };

  const handleToggleManagePanel = () => {
    setIsManagePanelCollapsed(prev => !prev);
  };

  const handleLogout = () => {
    authService.logout();
    navigate('/login', { replace: true });
  };

  const handleUpdateSources = (newSources) => {
    // If newSources contains objects, extract IDs, otherwise assume it's already IDs
    const sourceIds = Array.isArray(newSources)
      ? newSources.map(source => typeof source === 'object' ? source.id : source)
      : newSources;

    setSelectedSources(sourceIds);

    // Update the session's selected sources
    setSessions(prevSessions =>
      prevSessions.map(session =>
        session.id === activeSessionId
          ? { ...session, dataSourceIds: sourceIds }
          : session
      )
    );
  };

  const deleteSession = async (sessionId) => {
    try {
      // Try to get messages for this session to check if it exists in backend
      try {
        const response = await chatService.getSession(sessionId);
        // If we get messages, delete the session from backend
        if (response.data) {
          await chatService.deleteSession(sessionId);
        }
      } catch (error) {
        // If we get a 404, the session doesn't exist in backend
        // If we get any other error, we should probably still try to delete
        if (error.response?.status !== 404) {
          await chatService.deleteSession(sessionId);
        }
      }

      // If the deleted session was active, find the next session to switch to
      if (sessionId === activeSessionId) {
        // Find index of current session
        const currentIndex = sessions.findIndex(session => session.id === sessionId);
        const remainingSessions = sessions.filter(session => session.id !== sessionId);

        if (remainingSessions.length > 0) {
          // If there was a previous session, switch to it, otherwise take the next one
          const nextSession = remainingSessions[currentIndex > 0 ? currentIndex - 1 : 0];
          // Switch to the next session before removing the current one
          await handleSelectSession(nextSession.id);
        } else {
          setActiveSessionId(null);
          setCurrentSessionMessages([]);
          setShowWelcome(true);
        }
      }

      // Remove session from state
      setSessions(prevSessions => prevSessions.filter(session => session.id !== sessionId));

    } catch (error) {
      console.error('Error deleting session:', error);
      // You might want to add some user notification here
    }
  };

  return (
    <div className={`app-container ${isPanelCollapsed ? 'panel-collapsed' : ''}`}>
      <Header />

      <SessionPanel
        sessions={sessions}
        activeSessionId={activeSessionId}
        onNewSession={createNewSession}
        onSelectSession={handleSelectSession}
        onDeleteSession={deleteSession}
        isCollapsed={isPanelCollapsed}
        onToggleCollapse={() => setIsPanelCollapsed(prev => !prev)}
      />

      <div className={`chat-container ${isPanelCollapsed ? 'expanded' : ''}`}>
        <div className="chat-content">
          {showWelcome ? (
            <Welcome />
          ) : (
            activeSessionId && sessions.find(session => session.id === activeSessionId) && (
              <ChatInterface
                messages={currentSessionMessages}
                isLoading={isLoading}
                onSendMessage={(message, selectedSources, enableSOP) => handleSendMessage(message, selectedSources, enableSOP, null)}
                onManageClick={handleManageClick}
                selectedSources={selectedSources}
                progressMessage={progressMessage}
                isThinking={isThinking}
              />
            )
          )}
        </div>
      </div>

      {/* Only show ManagePanel when not in welcome screen */}
      {!showWelcome && (
        <ManagePanel
          isCollapsed={isManagePanelCollapsed}
          onToggleCollapse={handleManageClick}
          onClose={handleCloseManagePanel}
          selectedSources={selectedSources}
          onUpdateSources={handleUpdateSources}
        />
      )}

      <WelcomeGuideModal
        isOpen={showWelcomeGuide}
        onClose={() => setShowWelcomeGuide(false)}
        onManageClick={handleManageClick}
      />
    </div>
  );
}

export default Home; 