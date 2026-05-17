import { useState, useEffect } from 'react'
import { Upload, Image, Film } from 'lucide-react'
import Layout from '../components/Layout'
import { assets as assetsApi } from '../api/client'

const AssetUpload = ({ type, label, accept, icon: Icon, onUpload }) => {
  const [uploading, setUploading] = useState(false)
  const [asset, setAsset]         = useState(null)

  useEffect(() => {
    assetsApi.list().then(list => {
      const a = list.find(x => x.type === type)
      if (a) setAsset(a)
    }).catch(() => {})
  }, [])

  const handle = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    const fd = new FormData()
    fd.append('file', file)
    try {
      const fn = type === 'logo' ? assetsApi.uploadLogo :
                 type === 'intro' ? assetsApi.uploadIntro : assetsApi.uploadOutro
      const result = await fn(fd)
      setAsset(result)
    } catch(e) {
      alert('Upload failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div style={{background:'#111820',border:'1px solid #1e2a38',borderRadius:12,padding:24}}>
      <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:16}}>
        <Icon size={16} style={{color:'#00e5ff'}} />
        <h3 style={{fontFamily:'Bebas Neue',fontSize:20,letterSpacing:1}}>{label}</h3>
      </div>

      {asset ? (
        <div style={{background:'rgba(6,214,160,.06)',border:'1px solid rgba(6,214,160,.2)',
                     borderRadius:8,padding:12,marginBottom:12}}>
          <div style={{fontSize:12,color:'#06d6a0'}}>✓ Uploaded</div>
          <div style={{fontSize:13,color:'#e8edf2',marginTop:2}}>{asset.filename}</div>
          <div style={{fontSize:11,color:'#5a7080'}}>
            {new Date(asset.created_at).toLocaleDateString()}
          </div>
        </div>
      ) : (
        <div style={{background:'rgba(255,255,255,.03)',border:'1px dashed #1e2a38',
                     borderRadius:8,padding:12,marginBottom:12,
                     fontSize:12,color:'#5a7080',textAlign:'center'}}>
          No {label.toLowerCase()} uploaded yet
        </div>
      )}

      <label style={{display:'flex',alignItems:'center',justifyContent:'center',gap:6,
                     padding:'10px',borderRadius:8,cursor:'pointer',
                     background:'rgba(0,229,255,.08)',border:'1px solid rgba(0,229,255,.2)',
                     color:'#00e5ff',fontSize:13,fontWeight:600,transition:'all .2s'}}
             onMouseEnter={e=>e.currentTarget.style.background='rgba(0,229,255,.15)'}
             onMouseLeave={e=>e.currentTarget.style.background='rgba(0,229,255,.08)'}>
        <input type="file" accept={accept} style={{display:'none'}} onChange={handle} />
        <Upload size={14} />
        {uploading ? 'Uploading...' : asset ? 'Replace' : 'Upload'}
      </label>
    </div>
  )
}

export default function Assets() {
  return (
    <Layout>
      <div style={{marginBottom:24}}>
        <h1 style={{fontFamily:'Bebas Neue',fontSize:40,letterSpacing:2}}>ASSETS</h1>
        <p style={{color:'#5a7080',fontSize:14}}>Upload your branding assets for use in jobs</p>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(280px,1fr))',gap:16}}>
        <AssetUpload type="logo"  label="Logo Watermark" accept="image/*"
                     icon={Image} />
        <AssetUpload type="intro" label="Intro Video"     accept="video/*"
                     icon={Film} />
        <AssetUpload type="outro" label="Outro Video"     accept="video/*"
                     icon={Film} />
      </div>

      <div style={{background:'#111820',border:'1px solid #1e2a38',borderRadius:12,
                   padding:20,marginTop:16}}>
        <h3 style={{fontFamily:'Bebas Neue',fontSize:18,letterSpacing:1,marginBottom:12}}>
          USAGE NOTES
        </h3>
        <div style={{display:'flex',flexDirection:'column',gap:8,fontSize:13,color:'#5a7080'}}>
          <div>🏷️ <strong style={{color:'#e8edf2'}}>Logo</strong> — PNG with transparency recommended. Placed top-left at 120px width.</div>
          <div>🎬 <strong style={{color:'#e8edf2'}}>Intro</strong> — Must be 9:16 ratio (1080×1920) for best results. Max 15 seconds.</div>
          <div>🎬 <strong style={{color:'#e8edf2'}}>Outro</strong> — Same as intro. Added after the recap ends.</div>
          <div>⚠️ Upload new files to replace existing ones. Only one of each type is stored.</div>
        </div>
      </div>
    </Layout>
  )
}
