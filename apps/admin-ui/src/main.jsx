import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'

// Feuilles de style réelles d'Open Admin (Bootstrap 5.1.3 + Font Awesome + thème open-admin),
// copiées depuis https://github.com/open-admin-org/open-admin (licence MIT).
import './vendor/open-admin/css/styles.css'
import './vendor/open-admin/css/pages/dashboard.css'
// Ajustements spécifiques au prototype LyuX, chargés après le thème d'origine.
import './styles.css'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
