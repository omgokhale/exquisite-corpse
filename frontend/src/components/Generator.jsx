import { useState } from 'react'
import { generateComposite } from '../api/client'

export default function Generator({ onGenerate, hasResult }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)

    try {
      const result = await generateComposite()
      onGenerate(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.container}>
      <button
        onClick={handleGenerate}
        disabled={loading}
        style={{
          ...styles.button,
          ...(loading ? styles.buttonDisabled : {}),
        }}
      >
        {hasResult ? 'Shuffle' : 'Create'}
      </button>

      {error && <div style={styles.error}>{error}</div>}
    </div>
  )
}

const styles = {
  container: {
    position: 'fixed',
    bottom: '24px',
    left: '50%',
    transform: 'translateX(-50%)',
    textAlign: 'center',
    zIndex: 1000,
  },
  button: {
    padding: '0 40px',
    height: '40px',
    fontSize: '13px',
    fontWeight: 'bold',
    fontFamily: '"Hedvig Letters Serif", serif',
    background: 'rgba(255, 255, 255, 0.9)',
    color: '#000000',
    border: 'none',
    borderRadius: '20px',
    cursor: 'pointer',
    transition: 'background 0.2s',
    backdropFilter: 'blur(30px)',
    WebkitBackdropFilter: 'blur(30px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonDisabled: {
    background: '#666666',
    color: '#cccccc',
    cursor: 'not-allowed',
  },
  error: {
    marginTop: '15px',
    padding: '10px',
    background: '#3a1a1a',
    color: '#ff6b6b',
    borderRadius: '4px',
    border: '1px solid #5a2a2a',
    fontFamily: '"Hedvig Letters Serif", serif',
  },
}
