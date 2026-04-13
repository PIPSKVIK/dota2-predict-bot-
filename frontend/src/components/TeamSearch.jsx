import { useState, useRef } from 'react'
import { searchTeam } from '../api'
import VoiceButton from './VoiceButton'

const TeamSearch = ({ label, value, onSelect, color }) => {
  const [q, setQ] = useState(value?.name || '')
  const [loading, setLoading] = useState(false)
  const [found, setFound] = useState(value)
  const timerRef = useRef(null)

  const doSearch = async (val) => {
    if (!val || val.length < 2) return
    setLoading(true)
    try {
      const data = await searchTeam(val)
      if (data?.team_id) {
        setFound(data)
        onSelect(data)
      } else {
        setFound(null)
        onSelect(null)
      }
    } catch {}
    setLoading(false)
  }

  const onChange = (e) => {
    const val = e.target.value
    setQ(val)
    setFound(null)
    onSelect(null)
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => doSearch(val), 600)
  }

  const onVoice = (text) => {
    setQ(text)
    doSearch(text)
  }

  return (
    <div style={{ flex: 1 }}>
      <div style={{
        fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
        letterSpacing: 1, color, marginBottom: 8,
      }}>
        {label}
      </div>

      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <input
            value={q}
            onChange={onChange}
            placeholder="Название команды..."
            style={{
              width: '100%',
              background: '#1e2535',
              border: `1px solid ${found ? color : '#2a3345'}`,
              borderRadius: 8,
              padding: '10px 36px 10px 14px',
              color: '#e8eaf0',
              fontSize: 14,
              outline: 'none',
            }}
          />
          <span style={{
            position: 'absolute', right: 12, top: '50%',
            transform: 'translateY(-50%)', fontSize: 16,
          }}>
            {loading ? '⏳' : found ? '✅' : ''}
          </span>
        </div>
        <VoiceButton onResult={onVoice} />
      </div>

      {found && (
        <div style={{
          marginTop: 6, fontSize: 12, color,
          display: 'flex', alignItems: 'center', gap: 6,
        }}>
          {found.logo_url && (
            <img
              src={found.logo_url}
              alt=""
              style={{ width: 20, height: 20, objectFit: 'contain' }}
              onError={e => { e.target.style.display = 'none' }}
            />
          )}
          {found.name} <span style={{ color: '#8b95a8' }}>#{found.team_id}</span>
        </div>
      )}
    </div>
  )
}

export default TeamSearch
