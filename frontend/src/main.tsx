import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#fff',
            color: '#26332B',
            borderRadius: '12px',
            border: '1px solid #EAF1E5',
            boxShadow: '0 4px 16px rgba(36,91,67,0.12)',
            fontFamily: 'Inter, sans-serif',
            fontSize: '14px',
          },
          success: {
            iconTheme: { primary: '#245B43', secondary: '#EAF1E5' },
          },
          error: {
            iconTheme: { primary: '#DC2626', secondary: '#FEE2E2' },
          },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
