import { createContext, useContext, useState, useCallback } from 'react'

const BatchContext = createContext(null)

export function BatchProvider({ children }) {
  // docs: { [fileName]: { marc, raw, dc, errors } }
  const [docs, setDocs] = useState({})
  const [selectedName, setSelectedName] = useState(null)

  const addDoc = useCallback((name, payload) => {
    setDocs((prev) => ({ ...prev, [name]: payload }))
    setSelectedName(name)
  }, [])

  const updateMarc = useCallback((name, marc) => {
    setDocs((prev) => ({ ...prev, [name]: { ...prev[name], marc } }))
  }, [])

  const clear = useCallback(() => {
    setDocs({})
    setSelectedName(null)
  }, [])

  return (
    <BatchContext.Provider
      value={{ docs, selectedName, setSelectedName, addDoc, updateMarc, clear }}
    >
      {children}
    </BatchContext.Provider>
  )
}

export function useBatch() {
  const ctx = useContext(BatchContext)
  if (!ctx) throw new Error('useBatch phải nằm trong <BatchProvider>')
  return ctx
}
