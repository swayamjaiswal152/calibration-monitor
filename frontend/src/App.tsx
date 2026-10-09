import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { api, wsUrl } from './api'
import WhatIfSimulator from './components/WhatIfSimulator'
import ConformalPanel from './components/ConformalPanel'

export default function App() {
    const [metrics, setMetrics] = useState<any>({ picp: 0.9, mae: 0, q_value: 0 })
    const [history, setHistory] = useState<any[]>([])
    const [alerts, setAlerts] = useState<any[]>([])

    const refresh = async () => {
        const { data } = await api.get('/metrics?sensor_id=sensor-1')
    setMetrics(data)
    const { data: al } = await api.get('/alerts')
    setAlerts(al)
  }

    useEffect(() => {
        const ws = new WebSocket(wsUrl('/ws/metrics'))
        ws.onmessage = (e) => {
            const msg = JSON.parse(e.data)
            if (msg.event === 'metrics_update') {
            setMetrics(msg.data)
            setHistory(h => [...h.slice(-50), { time: new Date().toLocaleTimeString(), coverage: msg.data.picp, q: msg.data.q_value }])
        }
        if (msg.event === 'alert') { setAlerts(a => [msg.data, ...a]); refresh() }
    }
    refresh()
    const id = setInterval(refresh, 3000)
    return () => { ws.close(); clearInterval(id) }
}, [])

return (
    <div style={{
        padding: 24, fontFamily: 'Inter', background: '#0a0a0a', color: 'white', minHeight: '100vh' }}>
            <h1>Forecast Calibration Monitor<span style = {{
                fontSize: 14, background: '#00ff88', color:'black', padding:'2px 8px', borderRadius:20}}>LIVE</span></h1>
                    < p > Target 90 % | Live PICP: <b style={{
                        color: metrics.picp < 0.85 ?'#ff4d4f' : '#00ff88'}}>{(metrics.picp * 100).toFixed(1)}%</b> | MAE: {metrics.mae?.toFixed(2)} | q: {metrics.q_value?.toFixed(2)}</p>

                            <div style = {{
                                display: 'grid', gridTemplateColumns:'2fr 1fr', gap:16}}>
                                    < div style = {{
                                        height: 300, background: '#1a1a1a', padding: 16, borderRadius: 12 }}>
                                            < h3 > Rolling Coverage</h3 >
                                                <ResponsiveContainer width="100%" height="90%">
                                                    <LineChart data={history.length ? history : [{ time: 'now', coverage: metrics.picp }]}>
                                                    <XAxis dataKey="time" stroke="#888" /><YAxis domain={[0, 1]} stroke="#888" />
                                                    <Tooltip /><ReferenceLine y={0.9} stroke="red" strokeDasharray="5 5" />
                                                    <Line type="monotone" dataKey="coverage" stroke="#00ff88" strokeWidth={2} dot={false} />
                                                </LineChart>
          </ResponsiveContainer >
        </div >
                                    <WhatIfSimulator onInject={refresh} />
      </div >

      <ConformalPanel />

      <div style={{ marginTop: 20 }}>
        <h3>Alerts ({alerts.length})</h3>
        {alerts.map((a,i) => <div key={i} style={{ background: '#ff4d4f22', border: '1px solid #ff4d4f', padding: 8, marginBottom: 8, borderRadius: 8 }}>
          ⚠️ {a.message || `Drift! Coverage ${(a.coverage*100).toFixed(1)}%`} - {new Date(a.time).toLocaleString()}
        </div>)
                            }
      </div >
    </div >
  )
                        }