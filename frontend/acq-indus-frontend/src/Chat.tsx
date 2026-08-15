'use client';

import React, { useState, useRef, useEffect, type JSX } from 'react';

// Interfaces TypeScript
interface Message {
  id: number;
  sender: 'user' | 'bot';
  text: string;
  isError?: boolean;
}

interface ChatApiResponse {
  reply: string;
}

export default function Chat(): JSX.Element {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      sender: 'bot',
      text: 'Bonjour ! Posez-moi des questions sur vos capteurs, ventilateurs ou tunnels.',
    },
  ]);
  const [inputText, setInputText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll vers le bas lors de l'ajout de messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendChatMessage = async (): Promise<void> => {
    const text = inputText.trim();
    if (!text || isLoading) return;

    // 1. Ajout du message utilisateur
    const userMsg: Message = { id: Date.now(), sender: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    // 2. Appel à l'API FastAPI
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data: ChatApiResponse = await response.json();

      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, sender: 'bot', text: data.reply },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          text: 'Erreur de connexion au serveur API.',
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Helper pour formater le texte avec du Markdown simple (gras et code)
  const renderFormattedText = (text: string): JSX.Element[] => {
    const lines = text.split('\n');
    return lines.map((line: string, idx: number) => {
      const formattedLine = line
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.*?)`/g, '<code style="background:#e5e7eb; padding:2px 4px; border-radius:4px;">$1</code>');

      return (
        <span
          key={idx}
          dangerouslySetInnerHTML={{ __html: formattedLine }}
          style={{ display: 'block', minHeight: '1.2em' }}
        />
      );
    });
  };

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        width: '360px',
        height: '480px',
        background: '#ffffff',
        borderRadius: '12px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
        display: 'flex',
        flexDirection: 'column',
        fontFamily: 'sans-serif',
        overflow: 'hidden',
        zIndex: 1000,
      }}
    >
      {/* En-tête */}
      <div
        style={{
          background: '#1f2937',
          color: 'white',
          padding: '14px 16px',
          fontWeight: 'bold',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span>🤖 Assistant Topologie</span>
        <span
          style={{
            fontSize: '12px',
            background: '#10b981',
            padding: '2px 8px',
            borderRadius: '10px',
          }}
        >
          En ligne
        </span>
      </div>

      {/* Zone de messages */}
      <div
        style={{
          flex: 1,
          padding: '12px',
          overflowY: 'auto',
          background: '#f9fafb',
          fontSize: '14px',
          lineHeight: '1.4',
        }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: 'flex',
              justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              marginBottom: '8px',
            }}
          >
            <div
              style={{
                background: msg.sender === 'user' ? '#2563eb' : msg.isError ? '#fee2e2' : '#e5e7eb',
                color: msg.sender === 'user' ? 'white' : msg.isError ? '#dc2626' : '#1f2937',
                padding: '8px 12px',
                borderRadius: '8px',
                maxWidth: '85%',
              }}
            >
              {renderFormattedText(msg.text)}
            </div>
          </div>
        ))}
        {isLoading && (
          <div style={{ color: '#6b7280', fontSize: '12px', fontStyle: 'italic' }}>
            Recherche dans Neo4j...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Saisie utilisateur */}
      <div
        style={{
          display: 'flex',
          padding: '10px',
          borderTop: '1px solid #e5e7eb',
          background: 'white',
        }}
      >
        <input
          type="text"
          value={inputText}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInputText(e.target.value)}
          onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && sendChatMessage()}
          placeholder="Demander la liste des capteurs..."
          style={{
            flex: 1,
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            padding: '8px 12px',
            outline: 'none',
          }}
        />
        <button
          onClick={sendChatMessage}
          disabled={isLoading}
          style={{
            marginLeft: '8px',
            background: '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 14px',
            cursor: 'pointer',
            fontWeight: 'bold',
            opacity: isLoading ? 0.6 : 1,
          }}
        >
          Envoyer
        </button>
      </div>
    </div>
  );
}