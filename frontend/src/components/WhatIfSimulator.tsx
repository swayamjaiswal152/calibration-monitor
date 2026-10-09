import { useState } from 'react'
import { api } from '../api'

export default function WhatIfSimulator({ onInject }: { onInject: () => void }) {
    const [drift, setDrift] = useState(3)
    const [preview, setPreview] = useState<any>(null)

    const handleSlider = async (v: number) => {
        setDrift(v)
        const { data } = await api.post(`/simulate/whatif?drift=${v}`)
        setPreview(data)
    }

    const inject = async () => {
        await api.post(`/simulate/drift?sensor_id=sensor-1&drift=${drift}&n=50`)
        onInject()
    }

    return (
    <div style={{ background: '#1a1a1a', padding: 16, borderRadius: 12, border: '1px solid #333', marginTop: 16 }}>
      <h3>🧪 What-If Drift Simulator <span style={{fontWeight:400, color:'#888', fontSize:14}}>- Drag to preview detection</span></h3>
      <input type="range" min="0" max="10" step="0.5" value={drift} onChange={e => handleSlider(parseFloat(e.target.value))} style = {{
    width: '100%'}}/>
        < div style = {{
            display: 'flex', justifyContent:'space-between', fontSize:14, color:'#aaa'}}>
                < span > Drift: { drift.toFixed(1) }</span >
        <span>Predicted Coverage: {preview ? (preview.predicted_coverage*100).toFixed(1)+'%' : '90%'}</span>
        <span style={{color: preview?.will_trigger_alert ? '#ff4d4f' : '#00ff88'}}>
          {preview?.will_trigger_alert ? '⚠️ WILL ALERT' : '✅ OK'}
        </span>
      </div>
      {preview && <div style={{fontSize:12, color:'#888', marginTop:8}}>Est. detection delay: {preview.estimated_detection_delay_mins} mins</div>}
      <button onClick={inject} style={{marginTop:12, width:'100%', padding:'10px', background:'#ff4d4f', color:'white', border:0, borderRadius:8, cursor:'pointer', fontWeight:600}}>
        Inject {drift} Drift Units (50 points)
      </button>
    </div>
  )
}