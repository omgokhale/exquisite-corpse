import { useState } from 'react'
import Generator from './components/Generator'
import ResultDisplay from './components/ResultDisplay'
import LogoA from './LogoA.svg'

function App() {
  const [currentResult, setCurrentResult] = useState(null)

  const handleLogoClick = () => {
    setCurrentResult(null)
  }

  return (
    <div style={styles.app}>
      {currentResult && (
        <header style={styles.header}>
          <img
            src={LogoA}
            alt="Exquisite Corpse"
            style={styles.logo}
            onClick={handleLogoClick}
          />
        </header>
      )}

      <main style={styles.main}>
        <ResultDisplay result={currentResult} />
      </main>

      <Generator onGenerate={setCurrentResult} hasResult={!!currentResult} />
    </div>
  )
}

const styles = {
  app: {
    minHeight: '100vh',
    background: '#000000',
    fontFamily: '"Hedvig Letters Serif", serif',
  },
  header: {
    position: 'absolute',
    top: '24px',
    left: '0',
    right: '0',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 100,
    pointerEvents: 'none',
  },
  logo: {
    height: '24px',
    width: 'auto',
    cursor: 'pointer',
    pointerEvents: 'auto',
  },
  main: {
    width: '100%',
    margin: '0',
    padding: '0',
  },
}

export default App
