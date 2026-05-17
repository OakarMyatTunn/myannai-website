import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Download, RefreshCw, CheckCircle, XCircle, Loader, Clock } from 'lucide-react'
import Layout from '../components/Layout'
import { jobs as jobsApi } from '../api/client'

export default function JobDetail() {
  const { id }  = useParams()
  const [job, setJob] = useState(null)

  const load = async () => {
    try { setJob(await jobsApi.get(id)) }
    catch(e) { console.error(e) }
  }

  useEffect(() => {
    load()
    const t = setInterval(() => {
      if (job?.status === 'processing' || job?.status === 'queued') load()
    }, 2000)
    return () => clearInterval(t)
  }, [job?.status])

  if (!job) return (
    <Layout>
      <div style={{textAlign:'center',padding:80,color:'#5a7080'}}>Loading...</div>
    </Layout>
  )

  const s = job.settings || {}
  const statusIcon = {
    queued:     <Clock size={20} style={{color:'#5a7080'}} />,
    processing: <Loader size={20} style={{color:'#00e5ff',animation:'spin 1s linear infinite'}} />,
    complete:   <CheckCircle size={20} style={{color:'#06d6a0'}} />,
    failed:     <XCircle size={20} style={{color:'#ff4757'}} />,
  }[job.status]

  const langs = s.language === 'both' ? ['myanmar','english'] : [s.language || 'myanmar']

  return (
    <Layout>
      <Link to="/" style={{color:'#5a7080',fontSize:13,textDecoration:'none',
                           display:'flex',alignItems:'center',gap:6,marginBottom:20}}>
        <ArrowLeft size={14} /> Back to Dashboard
      </Link>

      <div style={{display:'grid',gridTemplateColumns:'1fr 340px',gap:20,alignItems:'start'}}>
        {/* Left */}
        <div>
          <div style={{background:'#111820',border:'1px solid #1e2a38',borderRadius:12,padding:24,marginBottom:16}}>
            <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:16}}>
              {statusIcon}
              <h2 style={{fontFamily:'Bebas Neue',fontSize:28,letterSpacing:1}}>
                {job.status.toUpperCase()}
              </h2>
              <span style={{fontSize:11,color:'#5a7080',marginLeft:'auto'}}>
                {new Date(job.created_at).toLocaleString()}
              </span>
            </div>

            {/* Progress bar */}
            {(job.status === 'processing' || job.status === 'queued') && (
              <div style={{marginBottom:16}}>
                <div style={{height:6,background:'#1e2a38',borderRadius:6,overflow:'hidden',marginBottom:8}}>
                  <div style={{height:'100%',width:`${job.progress}%`,
                    background:'linear-gradient(90deg,#00e5ff,#ff6b35)',
                    borderRadius:6,transition:'width .5s'}} />
                </div>
                <div style={{fontSize:12,color:'#00e5ff'}}>
                  {job.step} — {job.progress}%
                </div>
              </div>
            )}

            {job.status === 'failed' && (
              <div style={{background:'rgba(255,71,87,.08)',border:'1px solid rgba(255,71,87,.2)',
                           borderRadius:8,padding:12,fontSize:12,color:'#ff4757'}}>
                <strong>Error:</strong> {job.step}
              </div>
            )}

            {/* Source */}
            <div style={{fontSize:12,color:'#5a7080',marginBottom:4}}>Source</div>
            <div style={{fontSize:13,wordBreak:'break-all',marginBottom:16}}>
              {job.source_url || job.source_file?.split(/[\\/]/).pop() || 'Unknown'}
            </div>

            {/* Settings chips */}
            <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
              {[
                s.script_style, s.language, `${s.voice_gender} voice`,
                `${s.voice_speed}x`,s.voice_pitch,
                s.flip_video && 'flip',
                s.auto_color && 'color grade',
                s.copyright_bypass && 'copyright bypass',
                s.subtitles && 'subtitles',
                s.blur_masks?.length > 0 && `${s.blur_masks.length} blur`,
                s.logo && 'logo',
                s.intro && 'intro',
                s.outro && 'outro',
              ].filter(Boolean).map(tag => (
                <span key={tag} style={{fontSize:10,padding:'3px 10px',borderRadius:4,
                  background:'rgba(255,255,255,.04)',border:'1px solid #1e2a38',color:'#5a7080'}}>
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Downloads */}
          {job.status === 'complete' && (
            <div style={{background:'#111820',border:'1px solid rgba(6,214,160,.2)',
                         borderRadius:12,padding:24}}>
              <h3 style={{fontFamily:'Bebas Neue',fontSize:22,letterSpacing:1,
                          color:'#06d6a0',marginBottom:16}}>
                ✅ READY TO DOWNLOAD
              </h3>
              <div style={{display:'flex',flexDirection:'column',gap:8}}>
                {langs.map(lang => (
                  <a key={lang}
                     href={jobsApi.downloadUrl(id, lang)}
                     style={{display:'flex',alignItems:'center',justifyContent:'space-between',
                             background:'rgba(6,214,160,.06)',border:'1px solid rgba(6,214,160,.2)',
                             borderRadius:8,padding:'12px 16px',textDecoration:'none',
                             transition:'background .2s'}}
                     onMouseEnter={e=>e.currentTarget.style.background='rgba(6,214,160,.12)'}
                     onMouseLeave={e=>e.currentTarget.style.background='rgba(6,214,160,.06)'}>
                    <span style={{fontSize:13,fontWeight:600,color:'#06d6a0'}}>
                      {lang === 'myanmar' ? '🇲🇲 Myanmar Version' : '🇬🇧 English Version'}
                    </span>
                    <div style={{display:'flex',alignItems:'center',gap:6,
                                 fontSize:12,color:'#06d6a0'}}>
                      <Download size={14} /> Download MP4
                    </div>
                  </a>
                ))}
              </div>
              <p style={{fontSize:11,color:'#5a7080',marginTop:12}}>
                ⚠️ Files auto-deleted after 7 days
              </p>
            </div>
          )}
        </div>

        {/* Right — Job ID + refresh */}
        <div style={{background:'#111820',border:'1px solid #1e2a38',borderRadius:12,padding:20}}>
          <div style={{fontSize:10,color:'#5a7080',letterSpacing:1,textTransform:'uppercase',marginBottom:8}}>
            Job ID
          </div>
          <div style={{fontSize:11,fontFamily:'monospace',color:'#00e5ff',
                       wordBreak:'break-all',marginBottom:16}}>
            {job.id}
          </div>
          <button onClick={load}
            style={{width:'100%',padding:'8px',borderRadius:6,border:'1px solid #1e2a38',
                    background:'transparent',color:'#5a7080',cursor:'pointer',fontSize:12,
                    display:'flex',alignItems:'center',justifyContent:'center',gap:6}}>
            <RefreshCw size={12} /> Refresh Status
          </button>
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </Layout>
  )
}
