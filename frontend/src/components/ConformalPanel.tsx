import { useEffect, useState } from 'react'
import { api } from '../api'

export default function ConformalPanel() {
    const [state, setState] = useState<any>(null)
    const fetch = async () => {
        const { data } = await api.get('/conformal/state?sensor_id=sensor-1')
    setState(data)
  }
    useEffect(() => { fetch(); const id = setInterval(fetch, 3000); return () => clearInterval(id) }, [])
    const reset = async () => {
        await api.post('/conformal/reset?sensor_id=sensor-1'); fetch()}

  if (!state) return null
        return (
            <div style={{
                background: '#1a1a1a', padding: 16, borderRadius: 12, border: state.q_value>1 ? '1px solid #ff4d4f':'1px solid #00ff88', marginTop:16}}>
                    <h3>🎯 Adaptive Conformal Correction</h3>
      <div style={{display:'flex', gap:16, fontSize:14}}>
        <div><b>q-value:</b> {state.q_value.toFixed(3)}</div>
        <div><b>Interval Adjustment:</b> +{(state.q_value*2).toFixed(2)} width</div>
        <div style={{color: state.q_value>0.5 ? '#ffaa00':'#00ff88'}}>{state.q_value>0.5 ? 'Widening intervals (drift!)' : 'Intervals calibrated'}</div>
      </div >
        <p style={{
            fontSize: 12, color: '#888'}}>Formula: q_t+1 = q_t + 0.05*(err - 0.1). Auto-widens when coverage drops.</p>
                <button onClick = { reset } style = {{
                    marginTop: 8, padding: '6px 12px', background:'#333', color:'white', border:0, borderRadius:6}}>Reset q</button>
    </div >
  )
            }