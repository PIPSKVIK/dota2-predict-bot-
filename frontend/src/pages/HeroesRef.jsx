import { useState, useEffect } from 'react'
import { heroImg } from '../utils'

const HeroesRef = () => {
  const [heroes, setHeroes]     = useState([])
  const [copied, setCopied]     = useState(null)
  const [filter, setFilter]     = useState('')

  useEffect(() => {
    fetch('/api/heroes', { credentials: 'include' })
      .then(r => r.json())
      .then(data => setHeroes(data.sort((a, b) => a.localized_name.localeCompare(b.localized_name))))
      .catch(() => {})
  }, [])

  const copy = (hero) => {
    navigator.clipboard.writeText(hero.localized_name).then(() => {
      setCopied(hero.id)
      setTimeout(() => setCopied(null), 1200)
    })
  }

  const filtered = filter
    ? heroes.filter(h => h.localized_name.toLowerCase().includes(filter.toLowerCase()))
    : heroes

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ fontSize: 16, fontWeight: 700 }}>🦸 Герои</h2>
        <span style={{ fontSize: 11, color: '#4a5568' }}>нажми — скопируется имя</span>
      </div>

      <input
        value={filter}
        onChange={e => setFilter(e.target.value)}
        placeholder="Поиск..."
        style={{
          width: '100%', marginBottom: 16,
          background: '#1e2535', border: '1px solid #2a3345',
          borderRadius: 8, padding: '8px 12px',
          color: '#e8eaf0', fontSize: 13, outline: 'none',
        }}
      />

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(80px, 1fr))',
        gap: 6,
      }}>
        {filtered.map(hero => {
          const isCopied = copied === hero.id
          return (
            <button
              key={hero.id}
              onClick={() => copy(hero)}
              title={hero.localized_name}
              style={{
                background: isCopied ? '#3dba6c22' : '#1e2535',
                border: `1px solid ${isCopied ? '#3dba6c' : '#2a3345'}`,
                borderRadius: 8, padding: '6px 4px 4px',
                cursor: 'pointer', transition: 'all .15s',
                display: 'flex', flexDirection: 'column',
                alignItems: 'center', gap: 4,
              }}
              onMouseEnter={e => { if (!isCopied) e.currentTarget.style.borderColor = '#4a9eff44' }}
              onMouseLeave={e => { if (!isCopied) e.currentTarget.style.borderColor = '#2a3345' }}
            >
              <img
                src={heroImg(hero.name?.replace('npc_dota_hero_', ''))}
                alt={hero.localized_name}
                style={{ width: 64, height: 36, objectFit: 'cover', borderRadius: 4 }}
                onError={e => { e.currentTarget.style.display = 'none' }}
              />
              <span style={{
                fontSize: 10, color: isCopied ? '#3dba6c' : '#8b95a8',
                textAlign: 'center', lineHeight: 1.2,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                width: '100%',
              }}>
                {isCopied ? '✓ Скопировано' : hero.localized_name}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default HeroesRef
