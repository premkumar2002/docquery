import './App.css'
import FileUpload from './components/FileUpload'
import QueryBox from './components/QueryBox'


function App() {

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

        <FileUpload />
        <QueryBox />
      </main>
    </div>
  )
}

export default App
