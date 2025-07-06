import React from 'react';
import './Home.css';

const Home = () => {
  return (
    <div className="home-container">
      <div className="welcome-message">
        <h2>Welcome to Nova Chatbot</h2>
        <p>Your intelligent AI assistant for seamless conversations.</p>
      </div>
      <div className="features">
        <div className="feature-card">
          <h3>Smart Conversations</h3>
          <p>Engage in natural, human-like conversations with our advanced AI.</p>
        </div>
        <div className="feature-card">
          <h3>Topic Analysis</h3>
          <p>Intelligent topic tracking for better context and responses.</p>
        </div>
        <div className="feature-card">
          <h3>Fast & Reliable</h3>
          <p>Powered by state-of-the-art language models for quick responses.</p>
        </div>
      </div>
    </div>
  );
};

export default Home;
