import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Link2, Upload, Film, Mic, Wand2, Eye, Image } from 'lucide-react'
import Layout from '../components/Layout'
import BlurMask from '../components/BlurMask'
import { jobs as jobsApi, assets as assetsApi } from '../api/client'

const STYLES = [
  { id:'standard',    label:'Standard',    desc:'Clear professional narration',          emoji:'📋' },
  { id:'story',       label:'Story',       desc:'3-act dramatic arc',                    emoji:'📖' },
  { id:'quick',       label:'Quick',       desc:'Punchy under 60 seconds',               emoji:'⚡' },
  { id:'dramatic',    label:'Dramatic',    desc:'Suspenseful, emotional tone',           emoji:'🎭' },
  { id:'comedy',      label:'Comedy',      desc:'Fun and lighthearted recap',            emoji:'😄' },
  { id:'educational', label:'Educational', desc:'Facts-first, informative',              emoji:'🎓' },
]

const SECTION = ({ title, children }) => (
  <div style={{background:'#111820',border:'1px solid #1e2a38',borderRadius:12,overflow:'hidden',marginBottom:16}}>
    <div style={{padding:'14px 20px',borderBottom:'1px solid #1e2a38',
                 fontSize:11,fontWeight:700,letterSpacing:2,color:'#5a7080',textTransform:'uppercase'}}>
      {title}
    </div>
    <div style={{padding:20}}>{children}</div>
  </div>
)

const ROW = ({ label, children }) => (
  <div style={{display:'grid',gridTemplateColumns:'160px 1fr',gap:16,alignItems:'start',marginBottom:16}}>
    <div style={{fontSize:12,color:'#5a7080',paddingTop:8}}>{label}</div>
    <div>{children}</div>
  </div>
)

const Toggle = ({ checked, onChange, label }) => (
  <label style={{display:'flex',alignItems:'center',gap:10,cursor:'pointer'}}>
    <div style={{width:44,height:24,borderRadius:12,
                 background: checked ? '#00e5ff' : '#1e2a38',
                 position:'relative',transition:'background .2s'}}
         onClick={() => onChange(!checked)}>
      <div style={{width:18,height:18,borderRadius:9,background:'#fff',
                   position:'absolute',top:3,
                   left: checked ? 23 : 3,
                   transition:'left .2s'}} />
    </div>
    <span style={{fontSize:13,color: checked ? '#e8edf2' : '#5a7080'}}>{label}</span>
  </label>
)

const Select = ({ value, onChange, options }) => (
  <select value={value} onChange={e => onChange(e.target.value)}
    style={{background:'#0d1219',border:'1px solid #1e2a38',color:'#e8edf2',
            fontFamily:'DM Sans',fontSize:13,padding:'8px 12px',borderRadius:8,
            outline:'none',width:'100%'}}>
    {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
  </select>
)

export default function NewJob() {
  const nav = useNavigate()
  const [tab, setTab]         = useState('url')   // url | file
  const [url, setUrl]         = useState('')
  const [file, setFile]       = useState(null)
  const [submitting, setSub]  = useState(false)
  const [error, setError]     = useState('')

  // Settings
  const [style, setStyle]     = useState('standard')
  const [language, setLang]   = useState('myanmar')
  const [gender, setGender]   = useState('male')
  const [speed, setSpeed]     = useState(1.0)
  const [pitch, setPitch]     = useState('normal')
  const [flip, setFlip]       = useState(false)
  const [color, setColor]     = useState(true)
  const [bypass, setBypass]   = useState(true)
  const [subs, setSubs]       = useState(true)
  const [masks, setMasks]     = useState([])
  const [useLogo, setUseLogo] = useState(false)
  const [useIntro, setIntro]  = useState(false)
  const [useOutro, setOutro]  = useState(false)
  const [showMask, setShowMask] = useState(false)

  const submit = async () => {
    if (tab === 'url' && !url.trim()) { setError('Please enter a URL'); return }
    if (tab === 'file' && !file)      { setError('Please select a file'); return }
    setError(''); setSub(true)
    try {
      let job
      const settings = {
        script_style: style, language, voice_gender: gender,
        voice_speed: speed, voice_pitch: pitch,
        flip_video: flip, auto_color: color,
        copyright_bypass: bypass, subtitles: subs,
        blur_masks: masks,
        logo: useLogo, intro: useIntro, outro: useOutro,
      }

      if (tab === 'url') {
        job = await jobsApi.submit({ source_url: url, ...settings })
      } else {
        const fd = new FormData()
        fd.append('file', file)
        Object.entries(settings).forEach(([k,v]) =>
          fd.append(k, typeof v === 'object' ? JSON.stringify(v) : v)
        )
        job = await jobsApi.uploadFile(fd)
      }
      nav(`/jobs/${job.id}`)
    } catch(e) {
      setError(e.response?.data?.detail || e.message || 'Submission failed')
    } finally {
      setSub(false)
    }
  }

  return (
    <Layout>
      <div style={{maxWidth:800,margin:'0 auto'}}>
        <div style={{marginBottom:24}}>
          <h1 style={{fontFamily:'Bebas Neue',fontSize:40,letterSpacing:2}}>NEW JOB</h1>
          <p style={{color:'#5a7080',fontSize:14}}>Configure your video recap job</p>
        </div>

        {/* Source */}
        <SECTION title="📥 Source Video">
          <div style={{display:'flex',gap:4,marginBottom:16}}>
            {['url','file'].map(t => (
              <button key={t} onClick={() => setTab(t)}
                style={{padding:'7px 20px',borderRadius:6,border:'none',cursor:'pointer',
                        fontSize:13,fontWeight:600,
                        background: tab===t ? '#00e5ff' : '#1e2a38',
                        color: tab===t ? '#000' : '#5a7080'}}>
                {t === 'url' ? '🔗 URL' : '📁 File Upload'}
              </button>
            ))}
          </div>

          {tab === 'url' ? (
            <div>
              <input value={url} onChange={e => setUrl(e.target.value)}
                placeholder="YouTube, TikTok, Facebook, Instagram, Xiaohongshu, Google Drive..."
                style={{width:'100%',background:'#0d1219',border:'1px solid #1e2a38',
                        color:'#e8edf2',fontFamily:'DM Sans',fontSize:13,
                        padding:'10px 14px',borderRadius:8,outline:'none'}} />
              <p style={{fontSize:11,color:'#5a7080',marginTop:6}}>
                Supports YouTube • TikTok • Facebook • Instagram • Xiaohongshu • Google Drive links
              </p>
            </div>
          ) : (
            <div>
              <label style={{display:'block',border:'2px dashed #1e2a38',borderRadius:10,
                             padding:30,textAlign:'center',cursor:'pointer',
                             transition:'border-color .2s'}}
                     onMouseEnter={e=>e.target.style.borderColor='#00e5ff'}
                     onMouseLeave={e=>e.target.style.borderColor='#1e2a38'}>
                <input type="file" accept="video/*,.mkv" style={{display:'none'}}
                       onChange={e => setFile(e.target.files[0])} />
                <Upload size={28} style={{color:'#5a7080',margin:'0 auto 8px'}} />
                <div style={{fontSize:14,fontWeight:500}}>
                  {file ? file.name : 'Click to select video file'}
                </div>
                <div style={{fontSize:11,color:'#5a7080',marginTop:4}}>MP4, MKV, MOV, AVI (max 2GB)</div>
              </label>
              {file && (
                <div style={{fontSize:12,color:'#06d6a0',marginTop:8}}>
                  ✓ {file.name} ({(file.size/1024/1024).toFixed(1)}MB)
                </div>
              )}
            </div>
          )}
        </SECTION>

        {/* Script Style */}
        <SECTION title="✍️ Script Style">
          <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:8}}>
            {STYLES.map(s => (
              <button key={s.id} onClick={() => setStyle(s.id)}
                style={{padding:'12px 10px',borderRadius:8,cursor:'pointer',textAlign:'left',
                        border: style===s.id ? '1px solid #00e5ff' : '1px solid #1e2a38',
                        background: style===s.id ? 'rgba(0,229,255,.06)' : '#0d1219',
                        transition:'all .2s'}}>
                <div style={{fontSize:20,marginBottom:4}}>{s.emoji}</div>
                <div style={{fontSize:13,fontWeight:600,color: style===s.id ? '#00e5ff' : '#e8edf2'}}>
                  {s.label}
                </div>
                <div style={{fontSize:11,color:'#5a7080',marginTop:2}}>{s.desc}</div>
              </button>
            ))}
          </div>
        </SECTION>

        {/* Voice */}
        <SECTION title="🎙️ Voice Settings">
          <ROW label="Language">
            <Select value={language} onChange={setLang} options={[
              {value:'myanmar', label:'Myanmar (မြန်မာ)'},
              {value:'english', label:'English'},
              {value:'both',    label:'Both — EN + Myanmar'},
            ]} />
          </ROW>
          <ROW label="Voice">
            <Select value={gender} onChange={setGender} options={[
              {value:'male',   label:'Male — Thiha (Deep, confident)'},
              {value:'female', label:'Female — Nilar (Clear, warm)'},
            ]} />
          </ROW>
          <ROW label={`Speed — ${speed}x`}>
            <input type="range" min="0.7" max="1.3" step="0.05"
                   value={speed} onChange={e => setSpeed(parseFloat(e.target.value))}
                   style={{width:'100%',accentColor:'#00e5ff'}} />
          </ROW>
          <ROW label="Pitch">
            <Select value={pitch} onChange={setPitch} options={[
              {value:'low',    label:'Low'},
              {value:'normal', label:'Normal'},
              {value:'high',   label:'High'},
            ]} />
          </ROW>
        </SECTION>

        {/* Video Effects */}
        <SECTION title="🎬 Video Effects">
          <div style={{display:'flex',flexDirection:'column',gap:12}}>
            <Toggle checked={bypass}  onChange={setBypass}  label="Copyright Bypass — speed/zoom/color variation per clip" />
            <Toggle checked={color}   onChange={setColor}   label="Auto Color Grade — boost saturation & contrast" />
            <Toggle checked={flip}    onChange={setFlip}    label="Flip Video — horizontal mirror" />
            <Toggle checked={subs}    onChange={setSubs}    label="Burn Subtitles — words overlaid on video" />
          </div>
        </SECTION>

        {/* Blur Mask */}
        <SECTION title="🔲 Custom Blur Mask">
          <p style={{fontSize:12,color:'#5a7080',marginBottom:12}}>
            Draw rectangles on the preview to blur logos, watermarks, or unwanted UI elements.
          </p>
          <button onClick={() => setShowMask(!showMask)}
            style={{fontSize:12,color:'#00e5ff',background:'rgba(0,229,255,.08)',
                    border:'1px solid rgba(0,229,255,.2)',padding:'6px 14px',
                    borderRadius:6,cursor:'pointer',marginBottom:16}}>
            {showMask ? 'Hide Mask Canvas' : 'Open Mask Canvas'}
            {masks.length > 0 && ` (${masks.length} region${masks.length>1?'s':''})`}
          </button>
          {showMask && <BlurMask onChange={setMasks} />}
        </SECTION>

        {/* Branding */}
        <SECTION title="🏷️ Branding">
          <div style={{display:'flex',flexDirection:'column',gap:12}}>
            <Toggle checked={useLogo}  onChange={setUseLogo}  label="Logo Watermark (top-left) — upload in Assets" />
            <Toggle checked={useIntro} onChange={setIntro}    label="Intro Video — prepend to output" />
            <Toggle checked={useOutro} onChange={setOutro}    label="Outro Video — append to output" />
          </div>
        </SECTION>

        {error && (
          <div style={{background:'rgba(255,71,87,.1)',border:'1px solid rgba(255,71,87,.3)',
                       borderRadius:8,padding:'10px 14px',color:'#ff4757',fontSize:13,marginBottom:16}}>
            {error}
          </div>
        )}

        <button onClick={submit} disabled={submitting}
          style={{width:'100%',padding:16,borderRadius:10,border:'none',cursor:'pointer',
                  background: submitting ? '#1e2a38' : 'linear-gradient(135deg,#00e5ff,#00b4cc)',
                  color: submitting ? '#5a7080' : '#000',
                  fontFamily:'Bebas Neue',fontSize:22,letterSpacing:2,
                  transition:'all .2s',
                  boxShadow: submitting ? 'none' : '0 4px 20px rgba(0,229,255,.3)'}}>
          {submitting ? 'SUBMITTING...' : 'GENERATE RECAP →'}
        </button>
      </div>
    </Layout>
  )
}
