import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const TOKEN = 'devtoken'

function Card({title,children}){
  return <div style={{padding:16, borderRadius:16, boxShadow:'0 6px 22px rgba(0,0,0,0.08)', marginBottom:16}}>
    <h3 style={{marginTop:0}}>{title}</h3>
    <div>{children}</div>
  </div>
}

function App(){
  const [events, setEvents] = useState([])
  const [manifest, setManifest] = useState(`apiVersion: apps/v1
kind: Deployment
metadata: {name: demo}
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: web
        image: nginx:1.27`)
  const [diff, setDiff] = useState('api_key=ABCD1234EFGH5678TOKEN')
  const [driftScore, setDriftScore] = useState(null)
  const [secretScore, setSecretScore] = useState(null)

  const headers = {'Authorization': 'Bearer ' + TOKEN, 'Content-Type':'application/json'}

  const refresh = async () => {
    const r = await fetch(API + '/events', {headers})
    if(r.ok){
      setEvents(await r.json())
    }
  }

  useEffect(()=>{ refresh() }, [])

  const checkDrift = async () => {
    const r = await fetch(API + '/drift/check', {method:'POST', headers, body: JSON.stringify({manifest, source:'ui'})})
    const j = await r.json()
    setDriftScore(j.score?.toFixed(3))
    refresh()
  }

  const checkSecret = async () => {
    const r = await fetch(API + '/secret/check', {method:'POST', headers, body: JSON.stringify({diff})})
    const j = await r.json()
    setSecretScore(j.score?.toFixed(3))
    refresh()
  }

  return <div style={{maxWidth:1000, margin:'40px auto', fontFamily:'Inter, system-ui, sans-serif', padding:'0 16px'}}>
    <h1 style={{letterSpacing:'-0.02em'}}>ObservaGuard</h1>
    <p>AI‑powered drift & secret‑leak sentinel for your K8s + GitOps.</p>

    <Card title="Drift Check (YAML manifest)">
      <textarea value={manifest} onChange={e=>setManifest(e.target.value)} rows={12} style={{width:'100%', fontFamily:'monospace', borderRadius:12, padding:12}} />
      <button onClick={checkDrift} style={{padding:'10px 16px', borderRadius:12, border:'1px solid #ddd', cursor:'pointer'}}>Analyze Drift</button>
      {driftScore && <div>Drift Anomaly Score: <b>{driftScore}</b></div>}
    </Card>

    <Card title="Secret Leak Check (diff/text)">
      <textarea value={diff} onChange={e=>setDiff(e.target.value)} rows={6} style={{width:'100%', fontFamily:'monospace', borderRadius:12, padding:12}} />
      <button onClick={checkSecret} style={{padding:'10px 16px', borderRadius:12, border:'1px solid #ddd', cursor:'pointer'}}>Scan Secrets</button>
      {secretScore && <div>Leak Risk Score: <b>{secretScore}</b></div>}
    </Card>

    <Card title="Recent Events">
      <table style={{width:'100%', borderCollapse:'collapse'}}>
        <thead><tr><th align="left">Time</th><th align="left">Kind</th><th align="left">Score</th></tr></thead>
        <tbody>
          {events.map(e=>(
            <tr key={e.id}>
              <td>{new Date(e.ts*1000).toLocaleString()}</td>
              <td>{e.kind}</td>
              <td>{e.score?.toFixed?.(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  </div>
}

createRoot(document.getElementById('root')).render(<App/>)
