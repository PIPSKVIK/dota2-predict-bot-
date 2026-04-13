import { useState } from 'react'
import TeamSearch from './components/TeamSearch'
import HeroSearch from './components/HeroSearch'
import HeroChip from './components/HeroChip'
import PredictResult from './components/PredictResult'
import { runPredict } from './api'

const STEPS = ['teams', 'bans', 'picks', 'odds', 'result']

const STEP_LABELS = [
  { key: 'teams', label: 'Команды' },
  { key: 'bans',  label: 'Баны'    },
  { key: 'picks', label: 'Пики'    },
  { key: 'odds',  label: 'Кэфы'   },
]

const TEAM_COLORS = { team1: '#4a9eff', team2: '#e84f4f' }

const App = () => {
  const [step, setStep]     = useState('teams')
  const [team1, setTeam1]   = useState(null)
  const [team2, setTeam2]   = useState(null)
  const [picks, setPicks]   = useState({ team1: [], team2: [] })
  const [bans, setBans]     = useState({ team1: [], team2: [] })
  const [odds, setOdds]     = useState({ team1: '', team2: '' })
  const [activeTeam, setActiveTeam] = useState('team1')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')

  const allUsedIds = [
    ...picks.team1, ...picks.team2,
    ...bans.team1,  ...bans.team2,
  ].map(h => h.id)

  const addHero = (teamKey, hero, type) => {
    if (type === 'pick') {
      setPicks(p => {
        if (p[teamKey].length >= 5 || p[teamKey].find(h => h.id === hero.id)) return p
        return { ...p, [teamKey]: [...p[teamKey], hero] }
      })
    } else {
      setBans(b => {
        if (b[teamKey].find(h => h.id === hero.id)) return b
        return { ...b, [teamKey]: [...b[teamKey], hero] }
      })
    }
  }

  const removeHero = (teamKey, heroId, type) => {
    if (type === 'pick') {
      setPicks(p => ({ ...p, [teamKey]: p[teamKey].filter(h => h.id !== heroId) }))
    } else {
      setBans(b => ({ ...b, [teamKey]: b[teamKey].filter(h => h.id !== heroId) }))
    }
  }

  const handlePredict = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await runPredict({
        team1: { id: team1.team_id, name: team1.name },
        team2: { id: team2.team_id, name: team2.name },
        picks,
        bans,
        odds: {
          team1: odds.team1 ? parseFloat(odds.team1) : null,
          team2: odds.team2 ? parseFloat(odds.team2) : null,
        },
      })
      setResult(data)
      setStep('result')
    } catch (e) {
      setError(e.message)
    }
    setLoading(false)
  }

  const reset = () => {
    setStep('teams')
    setTeam1(null); setTeam2(null)
    setPicks({ team1: [], team2: [] })
    setBans({ team1: [], team2: [] })
    setOdds({ team1: '', team2: '' })
    setActiveTeam('team1')
    setResult(null); setError('')
  }

  const teamName = (key) => key === 'team1' ? team1?.name : team2?.name

  return (
    <div style={{
      minHeight: '100vh', background: '#0e1117',
      display: 'flex', justifyContent: 'center', alignItems: 'flex-start',
      padding: '20px 16px',
    }}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }
        @keyframes spin   { to{transform:rotate(360deg)} }
      `}</style>

      <div style={{ width: '100%', maxWidth: 600 }}>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: -1 }}>
            <span style={{ color: '#4a9eff' }}>Dota 2</span>{' '}
            <span style={{ color: '#e8eaf0' }}>Predict</span>
          </div>
          <div style={{ fontSize: 13, color: '#8b95a8', marginTop: 4 }}>
            Анализ матча по пикам и истории команд
          </div>
        </div>

        {/* Progress bar */}
        {step !== 'result' && (
          <div style={{ display: 'flex', marginBottom: 28 }}>
            {STEP_LABELS.map((s, i) => {
              const idx = STEPS.indexOf(step)
              const done = idx > i
              const active = step === s.key
              return (
                <div key={s.key} style={{
                  flex: 1, textAlign: 'center',
                  fontSize: 11, fontWeight: 600, padding: '6px 4px',
                  color: active ? '#4a9eff' : done ? '#3dba6c' : '#2a3345',
                  borderBottom: `2px solid ${active ? '#4a9eff' : done ? '#3dba6c' : '#2a3345'}`,
                  transition: 'all .2s',
                }}>
                  {done ? '✓ ' : ''}{s.label}
                </div>
              )
            })}
          </div>
        )}

        {/* Card */}
        <div style={{
          background: '#161b27', border: '1px solid #2a3345',
          borderRadius: 16, padding: 24,
        }}>

          {/* ── TEAMS ── */}
          {step === 'teams' && (
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 20 }}>Выбери команды</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                <TeamSearch label="Команда 1" value={team1} onSelect={setTeam1} color="#4a9eff" />
                <TeamSearch label="Команда 2" value={team2} onSelect={setTeam2} color="#e84f4f" />
              </div>
              <Btn
                onClick={() => setStep('bans')}
                disabled={!team1 || !team2}
                style={{ marginTop: 24 }}
              >Далее →</Btn>
            </div>
          )}

          {/* ── BANS ── */}
          {step === 'bans' && (
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>
                Баны <span style={{ fontSize: 13, color: '#8b95a8', fontWeight: 400 }}>(опционально)</span>
              </h2>
              <p style={{ fontSize: 13, color: '#8b95a8', marginBottom: 20 }}>
                Выбери команду и забань героя, или пропусти
              </p>

              <TeamTabs
                teams={[
                  { key: 'team1', name: teamName('team1'), count: bans.team1.length },
                  { key: 'team2', name: teamName('team2'), count: bans.team2.length },
                ]}
                active={activeTeam}
                onChange={setActiveTeam}
                prefix="🚫"
              />

              <HeroSearch
                placeholder="Поиск героя для бана..."
                onSelect={h => addHero(activeTeam, h, 'ban')}
                usedIds={allUsedIds}
                teamColor={TEAM_COLORS[activeTeam]}
              />

              <HeroLists picks={bans} team1={team1} team2={team2} type="ban" onRemove={removeHero} />

              <NavButtons
                onBack={() => setStep('teams')}
                onNext={() => setStep('picks')}
                nextLabel={bans.team1.length + bans.team2.length > 0 ? 'Готово →' : 'Пропустить →'}
              />
            </div>
          )}

          {/* ── PICKS ── */}
          {step === 'picks' && (
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>Пики</h2>
              <p style={{ fontSize: 13, color: '#8b95a8', marginBottom: 20 }}>
                По 5 героев на каждую команду
              </p>

              <TeamTabs
                teams={[
                  { key: 'team1', name: teamName('team1'), count: picks.team1.length, max: 5 },
                  { key: 'team2', name: teamName('team2'), count: picks.team2.length, max: 5 },
                ]}
                active={activeTeam}
                onChange={setActiveTeam}
              />

              {picks[activeTeam].length < 5 && (
                <HeroSearch
                  placeholder={`Герой для ${teamName(activeTeam)}...`}
                  onSelect={h => addHero(activeTeam, h, 'pick')}
                  usedIds={allUsedIds}
                  teamColor={TEAM_COLORS[activeTeam]}
                />
              )}

              <HeroLists picks={picks} team1={team1} team2={team2} type="pick" onRemove={removeHero} />

              <NavButtons
                onBack={() => setStep('bans')}
                onNext={() => setStep('odds')}
                nextDisabled={picks.team1.length < 5 || picks.team2.length < 5}
              />
            </div>
          )}

          {/* ── ODDS ── */}
          {step === 'odds' && (
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>
                Коэффициенты <span style={{ fontSize: 13, color: '#8b95a8', fontWeight: 400 }}>(опционально)</span>
              </h2>
              <p style={{ fontSize: 13, color: '#8b95a8', marginBottom: 24 }}>
                Введи кэфы букмекера — получишь анализ ставки
              </p>

              <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
                {[
                  { key: 'team1', name: team1?.name, color: '#4a9eff' },
                  { key: 'team2', name: team2?.name, color: '#e84f4f' },
                ].map(t => (
                  <div key={t.key} style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: t.color, marginBottom: 8 }}>
                      {t.name}
                    </div>
                    <input
                      type="number" step="0.01" min="1" placeholder="1.85"
                      value={odds[t.key]}
                      onChange={e => setOdds(o => ({ ...o, [t.key]: e.target.value }))}
                      style={{
                        width: '100%', background: '#1e2535',
                        border: `1px solid ${odds[t.key] ? t.color + '88' : '#2a3345'}`,
                        borderRadius: 8, padding: '12px 14px',
                        color: '#e8eaf0', fontSize: 16, fontWeight: 700,
                        outline: 'none', textAlign: 'center',
                      }}
                    />
                  </div>
                ))}
              </div>

              {error && (
                <div style={{
                  background: '#e84f4f22', border: '1px solid #e84f4f44',
                  borderRadius: 8, padding: '10px 14px',
                  color: '#e84f4f', fontSize: 13, marginBottom: 16,
                }}>❌ {error}</div>
              )}

              <div style={{ display: 'flex', gap: 10 }}>
                <BackBtn onClick={() => setStep('picks')} />
                <button
                  onClick={handlePredict}
                  disabled={loading}
                  style={{
                    flex: 1, padding: 14, border: 'none', borderRadius: 10,
                    background: loading ? '#2a3345' : 'linear-gradient(135deg, #4a9eff, #6eb5ff)',
                    color: loading ? '#8b95a8' : '#fff',
                    fontSize: 15, fontWeight: 700, cursor: loading ? 'default' : 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  }}
                >
                  {loading
                    ? <><span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⏳</span> Анализирую...</>
                    : '📊 Рассчитать'
                  }
                </button>
              </div>
            </div>
          )}

          {/* ── RESULT ── */}
          {step === 'result' && result && (
            <PredictResult result={result} onReset={reset} />
          )}

        </div>
      </div>
    </div>
  )
}

// ── Мелкие UI-компоненты ──────────────────────────────

const Btn = ({ children, onClick, disabled, style = {} }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    style={{
      width: '100%', padding: 14, border: 'none', borderRadius: 10,
      background: disabled ? '#2a3345' : '#4a9eff',
      color: disabled ? '#8b95a8' : '#fff',
      fontSize: 15, fontWeight: 600, cursor: disabled ? 'default' : 'pointer',
      transition: 'all .2s', ...style,
    }}
  >
    {children}
  </button>
)

const BackBtn = ({ onClick }) => (
  <button
    onClick={onClick}
    style={{
      padding: '12px 20px', background: '#1e2535',
      border: '1px solid #2a3345', borderRadius: 10,
      color: '#8b95a8', fontSize: 14, cursor: 'pointer',
    }}
  >← Назад</button>
)

const NavButtons = ({ onBack, onNext, nextLabel = 'Далее →', nextDisabled = false }) => (
  <div style={{ display: 'flex', gap: 10, marginTop: 24 }}>
    <BackBtn onClick={onBack} />
    <Btn onClick={onNext} disabled={nextDisabled} style={{ flex: 1, width: 'auto' }}>
      {nextLabel}
    </Btn>
  </div>
)

const TeamTabs = ({ teams, active, onChange, prefix = '' }) => (
  <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
    {teams.map(t => {
      const color = t.key === 'team1' ? '#4a9eff' : '#e84f4f'
      const isActive = active === t.key
      const label = t.max
        ? `${t.count === t.max ? '✅ ' : ''}${t.name} (${t.count}/${t.max})`
        : `${prefix} ${t.name} (${t.count})`
      return (
        <button key={t.key} onClick={() => onChange(t.key)} style={{
          flex: 1, padding: '10px 12px',
          background: isActive ? color + '22' : '#1e2535',
          border: `1px solid ${isActive ? color : '#2a3345'}`,
          borderRadius: 8, color: isActive ? color : '#8b95a8',
          fontSize: 13, fontWeight: 600, cursor: 'pointer',
        }}>
          {label}
        </button>
      )
    })}
  </div>
)

const HeroLists = ({ picks, team1, team2, type, onRemove }) => {
  const keys = ['team1', 'team2'].filter(k => picks[k].length > 0)
  if (!keys.length) return null
  return (
    <div style={{ marginTop: 16 }}>
      {keys.map(k => (
        <div key={k} style={{ marginBottom: 10 }}>
          <div style={{
            fontSize: 11, fontWeight: 600, marginBottom: 6,
            color: k === 'team1' ? '#4a9eff' : '#e84f4f',
          }}>
            {k === 'team1' ? team1?.name : team2?.name}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {picks[k].map(h => (
              <HeroChip
                key={h.id} hero={h}
                color={k === 'team1' ? '#4a9eff' : '#e84f4f'}
                onRemove={id => onRemove(k, id, type)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export default App
