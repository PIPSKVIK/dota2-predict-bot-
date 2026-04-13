import { useState, useRef } from 'react'
import { searchHeroes } from '../api'
import { heroImg } from '../utils'
import VoiceButton from './VoiceButton'

const HeroSearch = ({ placeholder, onSelect, usedIds = [], teamColor }) => {
  const [q, setQ] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [focusedIdx, setFocusedIdx] = useState(-1)
  const timerRef = useRef(null)
  const itemsRef = useRef([])

  const search = async (val) => {
    if (!val) { setSuggestions([]); setFocusedIdx(-1); return }
    try {
      const data = await searchHeroes(val)
      setSuggestions(data.filter(h => !usedIds.includes(h.id)))
      setFocusedIdx(-1)
    } catch {}
  }

  const onChange = (e) => {
    const val = e.target.value
    setQ(val)
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => search(val), 200)
  }

  const onKeyDown = (e) => {
    if (!suggestions.length) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setFocusedIdx(i => {
        const next = Math.min(i + 1, suggestions.length - 1)
        itemsRef.current[next]?.scrollIntoView({ block: 'nearest' })
        return next
      })
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setFocusedIdx(i => {
        const next = Math.max(i - 1, 0)
        itemsRef.current[next]?.scrollIntoView({ block: 'nearest' })
        return next
      })
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const hero = focusedIdx >= 0 ? suggestions[focusedIdx] : suggestions.length === 1 ? suggestions[0] : null
      if (hero) select(hero)
    } else if (e.key === 'Escape') {
      setSuggestions([])
      setFocusedIdx(-1)
    }
  }

  const select = (hero) => {
    setQ('')
    setSuggestions([])
    setFocusedIdx(-1)
    onSelect(hero)
  }

  const onVoice = (text) => {
    setQ(text)
    search(text)
  }

  return (
    <div style={{ position: 'relative', flex: 1 }}>
      <div style={{ display: 'flex', gap: 6 }}>
        <input
          value={q}
          onChange={onChange}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          onFocus={e => e.target.style.borderColor = teamColor}
          onBlur={e => {
            e.target.style.borderColor = teamColor + '44'
            setTimeout(() => { setSuggestions([]); setFocusedIdx(-1) }, 200)
          }}
          style={{
            flex: 1,
            background: '#1e2535',
            border: `1px solid ${teamColor}44`,
            borderRadius: 8,
            padding: '10px 14px',
            color: '#e8eaf0',
            fontSize: 14,
            outline: 'none',
          }}
        />
        <VoiceButton onResult={onVoice} />
      </div>

      {suggestions.length > 0 && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
          background: '#1e2535', border: '1px solid #2a3345',
          borderRadius: 8, marginTop: 4,
          maxHeight: 320, overflowY: 'auto',
          boxShadow: '0 8px 24px rgba(0,0,0,.5)',
        }}>
          {suggestions.map((h, idx) => (
            <div
              key={h.id}
              ref={el => itemsRef.current[idx] = el}
              onMouseDown={() => select(h)}
              onMouseEnter={() => setFocusedIdx(idx)}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '8px 12px', cursor: 'pointer',
                background: focusedIdx === idx ? teamColor + '33' : 'transparent',
                borderLeft: `3px solid ${focusedIdx === idx ? teamColor : 'transparent'}`,
                transition: 'background .1s',
              }}
            >
              <img
                src={heroImg(h.name?.replace('npc_dota_hero_', ''))}
                alt={h.localized_name}
                style={{ width: 40, height: 23, borderRadius: 4, objectFit: 'cover' }}
                onError={e => { e.target.style.display = 'none' }}
              />
              <span style={{ fontSize: 14 }}>{h.localized_name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default HeroSearch
