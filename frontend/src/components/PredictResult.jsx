const PredictResult = ({ result, onReset }) => {
  const { team1_pct: p1, team2_pct: p2, team1: t1, team2: t2 } = result
  const winner = p1 > p2 ? t1 : t2
  const winnerPct = Math.max(p1, p2)

  return (
    <div>
      <div style={{
        textAlign: 'center', marginBottom: 32,
        fontSize: 13, color: '#8b95a8', textTransform: 'uppercase', letterSpacing: 1,
      }}>
        Прогноз матча
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
            'H2H история': result.details.h2h,
            'Рейтинг': result.details.rating,
            'Каунтеры': result.details.counters,
            'Синергии': result.details.synergy,
            'Winrate героев': result.details.hero_wr,
            'Фит пиков': result.details.pick_fit,
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
        padding: 20, textAlign: 'center', marginBottom: 24,
      }}>
        <div style={{ fontSize: 12, color: '#8b95a8', marginBottom: 6 }}>🏆 Победитель по прогнозу</div>
        <div style={{ fontSize: 22, fontWeight: 800, color: p1 > p2 ? '#4a9eff' : '#e84f4f' }}>
          {winner}
        </div>
        <div style={{ fontSize: 14, color: '#8b95a8', marginTop: 4 }}>уверенность {winnerPct}%</div>
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

export default PredictResult
