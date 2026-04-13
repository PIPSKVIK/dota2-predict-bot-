import { useState, useRef } from 'react'
import { transcribeAudio } from '../api'

export function useVoiceRecorder(onResult) {
  const [recording, setRecording] = useState(false)
  const recorderRef = useRef(null)
  const chunksRef = useRef([])

  async function toggle() {
    if (recording) {
      recorderRef.current?.stop()
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []
      recorder.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        setRecording(false)
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        try {
          const data = await transcribeAudio(blob)
          if (data.text) onResult(data.text)
        } catch {}
      }
      recorderRef.current = recorder
      recorder.start()
      setRecording(true)
    } catch {
      alert('Нет доступа к микрофону')
    }
  }

  return { recording, toggle }
}
