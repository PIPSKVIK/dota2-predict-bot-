import { heroImg } from '../utils'

const HeroChip = ({ hero, onRemove, color }) => (
  <div style={{
    display: 'flex', alignItems: 'center', gap: 6,
    background: color + '22', border: `1px solid ${color}44`,
    borderRadius: 6, padding: '4px 8px 4px 4px', fontSize: 13,
  }}>
    <img
      src={heroImg(hero.name?.replace('npc_dota_hero_', ''))}
      alt={hero.localized_name}
      style={{ width: 32, height: 18, borderRadius: 3, objectFit: 'cover' }}
      onError={e => { e.target.style.display = 'none' }}
    />
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

export default HeroChip
