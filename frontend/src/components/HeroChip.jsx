import { useState } from 'react'
import { heroImg } from '../utils'

const HeroChip = ({ hero, onRemove, color }) => {
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      background: color + '22', border: `1px solid ${color}44`,
      borderRadius: 6, padding: '4px 8px 4px 4px', fontSize: 13,
    }}>
      <div style={{ width: 32, height: 18, borderRadius: 3, overflow: 'hidden', flexShrink: 0, position: 'relative' }}>
        {!loaded && !error && (
          <div style={{
            width: 32, height: 18,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: '#1e2535',
          }}>
            <div style={{
              width: 10, height: 10, borderRadius: '50%',
              border: `2px solid ${color}44`,
              borderTopColor: color,
              animation: 'spin 0.7s linear infinite',
            }} />
          </div>
        )}
        {!error && (
          <img
            src={heroImg(hero.name?.replace('npc_dota_hero_', ''))}
            alt={hero.localized_name}
            onLoad={() => setLoaded(true)}
            onError={() => setError(true)}
            style={{
              width: 32, height: 18, objectFit: 'cover',
              display: loaded ? 'block' : 'none',
            }}
          />
        )}
      </div>
      <span style={{ color: '#e8eaf0' }}>{hero.localized_name}</span>
      {onRemove && (
        <button
          onClick={() => onRemove(hero.id)}
          style={{
            background: 'none', border: 'none', color: '#8b95a8',
            fontSize: 12, padding: '0 2px', lineHeight: 1, cursor: 'pointer',
          }}
        >✕</button>
      )}
    </div>
  )
}

export default HeroChip
