import { useState } from 'react'
import './App.css'
import AuthPanel from './components/AuthPanel'
import FileUpload from './components/FileUpload'
import QueryBox from './components/QueryBox'


function App() {
  const [documentId, setDocumentId] = useState(null)
  const [auth, setAuth] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('docuquery_auth'))
    } catch {
      return null
    }
  })

  function handleAuthenticated(authResponse) {
    localStorage.setItem('docuquery_auth', JSON.stringify(authResponse))
    setAuth(authResponse)
    setDocumentId(null)
  }

  function handleLogout() {
    localStorage.removeItem('docuquery_auth')
    setAuth(null)
    setDocumentId(null)
  }

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-10 text-slate-100">
      <main className="mx-auto max-w-3xl space-y-6">
        <header className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-400">
            AI document assistant
          </p>
          <h1 className="text-4xl font-bold tracking-tight text-slate-100 sm:text-5xl">
            DocuQuery
          </h1>
          <p className="max-w-2xl text-slate-400">
            Upload a PDF and ask questions about its contents with answers grounded in your document.
          </p>
        </header>

        {auth ? (
          <>
            <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm">
              <span className="text-slate-400">
                Signed in as <span className="font-medium text-slate-200">{auth.username}</span>
              </span>
              <button type="button" onClick={handleLogout} className="text-blue-300 hover:text-blue-200">
                Sign out
              </button>
            </div>
            <FileUpload token={auth.access_token} onUploadSuccess={setDocumentId} />
            <QueryBox token={auth.access_token} documentId={documentId} />
          </>
        ) : (
          <AuthPanel onAuthenticated={handleAuthenticated} />
        )}
      </main>
    </div>
  )
}

export default App
