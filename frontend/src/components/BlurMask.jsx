import { useRef, useState, useEffect } from 'react'

/**
 * BlurMask — drag to draw rectangles on a video preview.
 * Returns masks as [{x, y, w, h}] in 0-1 fractions of the frame.
 */
export default function BlurMask({ onChange }) {
  const canvasRef  = useRef(null)
  const [masks, setMasks]     = useState([])
  const [drawing, setDrawing] = useState(false)
  const [start, setStart]     = useState(null)
  const [current, setCurrent] = useState(null)

  const W = 360, H = 640 // canvas display size (9:16)

  useEffect(() => { redraw() }, [masks, current])

  const redraw = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, W, H)

    // Background
    ctx.fillStyle = '#0d1219'
    ctx.fillRect(0, 0, W, H)

    // Grid
    ctx.strokeStyle = 'rgba(0,229,255,.08)'
    ctx.lineWidth = 1
    for (let x = 0; x < W; x += 40) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke() }
    for (let y = 0; y < H; y += 40) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke() }

    ctx.font = '13px DM Sans, sans-serif'
    ctx.fillStyle = 'rgba(0,229,255,.3)'
    ctx.textAlign = 'center'
    ctx.fillText('9:16 Preview — Drag to draw blur regions', W/2, H/2)

    // Existing masks
    masks.forEach((m, i) => {
      ctx.fillStyle = 'rgba(255,107,53,.3)'
      ctx.strokeStyle = '#ff6b35'
      ctx.lineWidth = 2
      ctx.fillRect(m.x*W, m.y*H, m.w*W, m.h*H)
      ctx.strokeRect(m.x*W, m.y*H, m.w*W, m.h*H)
      ctx.fillStyle = '#ff6b35'
      ctx.font = 'bold 11px DM Sans'
      ctx.textAlign = 'left'
      ctx.fillText(`Blur ${i+1}`, m.x*W+4, m.y*H+14)
    })

    // Current drag
    if (drawing && start && current) {
      const x = Math.min(start.x, current.x)
      const y = Math.min(start.y, current.y)
      const w = Math.abs(current.x - start.x)
      const h = Math.abs(current.y - start.y)
      ctx.fillStyle = 'rgba(0,229,255,.2)'
      ctx.strokeStyle = '#00e5ff'
      ctx.lineWidth = 2
      ctx.setLineDash([4,4])
      ctx.fillRect(x, y, w, h)
      ctx.strokeRect(x, y, w, h)
      ctx.setLineDash([])
    }
  }

  const getPos = e => {
    const r = canvasRef.current.getBoundingClientRect()
    return { x: e.clientX - r.left, y: e.clientY - r.top }
  }

  const onMouseDown = e => { setDrawing(true); setStart(getPos(e)); setCurrent(getPos(e)) }
  const onMouseMove = e => { if (drawing) setCurrent(getPos(e)) }
  const onMouseUp   = e => {
    if (!drawing || !start) return
    const end = getPos(e)
    const x = Math.min(start.x, end.x) / W
    const y = Math.min(start.y, end.y) / H
    const w = Math.abs(end.x - start.x) / W
    const h = Math.abs(end.y - start.y) / H
    if (w > 0.02 && h > 0.02) {
      const newMasks = [...masks, { x, y, w, h }]
      setMasks(newMasks)
      onChange(newMasks)
    }
    setDrawing(false); setStart(null); setCurrent(null)
  }

  const clearMasks = () => { setMasks([]); onChange([]) }

  return (
    <div>
      <canvas
        ref={canvasRef} width={W} height={H}
        style={{borderRadius:8, border:'1px solid #1e2a38', cursor:'crosshair', display:'block'}}
        onMouseDown={onMouseDown} onMouseMove={onMouseMove} onMouseUp={onMouseUp}
      />
      <div className="flex items-center justify-between mt-2">
        <span style={{fontSize:11,color:'#5a7080'}}>{masks.length} blur region{masks.length !== 1 ? 's' : ''} drawn</span>
        {masks.length > 0 && (
          <button onClick={clearMasks}
            style={{fontSize:11,color:'#ff4757',background:'rgba(255,71,87,.1)',
                    border:'1px solid rgba(255,71,87,.2)',padding:'3px 10px',borderRadius:4,cursor:'pointer'}}>
            Clear all
          </button>
        )}
      </div>
    </div>
  )
}
