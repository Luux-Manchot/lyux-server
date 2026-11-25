import React, { useState } from 'react'
import { Button } from '../../components.jsx'
import { Icon } from '../../icons.jsx'
import { api, setToken } from '../../api/client.js'
import './Login.css'

export default function Login({ onSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.login(username, password)
      setToken(res.access_token)
      onSuccess(res.user)
    } catch (err) {
      setError(err.message || 'Impossible de se connecter au serveur LyuX.')
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = () => {
    setUsername('lyux-admin')
    setPassword('LyuxAdmin2026!')
    setError('')
  }

  return (
    <div className="login-shell">
      <form className="login-box" onSubmit={handleSubmit}>
        <div className="login-head">
          <div className="login-brand">
            <div className="login-brand-mark">LX</div>
            <div>
              <h1>LyuX Administration</h1>
              <p>Console de gestion d’établissement</p>
            </div>
          </div>
        </div>

        <div className="login-body">
          {error && (
            <div className="login-error" role="alert">
              <Icon name="alert" size={14} />
              <span>{error}</span>
            </div>
          )}

          <div className="form-stack">
            <label className="form-field">
              <span className="form-label">Identifiant</span>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="ex. lyux-admin"
                autoComplete="username"
                required
              />
            </label>

            <label className="form-field">
              <span className="form-label">Mot de passe</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Mot de passe"
                autoComplete="current-password"
                required
              />
            </label>

            <Button
              type="submit"
              variant="primary"
              className="full-width"
              disabled={loading}
              icon="lock"
            >
              {loading ? 'Connexion en cours…' : 'Se connecter'}
            </Button>
          </div>
        </div>

        <div className="login-footer">
          <span>Serveur : api.lyux.lan</span>
          <button type="button" className="login-demo-btn" onClick={fillDemo}>
            Remplir compte labo
          </button>
        </div>
      </form>
    </div>
  )
}
