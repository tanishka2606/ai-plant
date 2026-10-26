import React, { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { 
  Bot, 
  User, 
  Send, 
  Trash2, 
  Sparkles, 
  Leaf, 
  Droplets, 
  Sun, 
  Shovel, 
  AlertCircle, 
  HelpCircle,
  CornerDownLeft,
  RotateCcw
} from "lucide-react";
import { askAssistant } from "../services/api";
import "./Assistant.css";

function Assistant() {
  const location = useLocation();
  const initialPlant = location.state?.plantName || "";

  const [activePlant, setActivePlant] = useState(initialPlant);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: "bot",
      text: initialPlant
        ? `Hello! I'm here to help you care for your ${initialPlant}. What would you like to know about watering, sunlight, soil, fertilizers, or troubleshooting?`
        : "Hello! I'm your plant-care assistant. Ask me anything about caring for your plants, watering schedules, sunlight needs, or troubleshooting problems like yellow leaves.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    },
  ]);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend) => {
    const query = (textToSend || inputMessage).trim();
    if (!query || loading) return;

    const userMsg = {
      id: Date.now(),
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage("");
    setLoading(true);

    try {
      // Build recent conversation history for conversational continuity
      const historyPayload = messages.slice(-6).map((m) => ({
        sender: m.sender,
        text: m.text,
      }));

      const response = await askAssistant(query, activePlant, historyPayload);
      const botAnswer = response.answer || response.message || "I apologize, but I could not formulate a response right now.";

      if (response.plant_name && !activePlant) {
        setActivePlant(response.plant_name);
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: "bot",
          text: botAnswer,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        },
      ]);
    } catch (err) {
      console.error("Assistant chat error:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: "bot",
          text: "Unable to reach the PlantAI assistant. Please make sure the backend server is running.",
          isError: true,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: Date.now(),
        sender: "bot",
        text: activePlant
          ? `Chat history cleared. Still focused on ${activePlant}. Ask me any plant care question!`
          : "Chat history cleared. How can I help you with your plants today?",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  // Section 26 suggested prompts
  const suggestedPrompts = [
    { label: "How often should I water it?", icon: Droplets },
    { label: "How much sunlight does it need?", icon: Sun },
    { label: "What soil should I use?", icon: Shovel },
    { label: "Why are the leaves turning yellow?", icon: AlertCircle },
    { label: "Should I keep it indoors?", icon: Leaf },
  ];

  return (
    <div className="page-container assistant-page-container">
      {/* Header */}
      <header className="page-header" style={{ marginBottom: "28px" }}>
        <div className="page-badge">
          <Bot size={14} />
          <span>Conversational Botanical Intelligence</span>
        </div>
        <h1 className="page-title">AI Plant Assistant</h1>
        <p className="page-subtitle">
          Ask questions regarding watering, sunlight, soil, fertilizers, location, or troubleshooting yellowing leaves.
        </p>
      </header>

      {/* Main Assistant Split Layout: Sidebar + Main Chat */}
      <div className="assistant-layout-grid">
        {/* Left Sidebar per Section 24 */}
        <aside className="assistant-sidebar">
          {/* Current Plant Focus Card */}
          <div className="sidebar-card">
            <div className="sidebar-card-header">
              <Leaf size={16} className="text-emerald" />
              <h4>Current Plant Focus</h4>
            </div>
            <p className="sidebar-card-desc">Set the botanical specimen context for precise advice:</p>
            <div className="active-plant-input-wrap">
              <input
                type="text"
                className="active-plant-input"
                value={activePlant}
                placeholder="e.g. Hibiscus, Neem, Rose..."
                onChange={(e) => setActivePlant(e.target.value)}
              />
              {activePlant && (
                <button
                  className="btn-clear-plant"
                  onClick={() => setActivePlant("")}
                  title="Clear plant focus"
                >
                  ✕
                </button>
              )}
            </div>
            {activePlant && (
              <div className="plant-context-badge">
                <span className="live-dot-small"></span>
                <span>Context: {activePlant}</span>
              </div>
            )}
          </div>

          {/* Suggested Questions per Section 24 & 26 */}
          <div className="sidebar-card">
            <div className="sidebar-card-header">
              <Sparkles size={16} className="text-accent" />
              <h4>Suggested Questions</h4>
            </div>
            <div className="suggested-prompts-list">
              {suggestedPrompts.map((item, idx) => {
                const IconComp = item.icon;
                return (
                  <button
                    key={idx}
                    className="sidebar-prompt-btn"
                    onClick={() => handleSend(item.label)}
                    disabled={loading}
                  >
                    <IconComp size={15} className="prompt-icon" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Clear Chat Action */}
          <div className="sidebar-bottom-actions">
            <button
              className="btn btn-outline btn-clear-chat"
              onClick={handleClearChat}
              disabled={loading || messages.length <= 1}
            >
              <Trash2 size={15} />
              <span>Clear Conversation</span>
            </button>
          </div>
        </aside>

        {/* Right Main Chat Panel per Section 24 */}
        <main className="assistant-main-chat">
          <div className="chat-window-card">
            {/* Chat Top Banner */}
            <div className="chat-top-banner">
              <div className="chat-bot-status">
                <div className="bot-avatar-wrap">
                  <Bot size={18} />
                </div>
                <div>
                  <div className="bot-title">PlantAI Care Expert</div>
                  <div className="bot-subtitle">
                    <span className="live-dot-small"></span> Active & Connected to MySQL Knowledge
                  </div>
                </div>
              </div>

              {activePlant && (
                <div className="active-plant-pill">
                  <span>Focus: <strong>{activePlant}</strong></span>
                </div>
              )}
            </div>

            {/* Conversation Messages Container */}
            <div className="chat-messages-scroll">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`chat-message-row ${msg.sender === "user" ? "row-user" : "row-bot"}`}
                >
                  <div className={`message-avatar ${msg.sender === "user" ? "user-avatar" : "bot-avatar"}`}>
                    {msg.sender === "user" ? <User size={15} /> : <Bot size={15} />}
                  </div>
                  
                  <div className="message-content-group">
                    <div className={`message-bubble ${msg.sender === "user" ? "bubble-user" : "bubble-bot"} ${msg.isError ? "bubble-error" : ""}`}>
                      {msg.text}
                    </div>
                    <span className="message-timestamp">{msg.timestamp}</span>
                  </div>
                </div>
              ))}

              {/* Typing Indicator Animation */}
              {loading && (
                <div className="chat-message-row row-bot">
                  <div className="message-avatar bot-avatar">
                    <Bot size={15} />
                  </div>
                  <div className="message-bubble bubble-bot typing-bubble">
                    <div className="typing-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <span className="typing-text">PlantAI is thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Bar */}
            <form
              className="chat-input-wrapper"
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
            >
              <input
                type="text"
                className="chat-text-input"
                placeholder={
                  activePlant
                    ? `Ask anything about ${activePlant}...`
                    : "Ask about watering, sunlight, soil, fertilizers, or yellow leaves..."
                }
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                disabled={loading}
              />
              <button
                type="submit"
                className="btn btn-primary btn-chat-send"
                disabled={loading || !inputMessage.trim()}
                title="Send Question"
              >
                <Send size={16} />
                <span>Send</span>
              </button>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}

export default Assistant;
