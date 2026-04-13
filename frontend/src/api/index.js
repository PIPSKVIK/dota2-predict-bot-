const BASE = ''

export async function searchHeroes(q) {
  const r = await fetch(`${BASE}/api/heroes/search?q=${encodeURIComponent(q)}`)
  return r.json()
}

export async function searchTeam(q) {
  const r = await fetch(`${BASE}/api/teams/search?q=${encodeURIComponent(q)}`)
  return r.json()
}

export async function transcribeAudio(blob) {
  const fd = new FormData()
  fd.append('audio', blob, 'voice.webm')
  const r = await fetch(`${BASE}/api/transcribe`, { method: 'POST', body: fd })
  return r.json()
}

export async function runPredict(body) {
  const r = await fetch(`${BASE}/api/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) {
    const err = await r.json()
    throw new Error(err.detail || 'Ошибка сервера')
  }
  return r.json()
}
