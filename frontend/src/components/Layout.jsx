import { Link, useLocation } from 'react-router-dom'
import { Film, Plus, Package, Zap } from 'lucide-react'

export default function Layout({ children }) {
  const loc = useLocation()
  const nav = [
    { to: '/',       label: 'Dashboard', icon: Film },
    { to: '/new',    label: 'New Job',   icon: Plus },
    { to: '/assets', label: 'Assets',    icon: Package },
  ]
  return (
    <div className="min-h-screen flex flex-col">
      {/* Nav */}
      <nav style={{background:'rgba(8,12,16,.95)',borderBottom:'1px solid #1e2a38',backdropFilter:'blur(12px)'}}
           className="sticky top-0 z-50 flex items-center justify-between px-6 h-14">
        <Link to="/" className="flex items-center gap-2">
          <Zap size={18} style={{color:'#00e5ff'}} />
          <span style={{fontFamily:'Bebas Neue',fontSize:22,letterSpacing:2,color:'#00e5ff'}}>
            MYANN<span style={{color:'#ff6b35'}}>AI</span>
          </span>
          <span style={{fontSize:10,color:'#5a7080',letterSpacing:1}} className="uppercase ml-1">Studio</span>
        </Link>
        <div className="flex gap-1">
          {nav.map(({to, label, icon: Icon}) => (
            <Link key={to} to={to}
              style={{
                color: loc.pathname === to ? '#00e5ff' : '#5a7080',
                background: loc.pathname === to ? 'rgba(0,229,255,.08)' : 'transparent',
                padding:'6px 14px', borderRadius:6, fontSize:13, fontWeight:500,
                textDecoration:'none', display:'flex', alignItems:'center', gap:6,
                transition:'all .2s'
              }}>
              <Icon size={14} /> {label}
            </Link>
          ))}
        </div>
      </nav>
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        {children}
      </main>
    </div>
  )
}
