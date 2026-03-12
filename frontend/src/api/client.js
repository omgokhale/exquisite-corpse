/**
 * API client for Exquisite Corpse Generator
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api'

export async function generateComposite() {
  const response = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    let errorMessage = 'Failed to generate composite'
    try {
      const error = await response.json()
      errorMessage = error.detail || errorMessage
    } catch (e) {
      // Response wasn't JSON, use status text
      errorMessage = `Server error: ${response.status} ${response.statusText}`
    }
    throw new Error(errorMessage)
  }

  try {
    return await response.json()
  } catch (e) {
    throw new Error('Invalid response from server')
  }
}

export async function getArtwork(artworkId) {
  const response = await fetch(`${API_BASE}/artwork/${artworkId}`)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch artwork')
  }

  return response.json()
}

export async function getGeneration(generationId) {
  const response = await fetch(`${API_BASE}/generation/${generationId}`)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch generation')
  }

  return response.json()
}
