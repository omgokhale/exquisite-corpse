import { useState, useEffect, useMemo } from 'react'

const AnimatedText = ({ text, isAnimating, baseDelay = 0 }) => {
  const chars = useMemo(() => {
    if (!text) return []

    // Split text into characters and assign random delays
    return text.split('').map((char, i) => ({
      char,
      delay: baseDelay + Math.random() * 400 // Random delay up to 400ms
    }))
  }, [text, baseDelay])

  return (
    <span style={{ display: 'inline-block' }}>
      {chars.map((item, i) => (
        <span
          key={i}
          style={{
            display: 'inline-block',
            opacity: isAnimating ? 0 : 1,
            animation: isAnimating ? `letterPopIn 0.3s ease-out ${item.delay}ms both` : 'none',
          }}
        >
          {item.char === ' ' ? '\u00A0' : item.char}
        </span>
      ))}
    </span>
  )
}

export default function SourceCredits({ sources }) {
  const [isAnimating, setIsAnimating] = useState(true)
  const [loadedImages, setLoadedImages] = useState({})

  useEffect(() => {
    // Reset loaded images and trigger text animation when sources change
    setLoadedImages({})
    setIsAnimating(true)
    const timer = setTimeout(() => setIsAnimating(false), 1200)
    return () => clearTimeout(timer)
  }, [sources])

  const handleImageLoad = (artworkId) => {
    setLoadedImages(prev => ({ ...prev, [artworkId]: true }))
  }

  return (
    <div style={styles.container}>
      {sources.map((source, index) => (
        <div key={`${source.artwork_id}-${source.role}`}>
          <div style={styles.source}>
            <div style={styles.artwork}>
              {source.primary_image_url && (
                <div style={styles.imageContainer}>
                  <img
                    src={source.primary_image_url}
                    alt={source.title || 'Untitled'}
                    onLoad={() => handleImageLoad(source.artwork_id)}
                    style={{
                      ...styles.image,
                      opacity: loadedImages[source.artwork_id] ? 1 : 0,
                      animation: loadedImages[source.artwork_id] ? 'imageBlurIn 0.6s ease-out' : 'none',
                    }}
                  />
                </div>
              )}

              <div style={styles.info}>
                <div style={styles.artworkTitle}>
                  <AnimatedText
                    text={source.title || 'Untitled'}
                    isAnimating={isAnimating}
                    baseDelay={index * 100}
                  />
                </div>
                <div style={styles.artistDate}>
                  <AnimatedText
                    text={`${source.artist || 'Unknown Artist'}${source.object_date ? `, ${source.object_date}` : ''}`}
                    isAnimating={isAnimating}
                    baseDelay={index * 100 + 50}
                  />
                </div>
                <a
                  href={`https://www.metmuseum.org/art/collection/search/${source.artwork_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={styles.link}
                >
                  <AnimatedText
                    text="Visit at the MET"
                    isAnimating={isAnimating}
                    baseDelay={index * 100 + 100}
                  />
                </a>
              </div>
            </div>
          </div>
          {index < sources.length - 1 && <div style={styles.divider} />}
        </div>
      ))}
    </div>
  )
}

const styles = {
  container: {
    padding: '0',
  },
  source: {
    display: 'flex',
    flexDirection: 'column',
  },
  artwork: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  imageContainer: {
    width: '100%',
    display: 'flex',
    justifyContent: 'center',
  },
  image: {
    width: '224px',
    height: 'auto',
    borderRadius: '4px',
    border: '1px solid #333333',
  },
  divider: {
    width: '100%',
    height: '1px',
    background: 'rgba(255, 255, 255, 0.1)',
    marginTop: '24px',
    marginBottom: '24px',
  },
  info: {
    display: 'flex',
    flexDirection: 'column',
  },
  artworkTitle: {
    fontSize: '13px',
    fontWeight: 'bold',
    fontFamily: '"Hedvig Letters Serif", serif',
    color: '#ffffff',
    marginBottom: '2px',
    lineHeight: '1.4',
  },
  artistDate: {
    fontSize: '12px',
    fontFamily: '"Hedvig Letters Serif", serif',
    color: '#cccccc',
    lineHeight: '1.4',
    marginBottom: '8px',
  },
  link: {
    fontSize: '12px',
    fontFamily: '"Hedvig Letters Serif", serif',
    color: '#ffffff',
    textDecoration: 'underline',
    lineHeight: '1.4',
  },
}
