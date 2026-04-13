export function heroImg(name) {
  if (!name) return null
  const short = name.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_')
  return `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/${short}.png`
}
