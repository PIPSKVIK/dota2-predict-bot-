import { useState } from 'react'

const Login = ({ onLogin }) => {
  const [login, setLogin]       = useState('admin')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const r = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ login, password }),
      })
      if (r.ok) {
        onLogin()
      } else {
        setError('Неверный логин или пароль')
      }
    } catch {
      setError('Ошибка соединения')
    }
    setLoading(false)
  }

  return (
    <div style={{
      minHeight: '100vh', background: '#0e1117',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 16,
    }}>
      <div style={{ width: '100%', maxWidth: 360 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: -1 }}>
            <span style={{ color: '#4a9eff' }}>Dota 2</span>{' '}
            <span style={{ color: '#e8eaf0' }}>Predict</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} style={{
          background: '#161b27', border: '1px solid #2a3345',
          borderRadius: 16, padding: 28,
        }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 20, textAlign: 'center' }}>
            Вход
          </h2>

          <div style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 11, color: '#8b95a8', fontWeight: 600, marginBottom: 6 }}>ЛОГИН</div>
            <input
              value={login}
              onChange={e => setLogin(e.target.value)}
              style={inputStyle}
              autoComplete="username"
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 11, color: '#8b95a8', fontWeight: 600, marginBottom: 6 }}>ПАРОЛЬ</div>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              style={inputStyle}
              autoComplete="current-password"
              autoFocus
            />
          </div>

          {error && (
            <div style={{
              background: '#e84f4f22', border: '1px solid #e84f4f44',
              borderRadius: 8, padding: '10px 14px',
              color: '#e84f4f', fontSize: 13, marginBottom: 16, textAlign: 'center',
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !password}
            style={{
              width: '100%', padding: 14, border: 'none', borderRadius: 10,
              background: password && !loading
                ? 'linear-gradient(135deg, #4a9eff, #6eb5ff)'
                : '#2a3345',
              color: password && !loading ? '#fff' : '#8b95a8',
              fontSize: 15, fontWeight: 700,
              cursor: password && !loading ? 'pointer' : 'default',
            }}
          >
            {loading ? '⏳ Вхожу...' : 'Войти'}
          </button>
        </form>
      </div>
    </div>
  )
}

const inputStyle = {
  width: '100%', background: '#1e2535',
  border: '1px solid #2a3345', borderRadius: 8,
  padding: '10px 14px', color: '#e8eaf0',
  fontSize: 14, outline: 'none',
}

export default Login
