import React, { useState, useEffect, useRef } from 'react';

// Icons represent Lucide icons but used as plain elements for this demonstration
const SendIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
);

const SearchIcon = () => (
   <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
);

const App = () => {
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! I am your Mutual Fund factual assistant. How can I help you today?", sender: 'bot' }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  const funds = [
    "Kotak Large Cap",
    "HDFC Large Cap",
    "HDFC Small Cap",
    "HDFC Mid Cap",
    "ICICI Prudential Large",
    "ICICI Prudential Small",
    "ICICI Prudential Mid",
    "Kotak Midcap",
    "Kotak Small Cap"
  ];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage = { id: Date.now(), text: inputValue, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.text })
      });
      const data = await response.json();
      
      const botMessage = { 
        id: Date.now() + 1, 
        text: data.response, 
        sender: 'bot' 
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      setMessages(prev => [...prev, { id: Date.now() + 1, text: "Error connecting to server.", sender: 'bot' }]);
    } finally {
      setLoading(false);
    }
  };

  const formatMessage = (msg) => {
    if (msg.sender === 'user') return msg.text;
    
    // Check for source phrase
    const sourcePhrase = "Last updated from sources:";
    if (msg.text.includes(sourcePhrase)) {
        const parts = msg.text.split(sourcePhrase);
        const url = parts[1].trim();
        return (
            <>
                <div>{parts[0]}</div>
                <div className="citation">
                    <strong>Source:</strong> <a href={url} target="_blank" rel="noopener noreferrer">{url}</a>
                </div>
            </>
        )
    }
    return msg.text;
  };

  return (
    <div id="app-root">
      <nav className="top-nav">
        <div className="logo">Chat Bot</div>
        <div className="input-container" style={{maxWidth: '400px', width: '100%', border: 'none', background: 'rgba(255,255,255,0.05)'}}>
            <SearchIcon />
            <input type="text" className="chat-input" placeholder="Search..." />
        </div>
        <div style={{display: 'flex', gap: '20px', alignItems: 'center'}}>
            <div className="icon-btn">🔔</div>
            <div className="icon-btn">⚙️</div>
            <div style={{width: '32px', height: '32px', borderRadius: '50%', background: '#3b82f6'}}></div>
        </div>
      </nav>

      <aside className="sidebar">
        <div className="section-title">CHATS <span>+</span></div>
        <div style={{display: 'flex', gap: '10px', marginBottom: '15px'}}>
            <button style={{flex: 1, padding: '8px', borderRadius: '6px', background: '#3b82f6', border: 'none', color: 'white', fontSize: '12px'}}>DIRECT</button>
            <button style={{flex: 1, padding: '8px', borderRadius: '6px', background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '12px'}}>GROUP</button>
        </div>
        
        {funds.map((fund, idx) => (
          <div key={idx} className="fund-item">
            <div className="avatar">{fund[0]}</div>
            <div className="info">
              <span className="name">{fund}</span>
              <span className="status">Active Records</span>
            </div>
          </div>
        ))}
      </aside>

      <main className="chat-window">
        <header className="chat-header">
          <div style={{display: 'flex', gap: '15px', alignItems: 'center'}}>
            <div style={{width: '44px', height: '44px', borderRadius: '14px', background: '#3b82f6', display: 'flex', alignItems: 'center', justify: 'center', fontSize: '20px'}}>🤖</div>
            <div>
              <div style={{fontWeight: '600'}}>Factual Assistant</div>
              <div style={{fontSize: '12px', color: '#10b981'}}>Online</div>
            </div>
          </div>
          <div style={{display: 'flex', gap: '20px'}}>
            <button className="icon-btn">📞</button>
            <button className="icon-btn">📹</button>
            <button className="icon-btn">⋮</button>
          </div>
        </header>

        <section className="messages" ref={scrollRef}>
          {messages.map(msg => (
            <div key={msg.id} className={`message ${msg.sender}`}>
              <div className="avatar" style={{background: msg.sender === 'user' ? '#3b82f6' : '#1e293b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px'}}>
                {msg.sender === 'user' ? '👤' : '🤖'}
              </div>
              <div className="content">
                {formatMessage(msg)}
              </div>
            </div>
          ))}
          {loading && (
             <div className="message bot">
               <div className="content">Thinking...</div>
             </div>
          )}
        </section>

        <footer className="chat-footer">
          <div className="input-container">
            <button className="icon-btn">📎</button>
            <input 
              type="text" 
              className="chat-input" 
              placeholder="Type your question about mutual funds..." 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            />
            <button className="icon-btn">😊</button>
            <button className="send-btn" onClick={handleSend} disabled={loading}>
              <SendIcon />
            </button>
          </div>
        </footer>
      </main>

      <aside className="right-sidebar">
        <div className="section-title">NOTIFICATIONS</div>
        <div style={{fontSize: '13px', color: '#94a3b8', padding: '10px'}}>
          No new notifications.
        </div>
        <br />
        <div className="section-title">SUGGESTIONS</div>
        <div style={{fontSize: '13px', color: '#94a3b8', padding: '10px'}}>
          Ask about:
          <ul style={{marginTop: '10px', marginLeft: '15px', display: 'flex', flexDirection: 'column', gap: '10px'}}>
            <li>NAV of ICICI Prudential</li>
            <li>HDFC Small Cap Expense Ratio</li>
            <li>Min SIP for Kotak Midcap</li>
          </ul>
        </div>
      </aside>
    </div>
  );
};

export default App;
