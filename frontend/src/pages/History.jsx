import { useState, useEffect } from 'react'
import { getHistory, getHistoryStats, setMatchResult } from '../api'

const History = () => {
  const [rows, setRows]   = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter]   = useState('all')  // all | pending | correct | wrong

  const load = async () => {
    setLoading(true)
    const [h, s] = await Promise.all([getHistory(), getHistoryStats()])
    setRows(h)
    setStats(s)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const markResult = async (id, winner) => {
    const updated = await setMatchResult(id, winner)
    setRows(prev => prev.map(r => r.id === id ? updated : r))
    const [s] = await Promise.all([getHistoryStats()])
    setStats(s)
  }

  const filtered = rows.filter(r => {
    if (filter === 'pending') return r.actual_winner === null
    if (filter === 'correct') return r.correct === 1
    if (filter === 'wrong')   return r.correct === 0
    return true
  })

  return (
    <div>
      <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 20 }}>📜 История предиктов</h2>

      {/* Статистика */}
      {stats && stats.total > 0 && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 10, marginBottom: 20,
        }}>
          <StatCard label="Всего" value={stats.total} color="#8b95a8" />
          <StatCard
            label="Точность"
            value={stats.accuracy_pct !== null ? `${stats.accuracy_pct}%` : '—'}
            color={stats.accuracy_pct >= 60 ? '#3dba6c' : stats.accuracy_pct >= 45 ? '#f0a500' : '#e84f4f'}
          />
          <StatCard label="Верных" value={`${stats.correct}/${stats.with_result}`} color="#3dba6c" />
        </div>
      )}

      {/* Фильтры */}
      {rows.length > 0 && (
        <div style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
          {[
            { key: 'all',     label: 'Все'       },
            { key: 'pending', label: 'Без итога' },
            { key: 'correct', label: '✅ Верные'  },
            { key: 'wrong',   label: '❌ Промахи' },
          ].map(f => (
            <button key={f.key} onClick={() => setFilter(f.key)} style={{
              padding: '6px 12px', borderRadius: 6, fontSize: 12, fontWeight: 600,
              cursor: 'pointer', border: 'none',
              background: filter === f.key ? '#4a9eff' : '#1e2535',
              color: filter === f.key ? '#fff' : '#8b95a8',
            }}>
              {f.label}
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', color: '#8b95a8', padding: 32 }}>⏳ Загрузка...</div>
      ) : filtered.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: 32, color: '#2a3345',
          border: '1px dashed #2a3345', borderRadius: 10, fontSize: 14,
        }}>
          {rows.length === 0
            ? <>Предиктов пока нет.<br /><span style={{ fontSize: 12 }}>Сделай первый расчёт — он автоматически сохранится</span></>
            : 'Нет предиктов в этой категории'
          }
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filtered.map(r => (
            <PredictCard key={r.id} row={r} onMark={markResult} />
          ))}
        </div>
      )}
    </div>
  )
}

const PredictCard = ({ row, onMark }) => {
  const [marking, setMarking] = useState(false)
  const picks1 = safeJson(row.picks_team1)
  const picks2 = safeJson(row.picks_team2)
  const date = new Date(row.created_at + 'Z').toLocaleDateString('ru', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
  })

  const handleMark = async (winner) => {
    setMarking(true)
    await onMark(row.id, winner)
    setMarking(false)
  }

  const borderColor = row.correct === 1 ? '#3dba6c'
    : row.correct === 0 ? '#e84f4f'
    : '#2a3345'

  return (
    <div style={{
      background: '#1e2535', border: `1px solid ${borderColor}`,
      borderRadius: 10, padding: 14,
    }}>
      {/* Заголовок */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>
            <span style={{ color: '#4a9eff' }}>{row.team1}</span>
            <span style={{ color: '#8b95a8', margin: '0 8px' }}>vs</span>
            <span style={{ color: '#e84f4f' }}>{row.team2}</span>
          </div>
          <div style={{ fontSize: 11, color: '#8b95a8', marginTop: 3 }}>{date}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 18, fontWeight: 800 }}>
            <span style={{ color: '#4a9eff' }}>{row.team1_pct}%</span>
            <span style={{ color: '#8b95a8', margin: '0 6px', fontSize: 14 }}>—</span>
            <span style={{ color: '#e84f4f' }}>{row.team2_pct}%</span>
          </div>
        </div>
      </div>

      {/* Пики */}
      {(picks1.length > 0 || picks2.length > 0) && (
        <div style={{ marginBottom: 10 }}>
          {picks1.length > 0 && (
            <div style={{ fontSize: 11, color: '#4a9eff88', marginBottom: 2 }}>
              {picks1.join(' · ')}
            </div>
          )}
          {picks2.length > 0 && (
            <div style={{ fontSize: 11, color: '#e84f4f88' }}>
              {picks2.join(' · ')}
            </div>
          )}
        </div>
      )}

      {/* Прогноз */}
      <div style={{ fontSize: 12, color: '#8b95a8', marginBottom: 10 }}>
        Прогноз: <span style={{ color: '#e8eaf0', fontWeight: 600 }}>{row.predicted_winner}</span>
        {row.actual_winner && (
          <> · Победил: <span style={{
            color: row.correct === 1 ? '#3dba6c' : '#e84f4f', fontWeight: 600,
          }}>{row.actual_winner}</span>
          {' '}{row.correct === 1 ? '✅' : '❌'}
          </>
        )}
      </div>

      {/* Кнопки внесения результата */}
      {!row.actual_winner && (
        <div style={{ display: 'flex', gap: 6 }}>
          <div style={{ fontSize: 11, color: '#8b95a8', alignSelf: 'center', marginRight: 4 }}>
            Кто победил?
          </div>
          {[
            { name: row.team1, color: '#4a9eff' },
            { name: row.team2, color: '#e84f4f' },
          ].map(t => (
            <button
              key={t.name}
              onClick={() => handleMark(t.name)}
              disabled={marking}
              style={{
                flex: 1, padding: '6px 8px', fontSize: 12, fontWeight: 600,
                background: t.color + '11', border: `1px solid ${t.color}44`,
                borderRadius: 6, color: t.color, cursor: 'pointer',
              }}
              onMouseEnter={e => e.currentTarget.style.background = t.color + '33'}
              onMouseLeave={e => e.currentTarget.style.background = t.color + '11'}
            >
              {t.name}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

const StatCard = ({ label, value, color }) => (
  <div style={{
    background: '#1e2535', border: '1px solid #2a3345',
    borderRadius: 10, padding: '12px 16px', textAlign: 'center',
  }}>
    <div style={{ fontSize: 22, fontWeight: 800, color }}>{value}</div>
    <div style={{ fontSize: 11, color: '#8b95a8', marginTop: 3 }}>{label}</div>
  </div>
)

const safeJson = (s) => {
  try { return JSON.parse(s) || [] }
  catch { return [] }
}

export default History
