import { useState, useEffect } from 'react'
import { getSchedule } from '../api'

const Schedule = ({ onPickMatch }) => {
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getSchedule()
      if (!Array.isArray(data)) throw new Error(JSON.stringify(data))
      setMatches(data)
    } catch (e) {
      console.error('Schedule error:', e)
      setError('Не удалось загрузить расписание: ' + e.message)
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ fontSize: 16, fontWeight: 700 }}>📅 Расписание</h2>
        <button
          onClick={load}
          style={{
            background: 'none', border: '1px solid #2a3345',
            borderRadius: 6, padding: '4px 10px',
            color: '#8b95a8', fontSize: 12, cursor: 'pointer',
          }}
        >↻ Обновить</button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', color: '#8b95a8', padding: 32 }}>⏳ Загружаю...</div>
      ) : error ? (
        <div style={{ color: '#e84f4f', fontSize: 13, textAlign: 'center', padding: 24 }}>{error}</div>
      ) : matches.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: 32, color: '#2a3345',
          border: '1px dashed #2a3345', borderRadius: 10, fontSize: 14,
        }}>
          Сейчас нет запланированных матчей
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {matches.map((m, i) => (
            <MatchCard key={i} match={m} onPick={() => onPickMatch(m)} />
          ))}
        </div>
      )}

      <div style={{ fontSize: 11, color: '#4a5568', textAlign: 'center', marginTop: 16 }}>
        Данные предоставлены{' '}
        <a href="https://liquipedia.net/dota2" target="_blank" rel="noopener noreferrer"
          style={{ color: '#4a9eff', textDecoration: 'none' }}>Liquipedia</a>
        {' '}(CC-BY-SA) · обновляются каждые 5 минут
      </div>
    </div>
  )
}

const MatchCard = ({ match, onPick }) => {
  const isLive = match.live

  return (
    <div style={{
      background: '#1e2535',
      border: `1px solid ${isLive ? '#e84f4f44' : '#2a3345'}`,
      borderRadius: 10, padding: '12px 14px',
    }}>
      {/* Статус и время */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {isLive && (
            <span style={{
              background: '#e84f4f', color: '#fff',
              fontSize: 10, fontWeight: 700, padding: '2px 6px',
              borderRadius: 4, animation: 'pulse 1.5s infinite',
            }}>LIVE</span>
          )}
          <span style={{ fontSize: 11, color: '#8b95a8' }}>{match.time_str}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {match.format && (
            <span style={{
              fontSize: 11, color: '#8b95a8',
              background: '#0e1117', borderRadius: 4, padding: '2px 6px',
            }}>{match.format}</span>
          )}
        </div>
      </div>

      {/* Команды */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 6 }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: '#4a9eff', textAlign: 'right' }}>{match.team1}</span>
          {match.team1_logo && (
            <img src={match.team1_logo} alt="" onError={e => e.currentTarget.style.display='none'}
              style={{ width: 24, height: 24, objectFit: 'contain', flexShrink: 0 }} />
          )}
        </div>

        <div style={{ textAlign: 'center', minWidth: 48 }}>
          {isLive && match.score ? (
            <span style={{ fontSize: 16, fontWeight: 800, color: '#e8eaf0' }}>{match.score}</span>
          ) : (
            <span style={{ fontSize: 13, color: '#2a3345', fontWeight: 700 }}>vs</span>
          )}
        </div>

        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 6 }}>
          {match.team2_logo && (
            <img src={match.team2_logo} alt="" onError={e => e.currentTarget.style.display='none'}
              style={{ width: 24, height: 24, objectFit: 'contain', flexShrink: 0 }} />
          )}
          <span style={{ fontSize: 13, fontWeight: 700, color: '#e84f4f' }}>{match.team2}</span>
        </div>
      </div>

      {/* Турнир */}
      {match.tournament && (
        <div style={{ fontSize: 11, color: '#8b95a8', marginBottom: 10 }}>
          🏆 {match.tournament}
        </div>
      )}

      {/* Кнопка предикта */}
      <button
        onClick={onPick}
        style={{
          width: '100%', padding: '8px 0', border: 'none', borderRadius: 7,
          background: '#4a9eff22', color: '#4a9eff',
          fontSize: 12, fontWeight: 600, cursor: 'pointer',
          transition: 'background .15s',
        }}
        onMouseEnter={e => e.currentTarget.style.background = '#4a9eff33'}
        onMouseLeave={e => e.currentTarget.style.background = '#4a9eff22'}
      >
        📊 Сделать предикт →
      </button>
    </div>
  )
}

export default Schedule
