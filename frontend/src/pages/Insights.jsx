import { useState, useEffect, useRef } from 'react'
import { getInsights, addInsight, deleteInsight } from '../api'
import VoiceButton from '../components/VoiceButton'

const EFFECT_LABELS = {
  strong: { label: 'Сильный',  color: '#3dba6c', icon: '🔥' },
  weak:   { label: 'Слабый',   color: '#e84f4f', icon: '📉' },
  combo:  { label: 'Связка',   color: '#f0a500', icon: '⚡' },
}

const Insights = () => {
  const [insights, setInsights] = useState([])
  const [text, setText]         = useState('')
  const [loading, setLoading]   = useState(false)
  const [saving, setSaving]     = useState(false)
  const inputRef = useRef(null)

  const load = async () => {
    setLoading(true)
    try {
      setInsights(await getInsights())
    } catch {}
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const handleAdd = async () => {
    const t = text.trim()
    if (!t) return
    setSaving(true)
    try {
      const saved = await addInsight(t)
      setInsights(prev => [saved, ...prev])
      setText('')
      inputRef.current?.focus()
    } catch {}
    setSaving(false)
  }

  const handleDelete = async (id) => {
    await deleteInsight(id)
    setInsights(prev => prev.filter(i => i.id !== id))
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div>
      <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>💡 Инсайды</h2>
      <p style={{ fontSize: 13, color: '#8b95a8', marginBottom: 20 }}>
        Что знаешь о текущей мете — влияет на предикт
      </p>

      {/* Поле ввода */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <input
            ref={inputRef}
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder='Например: "Лина ташит", "Морф слабый", "связка Кунка Магнус"'
            style={{
              flex: 1, background: '#1e2535',
              border: `1px solid ${text ? '#f0a500aa' : '#2a3345'}`,
              borderRadius: 8, padding: '10px 14px',
              color: '#e8eaf0', fontSize: 14, outline: 'none',
            }}
          />
          <VoiceButton onResult={t => { setText(t); setTimeout(handleAdd, 300) }} />
        </div>
        <button
          onClick={handleAdd}
          disabled={!text.trim() || saving}
          style={{
            width: '100%', padding: 12, border: 'none', borderRadius: 8,
            background: text.trim() && !saving
              ? 'linear-gradient(135deg, #f0a500, #e09000)'
              : '#2a3345',
            color: text.trim() && !saving ? '#000' : '#8b95a8',
            fontSize: 14, fontWeight: 700, cursor: text.trim() ? 'pointer' : 'default',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}
        >
          {saving
            ? <><span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⏳</span> Анализирую...</>
            : '+ Добавить инсайд'
          }
        </button>
      </div>

      {/* Список */}
      {loading ? (
        <div style={{ textAlign: 'center', color: '#8b95a8', padding: 24 }}>⏳ Загрузка...</div>
      ) : insights.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: 32,
          color: '#2a3345', fontSize: 14,
          border: '1px dashed #2a3345', borderRadius: 10,
        }}>
          Инсайдов пока нет.<br />
          <span style={{ fontSize: 12 }}>Добавь первый — он повлияет на следующий предикт</span>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {insights.map(ins => {
            const ef = EFFECT_LABELS[ins.effect] || EFFECT_LABELS.strong
            return (
              <div key={ins.id} style={{
                background: '#1e2535',
                border: `1px solid ${ef.color}33`,
                borderLeft: `3px solid ${ef.color}`,
                borderRadius: 8, padding: '12px 14px',
                display: 'flex', alignItems: 'flex-start', gap: 12,
              }}>
                <span style={{ fontSize: 20, lineHeight: 1, marginTop: 1 }}>{ef.icon}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 14, color: '#e8eaf0', marginBottom: 4 }}>
                    {ins.raw_text}
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {ins.hero && (
                      <Tag color={ef.color}>{ins.hero}</Tag>
                    )}
                    <Tag color={ef.color}>{ef.label}</Tag>
                    {ins.combo_hero && (
                      <Tag color="#f0a500">+ {ins.combo_hero}</Tag>
                    )}
                    <Tag color="#8b95a8">вес {ins.weight}x</Tag>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(ins.id)}
                  style={{
                    background: 'none', border: 'none',
                    color: '#8b95a8', fontSize: 16,
                    cursor: 'pointer', padding: '0 4px',
                    lineHeight: 1, flexShrink: 0,
                    transition: 'color .15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.color = '#e84f4f'}
                  onMouseLeave={e => e.currentTarget.style.color = '#8b95a8'}
                  title="Удалить"
                >✕</button>
              </div>
            )
          })}
        </div>
      )}

      {insights.length > 0 && (
        <div style={{ fontSize: 12, color: '#8b95a8', marginTop: 16, textAlign: 'center' }}>
          {insights.length} инсайд{insights.length === 1 ? '' : insights.length < 5 ? 'а' : 'ов'} активно влияют на предикты
        </div>
      )}
    </div>
  )
}

const Tag = ({ children, color }) => (
  <span style={{
    fontSize: 11, fontWeight: 600,
    background: color + '22', color,
    border: `1px solid ${color}44`,
    borderRadius: 4, padding: '2px 6px',
  }}>
    {children}
  </span>
)

export default Insights
