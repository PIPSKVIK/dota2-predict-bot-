import { useState } from 'react'
import { setMatchResult } from '../api'

const PredictResult = ({ result, team1, team2, loading, onReset, onRepredict }) => {
  const { team1_pct: p1, team2_pct: p2, team1: t1, team2: t2 } = result
  const winner = p1 > p2 ? t1 : t2
  const winnerPct = Math.max(p1, p2)

  const [showLivePanel, setShowLivePanel]       = useState(false)
  const [actualWinner, setActualWinner]         = useState(null)  // null | team name
  const [resultSaved, setResultSaved]           = useState(false)
  const [savingResult, setSavingResult]         = useState(false)

  const handleSaveResult = async (winner) => {
    if (!result.prediction_id || savingResult) return
    setSavingResult(true)
    await setMatchResult(result.prediction_id, winner)
    setActualWinner(winner)
    setResultSaved(true)
    setSavingResult(false)
  }
  const [kills1, setKills1]   = useState('')
  const [kills2, setKills2]   = useState('')
  const [goldTeam, setGoldTeam] = useState('team1')
  const [goldAmt, setGoldAmt]   = useState('')
  const [newOdds1, setNewOdds1] = useState('')
  const [newOdds2, setNewOdds2] = useState('')

  const handleRepredict = () => {
    const goldAdv = goldAmt
      ? (goldTeam === 'team1' ? parseInt(goldAmt) : -parseInt(goldAmt))
      : 0
    onRepredict({
      kills_team1:    parseInt(kills1) || 0,
      kills_team2:    parseInt(kills2) || 0,
      gold_advantage: goldAdv,
      odds_team1:     newOdds1 ? parseFloat(newOdds1) : null,
      odds_team2:     newOdds2 ? parseFloat(newOdds2) : null,
    })
    setShowLivePanel(false)
  }

  return (
    <div>
      <div style={{
        textAlign: 'center', marginBottom: 32,
        fontSize: 13, color: '#8b95a8', textTransform: 'uppercase', letterSpacing: 1,
      }}>
        {result.live_weight > 0
          ? `Прогноз с live-данными (вес ${Math.round(result.live_weight * 100)}%)`
          : 'Прогноз матча'
        }
      </div>

      {/* Шкала */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: '#4a9eff' }}>{t1}</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: '#4a9eff' }}>{p1}%</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: '#e84f4f' }}>{t2}</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: '#e84f4f' }}>{p2}%</div>
          </div>
        </div>
        <div style={{
          height: 12, borderRadius: 6, overflow: 'hidden',
          background: '#1e2535', position: 'relative',
        }}>
          <div style={{
            position: 'absolute', left: 0, top: 0, bottom: 0, width: `${p1}%`,
            background: 'linear-gradient(90deg, #4a9eff, #6eb5ff)',
            borderRadius: '6px 0 0 6px', transition: 'width 1s ease',
          }} />
          <div style={{
            position: 'absolute', right: 0, top: 0, bottom: 0, width: `${p2}%`,
            background: 'linear-gradient(90deg, #ff6b6b, #e84f4f)',
            borderRadius: '0 6px 6px 0',
          }} />
        </div>
      </div>

      {/* H2H */}
      {result.h2h_total > 0 && (
        <div style={{
          background: '#1e2535', border: '1px solid #2a3345',
          borderRadius: 10, padding: 16, marginBottom: 20, textAlign: 'center',
        }}>
          <div style={{ fontSize: 11, color: '#8b95a8', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
            История встреч
          </div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>
            <span style={{ color: '#4a9eff' }}>{result.team1_h2h_wins}</span>
            <span style={{ color: '#8b95a8', margin: '0 12px' }}>—</span>
            <span style={{ color: '#e84f4f' }}>{result.h2h_total - result.team1_h2h_wins}</span>
          </div>
          <div style={{ fontSize: 12, color: '#8b95a8', marginTop: 4 }}>из {result.h2h_total} матчей</div>
        </div>
      )}

      {/* Факторы */}
      {result.details && (
        <div style={{
          background: '#1e2535', border: '1px solid #2a3345',
          borderRadius: 10, padding: 16, marginBottom: 20,
        }}>
          <div style={{ fontSize: 11, color: '#8b95a8', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
            Факторы предикта
          </div>
          {Object.entries({
            'H2H история':   result.details.h2h,
            'Рейтинг':       result.details.rating,
            'Каунтеры':      result.details.counters,
            'Синергии':      result.details.synergy,
            'Winrate героев': result.details.hero_wr,
            'Фит пиков':     result.details.pick_fit,
          }).map(([label, val]) => (
            <div key={label} style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 12, color: '#8b95a8' }}>{label}</span>
                <span style={{ fontSize: 12, color: val > 0 ? '#4a9eff' : val < 0 ? '#e84f4f' : '#8b95a8' }}>
                  {val > 0 ? '+' : ''}{val}
                </span>
              </div>
              <div style={{ height: 4, background: '#0e1117', borderRadius: 2, overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${Math.abs(val) * 100}%`, maxWidth: '100%',
                  background: val > 0 ? '#4a9eff' : '#e84f4f',
                  marginLeft: val >= 0 ? '50%' : `${(1 - Math.abs(val)) * 50}%`,
                  borderRadius: 2,
                }} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Победитель */}
      <div style={{
        background: 'linear-gradient(135deg, #1e2535, #252d40)',
        border: '1px solid #3d5a80', borderRadius: 12,
        padding: 20, textAlign: 'center', marginBottom: 16,
      }}>
        <div style={{ fontSize: 12, color: '#8b95a8', marginBottom: 6 }}>🏆 Победитель по прогнозу</div>
        <div style={{ fontSize: 22, fontWeight: 800, color: p1 > p2 ? '#4a9eff' : '#e84f4f' }}>
          {winner}
        </div>
        <div style={{ fontSize: 14, color: '#8b95a8', marginTop: 4 }}>уверенность {winnerPct}%</div>
      </div>

      {/* Результат матча */}
      {result.prediction_id && !resultSaved && (
        <div style={{
          background: '#1e2535', border: '1px solid #2a3345',
          borderRadius: 10, padding: 16, marginBottom: 12,
        }}>
          <div style={{ fontSize: 12, color: '#8b95a8', marginBottom: 12, textAlign: 'center' }}>
            Матч завершился? Отметь результат
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {[
              { name: t1, color: '#4a9eff' },
              { name: t2, color: '#e84f4f' },
            ].map(t => (
              <button
                key={t.name}
                onClick={() => handleSaveResult(t.name)}
                disabled={savingResult}
                style={{
                  flex: 1, padding: '10px 8px', border: `1px solid ${t.color}44`,
                  borderRadius: 8, background: t.color + '11',
                  color: t.color, fontSize: 13, fontWeight: 600,
                  cursor: 'pointer', transition: 'all .15s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = t.color + '33'}
                onMouseLeave={e => e.currentTarget.style.background = t.color + '11'}
              >
                🏆 {t.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {resultSaved && (
        <div style={{
          background: actualWinner === winner ? '#3dba6c22' : '#e84f4f22',
          border: `1px solid ${actualWinner === winner ? '#3dba6c' : '#e84f4f'}44`,
          borderRadius: 10, padding: 14, marginBottom: 12, textAlign: 'center',
        }}>
          {actualWinner === winner
            ? <><span style={{ fontSize: 18 }}>✅</span> <span style={{ color: '#3dba6c', fontWeight: 700 }}>Предикт верный!</span> Победил {actualWinner}</>
            : <><span style={{ fontSize: 18 }}>❌</span> <span style={{ color: '#e84f4f', fontWeight: 700 }}>Промах.</span> Победил {actualWinner}</>
          }
        </div>
      )}

      {/* Live-панель */}
      <div style={{ marginBottom: 12 }}>
        <button
          onClick={() => setShowLivePanel(v => !v)}
          style={{
            width: '100%', padding: 12,
            background: showLivePanel ? '#f0a50022' : '#1e2535',
            border: `1px solid ${showLivePanel ? '#f0a500' : '#2a3345'}`,
            borderRadius: 10, color: showLivePanel ? '#f0a500' : '#8b95a8',
            fontSize: 14, fontWeight: 600, cursor: 'pointer', transition: 'all .2s',
          }}
        >
          🔴 Обновить данные матча {showLivePanel ? '▲' : '▼'}
        </button>

        {showLivePanel && (
          <div style={{
            background: '#1a1f2e', border: '1px solid #f0a50033',
            borderTop: 'none', borderRadius: '0 0 10px 10px',
            padding: 16,
          }}>
            {/* Счёт по килам */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#f0a500', marginBottom: 10, textTransform: 'uppercase', letterSpacing: 1 }}>
                Счёт по килам
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: '#4a9eff', marginBottom: 4 }}>{team1?.name}</div>
                  <input
                    type="number" min="0" placeholder="0"
                    value={kills1}
                    onChange={e => setKills1(e.target.value)}
                    style={inputStyle('#4a9eff', kills1)}
                  />
                </div>
                <div style={{ color: '#8b95a8', fontSize: 18, fontWeight: 700, paddingTop: 18 }}>—</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: '#e84f4f', marginBottom: 4 }}>{team2?.name}</div>
                  <input
                    type="number" min="0" placeholder="0"
                    value={kills2}
                    onChange={e => setKills2(e.target.value)}
                    style={inputStyle('#e84f4f', kills2)}
                  />
                </div>
              </div>
            </div>

            {/* Преимущество по голду */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#f0a500', marginBottom: 10, textTransform: 'uppercase', letterSpacing: 1 }}>
                Перевес по голду
              </div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                {[
                  { key: 'team1', name: team1?.name, color: '#4a9eff' },
                  { key: 'team2', name: team2?.name, color: '#e84f4f' },
                ].map(t => (
                  <button key={t.key} onClick={() => setGoldTeam(t.key)} style={{
                    flex: 1, padding: '8px 10px',
                    background: goldTeam === t.key ? t.color + '22' : '#1e2535',
                    border: `1px solid ${goldTeam === t.key ? t.color : '#2a3345'}`,
                    borderRadius: 8, color: goldTeam === t.key ? t.color : '#8b95a8',
                    fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  }}>
                    {t.name}
                  </button>
                ))}
              </div>
              <input
                type="number" min="0" placeholder="5000"
                value={goldAmt}
                onChange={e => setGoldAmt(e.target.value)}
                style={{ ...inputStyle('#f0a500', goldAmt), width: '100%' }}
              />
              <div style={{ fontSize: 11, color: '#8b95a8', marginTop: 4 }}>
                Примерное преимущество в голде (например: 4000, 8000...)
              </div>
            </div>

            {/* Новые кэфы */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#f0a500', marginBottom: 10, textTransform: 'uppercase', letterSpacing: 1 }}>
                Обновлённые кэфы (опц.)
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: '#4a9eff', marginBottom: 4 }}>{team1?.name}</div>
                  <input
                    type="number" step="0.01" min="1" placeholder="1.85"
                    value={newOdds1}
                    onChange={e => setNewOdds1(e.target.value)}
                    style={{ ...inputStyle('#4a9eff', newOdds1), width: '100%', textAlign: 'center' }}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: '#e84f4f', marginBottom: 4 }}>{team2?.name}</div>
                  <input
                    type="number" step="0.01" min="1" placeholder="2.10"
                    value={newOdds2}
                    onChange={e => setNewOdds2(e.target.value)}
                    style={{ ...inputStyle('#e84f4f', newOdds2), width: '100%', textAlign: 'center' }}
                  />
                </div>
              </div>
            </div>

            <button
              onClick={handleRepredict}
              disabled={loading}
              style={{
                width: '100%', padding: 12, border: 'none', borderRadius: 8,
                background: loading ? '#2a3345' : 'linear-gradient(135deg, #f0a500, #e09000)',
                color: loading ? '#8b95a8' : '#000',
                fontSize: 14, fontWeight: 700, cursor: loading ? 'default' : 'pointer',
              }}
            >
              {loading ? '⏳ Пересчитываю...' : '📊 Пересчитать'}
            </button>
          </div>
        )}
      </div>

      <button
        onClick={onReset}
        style={{
          width: '100%', padding: 14,
          background: '#1e2535', border: '1px solid #2a3345',
          borderRadius: 10, color: '#e8eaf0',
          fontSize: 15, fontWeight: 600, cursor: 'pointer',
        }}
        onMouseEnter={e => e.currentTarget.style.background = '#2a3345'}
        onMouseLeave={e => e.currentTarget.style.background = '#1e2535'}
      >
        🔄 Новый матч
      </button>
    </div>
  )
}

const inputStyle = (color, val) => ({
  width: '100%',
  background: '#0e1117',
  border: `1px solid ${val ? color + '88' : '#2a3345'}`,
  borderRadius: 8,
  padding: '10px 12px',
  color: '#e8eaf0',
  fontSize: 14, fontWeight: 600,
  outline: 'none',
})

export default PredictResult
