import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Trash2, Download, Eye, Clock, CheckCircle, XCircle, Loader } from 'lucide-react'
import Layout from '../components/Layout'
import { jobs as jobsApi } from '../api/client'

const STATUS_CONFIG = {
  queued:     { color: '#5a7080', icon: Clock,        label: 'Queued' },
  processing: { color: '#00e5ff', icon: Loader,       label: 'Processing' },
  complete:   { color: '#06d6a0', icon: CheckCircle,  label: 'Complete' },
  failed:     { color: '#ff4757', icon: XCircle,      label: 'Failed' },
}

export default function Dashboard() {
  const [jobList, setJobList] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try { setJobList(await jobsApi.list()) }
    catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => {
    load()
    const t = setInterval(load, 3000) // poll every 3s
    return () => clearInterval(t)
  }, [])

  const handleDelete = async (id, e) => {
    e.preventDefault()
    if (!confirm('Delete this job?')) return
    await jobsApi.delete(id)
    load()
  }

  return (
    <Layout>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 style={{fontFamily:'Bebas Neue',fontSize:40,letterSpacing:2,lineHeight:1}}>
            JOB DASHBOARD
          </h1>
          <p style={{color:'#5a7080',fontSize:14,marginTop:4}}>
            {jobList.length} job{jobList.length !== 1 ? 's' : ''} total
          </p>
        </div>
        <Link to="/new"
          style={{background:'#00e5ff',color:'#000',fontWeight:700,fontSize:14,
                  padding:'10px 24px',borderRadius:8,textDecoration:'none',
                  display:'flex',alignItems:'center',gap:6,
                  boxShadow:'0 0 24px rgba(0,229,255,.3)'}}>
          <Plus size={16} /> New Job
        </Link>
      </div>

      {loading && (
        <div style={{textAlign:'center',color:'#5a7080',padding:60}}>
          Loading jobs...
        </div>
      )}

      {!loading && jobList.length === 0 && (
        <div style={{background:'#111820',border:'1px solid #1e2a38',borderRadius:16,
                     padding:60,textAlign:'center'}}>
          <div style={{fontSize:48,marginBottom:16}}>🎬</div>
          <h3 style={{fontFamily:'Bebas Neue',fontSize:28,letterSpacing:1,marginBottom:8}}>
            NO JOBS YET
          </h3>
          <p style={{color:'#5a7080',marginBottom:24}}>
            Submit your first video recap job to get started.
          </p>
          <Link to="/new"
            style={{background:'#00e5ff',color:'#000',fontWeight:700,
                    padding:'10px 24px',borderRadius:8,textDecoration:'none'}}>
            Create First Job →
          </Link>
        </div>
      )}

      <div style={{display:'flex',flexDirection:'column',gap:12}}>
        {jobList.map(job => {
          const s = STATUS_CONFIG[job.status] || STATUS_CONFIG.queued
          const Icon = s.icon
          const settings = job.settings || {}
          return (
            <Link key={job.id} to={`/jobs/${job.id}`}
              style={{background:'#111820',border:'1px solid #1e2a38',borderRadius:12,
                      padding:'18px 20px',textDecoration:'none',color:'inherit',
                      display:'grid',gridTemplateColumns:'1fr auto',gap:16,
                      transition:'border-color .2s'}}
              onMouseEnter={e=>e.currentTarget.style.borderColor='rgba(0,229,255,.3)'}
              onMouseLeave={e=>e.currentTarget.style.borderColor='#1e2a38'}>
              <div>
                <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:6}}>
                  <Icon size={14} style={{color:s.color,
                    animation: job.status==='processing' ? 'spin 1s linear infinite' : 'none'}} />
                  <span style={{fontSize:11,color:s.color,fontWeight:700,letterSpacing:1,textTransform:'uppercase'}}>
                    {s.label}
                  </span>
                  <span style={{fontSize:11,color:'#5a7080',marginLeft:8}}>
                    {new Date(job.created_at).toLocaleString()}
                  </span>
                </div>
                <div style={{fontSize:14,fontWeight:500,marginBottom:4}}>
                  {job.source_url
                    ? job.source_url.slice(0, 60) + (job.source_url.length > 60 ? '...' : '')
                    : job.source_file
                      ? `File: ${job.source_file.split(/[\\/]/).pop()}`
                      : 'Unknown source'}
                </div>
                <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
                  {[
                    settings.script_style,
                    settings.language,
                    settings.voice_gender,
                    settings.flip_video && 'flip',
                    settings.auto_color && 'color',
                    settings.subtitles && 'subtitles',
                  ].filter(Boolean).map(tag => (
                    <span key={tag} style={{fontSize:10,padding:'2px 8px',borderRadius:4,
                      background:'rgba(255,255,255,.05)',border:'1px solid #1e2a38',color:'#5a7080'}}>
                      {tag}
                    </span>
                  ))}
                </div>
                {job.status === 'processing' && (
                  <div style={{marginTop:8}}>
                    <div style={{height:3,background:'#1e2a38',borderRadius:4,overflow:'hidden'}}>
                      <div style={{height:'100%',width:`${job.progress}%`,
                        background:'linear-gradient(90deg,#00e5ff,#ff6b35)',
                        borderRadius:4,transition:'width .5s'}} />
                    </div>
                    <div style={{fontSize:11,color:'#5a7080',marginTop:4}}>
                      {job.step} — {job.progress}%
                    </div>
                  </div>
                )}
              </div>
              <div style={{display:'flex',alignItems:'center',gap:8}}>
                {job.status === 'complete' && (
                  <a href={jobsApi.downloadUrl(job.id, settings.language || 'myanmar')}
                     onClick={e=>e.stopPropagation()}
                     style={{background:'rgba(6,214,160,.1)',color:'#06d6a0',
                             border:'1px solid rgba(6,214,160,.2)',padding:'6px 12px',
                             borderRadius:6,fontSize:12,fontWeight:600,textDecoration:'none',
                             display:'flex',alignItems:'center',gap:4}}>
                    <Download size={12} /> Download
                  </a>
                )}
                <button onClick={(e) => handleDelete(job.id, e)}
                  style={{background:'rgba(255,71,87,.1)',color:'#ff4757',
                          border:'1px solid rgba(255,71,87,.2)',padding:'6px 10px',
                          borderRadius:6,cursor:'pointer'}}>
                  <Trash2 size={12} />
                </button>
              </div>
            </Link>
          )
        })}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </Layout>
  )
}
