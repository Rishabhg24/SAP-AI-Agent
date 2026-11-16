import React, { useState, useRef, useEffect } from 'react';
import { api } from '../services/api';
import type { ChatMessage, MissingFieldInfo } from '../types';
import { Send, Bot, User, Sparkles, BookOpen } from 'lucide-react';
import { VoiceInputButton } from './VoiceInputButton';

interface Props {
  workflowId?: string;
  missingFields?: MissingFieldInfo[];
  onDataUpdated?: () => void;
}

export const ChatDrawer: React.FC<Props> = ({ workflowId, missingFields = [], onDataUpdated }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Initialize with greeting or prompt for missing fields
  useEffect(() => {
    if (messages.length === 0) {
      if (missingFields.length > 0) {
        const first = missingFields[0];
        const remainingCount = missingFields.length - 1;
        const otherList =
          remainingCount > 0
            ? `\n\n*(We will also need ${remainingCount} other required field${remainingCount > 1 ? 's' : ''}: ${missingFields
              .slice(1)
              .map((m) => m.label)
              .join(', ')}).*`
            : '';
        const examplePrompt = first.example ? ` (e.g. \`${first.example}\`)` : '';
        setMessages([
          {
            id: 'init',
            role: 'assistant',
            content: `Hello! I am your SAP Master Data Assistant. I noticed your document is missing the mandatory **${first.label}**. ${first.reason}\n\nPlease provide the **${first.label}**${examplePrompt} below.${otherList}`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      } else {
        setMessages([
          {
            id: 'init',
            role: 'assistant',
            content: 'Hello! I am your SAP technical assistant. All mandatory fields are currently complete. How can I assist you with SAP Service Layer rules or documentation today?',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }
    }
  }, [missingFields.length, workflowId]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userText = inputValue.trim();
    const userMsg: ChatMessage = {
      id: String(Date.now()),
      role: 'user',
      content: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setLoading(true);

    try {
      const res = await api.sendChatMessage(userText, workflowId);
      const botMsg: ChatMessage = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: res.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: res.citations,
      };
      setMessages((prev) => [...prev, botMsg]);

      if (res.extracted_updates && Object.keys(res.extracted_updates).length > 0) {
        if (onDataUpdated) {
          onDataUpdated();
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now() + 1),
          role: 'assistant',
          content: 'Sorry, I encountered an issue processing your response. Please try again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <div style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          background: '#F5F3FF',
          border: '1px solid #DDD6FE',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <Sparkles size={18} color="#7C3AED" />
        </div>
        <div>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: '#0F172A' }}>Conversational Assistant</h3>
          <p style={{ fontSize: 11, color: '#64748B' }}>
            NVIDIA Nemotron powered master data dialogue & RAG retrieval
          </p>
        </div>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`chat-bubble ${msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant'}`}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, fontSize: 11, fontWeight: 600, color: msg.role === 'user' ? 'rgba(255,255,255,0.9)' : '#2563EB' }}>
                {msg.role === 'user' ? <User size={12} /> : <Bot size={12} />}
                <span>{msg.role === 'user' ? 'You' : 'SAP AI Assistant'}</span>
                <span style={{ marginLeft: 'auto', fontWeight: 400, color: msg.role === 'user' ? 'rgba(255,255,255,0.75)' : '#94A3B8' }}>{msg.timestamp}</span>
              </div>
              <div style={{ whiteSpace: 'pre-wrap', color: msg.role === 'user' ? '#FFFFFF' : '#0F172A', lineHeight: 1.55 }}>{msg.content}</div>

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div style={{
                  marginTop: 10,
                  paddingTop: 8,
                  borderTop: msg.role === 'user' ? '1px solid rgba(255, 255, 255, 0.2)' : '1px solid #E2E8F0',
                  fontSize: 11,
                  color: msg.role === 'user' ? 'rgba(255,255,255,0.85)' : '#475569',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 4, color: msg.role === 'user' ? '#FFFFFF' : '#2563EB', fontWeight: 600 }}>
                    <BookOpen size={12} />
                    <span>SAP Documentation Sources:</span>
                  </div>
                  {msg.citations.map((c, idx) => (
                    <div key={idx} style={{ marginTop: 2 }}>
                      • {c.document} {c.section ? `(${c.section})` : ''} {c.page ? `p. ${c.page}` : ''}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="chat-bubble chat-bubble-assistant" style={{ fontStyle: 'italic', opacity: 0.7 }}>
              Analyzing SAP rules and preparing response...
            </div>
          )}
          <div ref={chatBottomRef} />
        </div>

        <form onSubmit={handleSendMessage} className="chat-input-bar">
          <input
            type="text"
            className="form-input"
            placeholder={
              missingFields.length > 0
                ? `Provide ${missingFields[0].label} (e.g. ${missingFields[0].example || 'value'})...`
                : 'Ask a question or enter details...'
            }
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={loading}
          />
          <VoiceInputButton
            disabled={loading}
            onTranscript={(spokenText) => setInputValue(spokenText)}
            onSendDirectly={(spokenText) => {
              setInputValue(spokenText);
            }}
            showVisualizerBanner={false}
            showLanguageSelector={false}
          />
          <button type="submit" className="btn btn-primary" disabled={loading || !inputValue.trim()}>
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
};
