import { useVoiceRecorder } from '../hooks/useVoiceRecorder'

const VoiceButton = ({ onResult, disabled }) => {
  const { recording, toggle } = useVoiceRecorder(onResult)

  return (
    <button
      onClick={toggle}
      disabled={disabled}
      title={recording ? 'Остановить запись' : 'Голосовой ввод'}
      style={{
        background: recording ? '#e84f4f' : '#1e2535',
        border: `1px solid ${recording ? '#e84f4f' : '#2a3345'}`,
        color: recording ? '#fff' : '#8b95a8',
        borderRadius: 8,
        padding: '8px 14px',
        fontSize: 18,
        cursor: 'pointer',
        transition: 'all .2s',
        animation: recording ? 'pulse 1s infinite' : 'none',
      }}
    >
      {recording ? '⏹' : '🎤'}
    </button>
  )
}

export default VoiceButton
