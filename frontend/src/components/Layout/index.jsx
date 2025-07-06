import React from 'react';
import { Outlet } from 'react-router-dom';
import './Layout.css';

const Layout = () => {
  return (
    <div className="app-layout">
      <header className="app-header">
        <h1>Nova Chatbot</h1>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
      <footer className="app-footer">
        <p>© {new Date().getFullYear()} Nova Chatbot. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default Layout;
