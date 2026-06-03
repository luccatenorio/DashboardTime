import { useEffect, useState } from 'react'
import Dashboard from './Dashboard'
import FeedbackForm from './FeedbackForm'

function parseRoute() {
    const hash = window.location.hash || ''
    const m = hash.match(/^#\/feedback\/(.+)$/)
    if (m) return { name: 'feedback', hash: m[1].replace(/\/$/, '').trim() }
    return { name: 'dashboard' }
}

function App() {
    const [route, setRoute] = useState(parseRoute)
    useEffect(() => {
        const onHashChange = () => setRoute(parseRoute())
        window.addEventListener('hashchange', onHashChange)
        return () => window.removeEventListener('hashchange', onHashChange)
    }, [])

    return (
        <div className="app">
            {route.name === 'feedback' ? <FeedbackForm hash={route.hash} /> : <Dashboard />}
        </div>
    )
}

export default App
