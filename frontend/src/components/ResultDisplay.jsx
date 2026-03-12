import { useState, useRef, useEffect } from 'react'
import SourceCredits from './SourceCredits'
import FullIcon from '../full.svg'
import DownloadIcon from '../download.svg'
import BookIcon from '../book.svg'
import LogoB from '../LogoB.svg'
import Backdrop from '../Backdrop.png'

export default function ResultDisplay({ result }) {
  const [showSources, setShowSources] = useState(false)
  const [scale, setScale] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [parallaxOffset, setParallaxOffset] = useState({ x: 0, y: 0 })
  const imageRef = useRef(null)
  const containerRef = useRef(null)
  const previousResultRef = useRef(null)

  useEffect(() => {
    // Handle image transition when result changes
    if (result && result !== previousResultRef.current) {
      setIsTransitioning(true)

      // Reset zoom
      setScale(1)
      setPosition({ x: 0, y: 0 })

      // Clear transition after animation completes
      const timer = setTimeout(() => {
        setIsTransitioning(false)
        previousResultRef.current = result
      }, 600) // Match animation duration

      return () => clearTimeout(timer)
    }
  }, [result])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    let animationFrameId = null

    const handleWheel = (e) => {
      // Check if event is from sources modal - if so, let it scroll normally
      const sourcesModal = document.querySelector('[data-sources-modal]')
      if (sourcesModal && sourcesModal.contains(e.target)) {
        return // Let the modal handle its own scrolling
      }

      // Always capture wheel events in the container for zoom
      if (e.metaKey || e.ctrlKey || e.deltaY !== 0) {
        e.preventDefault()
        e.stopPropagation()

        // Cancel any pending animation frame
        if (animationFrameId) {
          cancelAnimationFrame(animationFrameId)
        }

        // Use requestAnimationFrame for smoother updates
        animationFrameId = requestAnimationFrame(() => {
          const delta = -e.deltaY
          // Much smaller increments for smoother zoom
          const scaleChange = delta > 0 ? 1.02 : 0.98
          const newScale = Math.min(Math.max(0.5, scale * scaleChange), 5)

          setScale(newScale)
        })
      }
    }

    const handleGesture = (e) => {
      e.preventDefault()
      e.stopPropagation()
    }

    const handleMouseDown = (e) => {
      if (scale > 1) {
        setIsDragging(true)
        setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y })
        e.preventDefault()
      }
    }

    const handleMouseMove = (e) => {
      if (isDragging && scale > 1) {
        requestAnimationFrame(() => {
          setPosition({
            x: e.clientX - dragStart.x,
            y: e.clientY - dragStart.y
          })
        })
      }
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    container.addEventListener('wheel', handleWheel, { passive: false })
    container.addEventListener('gesturestart', handleGesture, { passive: false })
    container.addEventListener('gesturechange', handleGesture, { passive: false })
    container.addEventListener('gestureend', handleGesture, { passive: false })
    container.addEventListener('mousedown', handleMouseDown)
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId)
      }
      container.removeEventListener('wheel', handleWheel)
      container.removeEventListener('gesturestart', handleGesture)
      container.removeEventListener('gesturechange', handleGesture)
      container.removeEventListener('gestureend', handleGesture)
      container.removeEventListener('mousedown', handleMouseDown)
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [scale, isDragging, dragStart, position])

  const handleMouseMove = (e) => {
    if (!result) {
      const { clientX, clientY, currentTarget } = e
      const { width, height } = currentTarget.getBoundingClientRect()

      // Calculate offset as percentage from center (-1 to 1)
      const xPercent = (clientX / width - 0.5) * 2
      const yPercent = (clientY / height - 0.5) * 2

      // Apply parallax movement (max 20px in each direction)
      setParallaxOffset({
        x: xPercent * 20,
        y: yPercent * 20
      })
    }
  }

  const handleMouseLeave = () => {
    if (!result) {
      setParallaxOffset({ x: 0, y: 0 })
    }
  }

  if (!result) {
    return (
      <div
        style={styles.homescreen}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <div
          style={{
            ...styles.homescreenBackdrop,
            transform: `translate(${parallaxOffset.x}px, ${parallaxOffset.y}px) scale(1.1)`,
          }}
        />
        <div style={styles.homescreenContent}>
          <img src={LogoB} alt="Exquisite Corpse" style={styles.homescreenLogo} />
        </div>
      </div>
    )
  }

  const handleResetZoom = () => {
    if (scale === 1 && position.x === 0 && position.y === 0) return

    // Animate back to default
    const startScale = scale
    const startPosition = { ...position }
    const duration = 400 // ms
    const startTime = performance.now()

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)

      // Ease out cubic for smooth deceleration
      const easeProgress = 1 - Math.pow(1 - progress, 3)

      const newScale = startScale + (1 - startScale) * easeProgress
      const newPosition = {
        x: startPosition.x * (1 - easeProgress),
        y: startPosition.y * (1 - easeProgress)
      }

      setScale(newScale)
      setPosition(newPosition)

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }

  const toggleSources = () => {
    setShowSources(!showSources)
  }

  const handleDownload = async () => {
    if (!result) return

    try {
      // Fetch the image
      const response = await fetch(result.image_url)
      const blob = await response.blob()

      // Create a download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `exquisite-corpse-${result.id}.png`
      document.body.appendChild(link)
      link.click()

      // Clean up
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  return (
    <div style={styles.container}>
      <div
        ref={containerRef}
        style={{
          ...styles.imageContainer,
          cursor: scale > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default',
        }}
      >
        <div style={styles.imageWrapper}>
          <img
            ref={imageRef}
            src={result.image_url}
            alt="Generated composite"
            style={{
              ...styles.image,
              transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
              transformOrigin: 'center center',
              filter: isTransitioning ? 'blur(0px)' : 'blur(0px)',
              animation: isTransitioning ? 'blurIn 0.6s ease-out' : 'none',
            }}
            draggable={false}
          />
        </div>

        <button
          onClick={toggleSources}
          style={styles.sourcesButton}
          aria-label="View sources"
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(90, 90, 90, 0.48)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(63, 63, 63, 0.38)'
          }}
        >
          <img src={BookIcon} alt="Sources" style={{ width: '18px', height: '18px' }} />
        </button>

        <button
          onClick={handleResetZoom}
          disabled={scale === 1 && position.x === 0 && position.y === 0}
          style={{
            ...styles.resetButton,
            opacity: scale === 1 && position.x === 0 && position.y === 0 ? 0.3 : 1,
            cursor: scale === 1 && position.x === 0 && position.y === 0 ? 'default' : 'pointer',
          }}
          aria-label="Reset zoom"
          onMouseEnter={(e) => {
            if (!(scale === 1 && position.x === 0 && position.y === 0)) {
              e.currentTarget.style.background = 'rgba(90, 90, 90, 0.48)'
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(63, 63, 63, 0.38)'
          }}
        >
          <img src={FullIcon} alt="Reset view" style={{ width: '18px', height: '18px' }} />
        </button>

        <button
          onClick={handleDownload}
          style={styles.downloadButton}
          aria-label="Download image"
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(90, 90, 90, 0.48)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(63, 63, 63, 0.38)'
          }}
        >
          <img src={DownloadIcon} alt="Download" style={{ width: '18px', height: '18px', filter: 'invert(1)' }} />
        </button>

        {showSources && (
          <>
            <div style={styles.modalOverlay} onClick={toggleSources} />
            <div style={styles.sourcesModal} data-sources-modal="true">
              <SourceCredits sources={result.sources} />
            </div>
          </>
        )}
      </div>
    </div>
  )
}

const styles = {
  container: {
    width: '100%',
    margin: '0',
    padding: '0',
  },
  homescreen: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    width: '100vw',
    backgroundColor: '#000000',
    overflow: 'hidden',
    position: 'relative',
  },
  homescreenBackdrop: {
    position: 'absolute',
    top: '-5%',
    left: '-5%',
    width: '110%',
    height: '110%',
    background: `url(${Backdrop}) center center / cover no-repeat`,
    transition: 'transform 0.3s ease-out',
    zIndex: 0,
  },
  homescreenContent: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '0',
    marginBottom: '40px', // Half of button height to center the group
    position: 'relative',
    zIndex: 1,
  },
  homescreenLogo: {
    width: '660px',
    height: 'auto',
    marginBottom: '60px',
  },
  imageContainer: {
    background: '#000000',
    padding: '0',
    margin: '0',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    width: '100vw',
    overflow: 'hidden',
    position: 'relative',
    touchAction: 'none',
  },
  imageWrapper: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    width: '100%',
    height: '100%',
  },
  image: {
    maxWidth: '95%',
    maxHeight: 'calc(100vh - 160px)',
    width: 'auto',
    height: 'auto',
    display: 'block',
    borderRadius: '4px',
    boxShadow: '0 4px 12px rgba(255,255,255,0.1)',
    objectFit: 'contain',
    pointerEvents: 'none',
    willChange: 'transform',
  },
  resetButton: {
    position: 'absolute',
    bottom: '24px',
    left: '80px',
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    background: 'rgba(63, 63, 63, 0.38)',
    color: 'white',
    border: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backdropFilter: 'blur(30px)',
    WebkitBackdropFilter: 'blur(30px)',
    zIndex: 10,
    pointerEvents: 'auto',
    transition: 'opacity 0.5s ease, background 0.3s ease',
    fontFamily: '"Hedvig Letters Serif", serif',
  },
  sourcesButton: {
    position: 'absolute',
    bottom: '24px',
    left: '24px',
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    background: 'rgba(63, 63, 63, 0.38)',
    color: 'white',
    border: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backdropFilter: 'blur(30px)',
    WebkitBackdropFilter: 'blur(30px)',
    zIndex: 10,
    pointerEvents: 'auto',
    cursor: 'pointer',
    transition: 'background 0.3s ease',
    fontFamily: '"Hedvig Letters Serif", serif',
  },
  downloadButton: {
    position: 'absolute',
    bottom: '24px',
    right: '24px',
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    background: 'rgba(63, 63, 63, 0.38)',
    color: 'white',
    border: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backdropFilter: 'blur(30px)',
    WebkitBackdropFilter: 'blur(30px)',
    zIndex: 10,
    pointerEvents: 'auto',
    cursor: 'pointer',
    transition: 'background 0.3s ease',
    fontFamily: '"Hedvig Letters Serif", serif',
  },
  sourcesModal: {
    position: 'absolute',
    bottom: '76px',
    left: '24px',
    width: '264px',
    maxHeight: 'calc(100vh - 100px)',
    overflowY: 'auto',
    background: 'rgba(63, 63, 63, 0.3)',
    backdropFilter: 'blur(30px)',
    WebkitBackdropFilter: 'blur(30px)',
    borderRadius: '8px',
    zIndex: 12,
    pointerEvents: 'auto',
    padding: '20px',
    border: '1px solid rgba(63, 63, 63, 0.5)',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'transparent',
    zIndex: 11,
    pointerEvents: 'auto',
  },
}
