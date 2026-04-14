const BASE = ''
const OPTS = { credentials: 'include' }
const JSON_OPTS = { ...OPTS, headers: { 'Content-Type': 'application/json' } }

export const searchHeroes = async (q) => {
  const r = await fetch(`${BASE}/api/heroes/search?q=${encodeURIComponent(q)}`, OPTS)
  return r.json()
}

export const searchTeam = async (q) => {
  const r = await fetch(`${BASE}/api/teams/search?q=${encodeURIComponent(q)}`, OPTS)
  return r.json()
}

export const transcribeAudio = async (blob) => {
  const fd = new FormData()
  fd.append('audio', blob, 'voice.webm')
  const r = await fetch(`${BASE}/api/transcribe`, { method: 'POST', body: fd, ...OPTS })
  return r.json()
}

export const getInsights = async () => {
  const r = await fetch(`${BASE}/api/insights`, OPTS)
  return r.json()
}

export const addInsight = async (text) => {
  const r = await fetch(`${BASE}/api/insights`, {
    method: 'POST', body: JSON.stringify({ text }), ...JSON_OPTS,
  })
  return r.json()
}

export const deleteInsight = async (id) => {
  await fetch(`${BASE}/api/insights/${id}`, { method: 'DELETE', ...OPTS })
}

export const getHistory = async () => {
  const r = await fetch(`${BASE}/api/history`, OPTS)
  return r.json()
}

export const getHistoryStats = async () => {
  const r = await fetch(`${BASE}/api/history/stats`, OPTS)
  return r.json()
}

export const setMatchResult = async (predictionId, actualWinner) => {
  const r = await fetch(`${BASE}/api/history/${predictionId}/result`, {
    method: 'PATCH', body: JSON.stringify({ actual_winner: actualWinner }), ...JSON_OPTS,
  })
  return r.json()
}

export const getSchedule = async () => {
  const r = await fetch(`${BASE}/api/schedule`, OPTS)
  return r.json()
}

export const runPredict = async (body) => {
  const r = await fetch(`${BASE}/api/predict`, {
    method: 'POST', body: JSON.stringify(body), ...JSON_OPTS,
  })
  if (!r.ok) {
    const err = await r.json()
    throw new Error(err.detail || 'Ошибка сервера')
  }
  return r.json()
}
