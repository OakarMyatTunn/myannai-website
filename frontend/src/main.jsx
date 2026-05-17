import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import NewJob from './pages/NewJob'
import JobDetail from './pages/JobDetail'
import Assets from './pages/Assets'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <Routes>
      <Route path="/"            element={<Dashboard />} />
      <Route path="/new"         element={<NewJob />} />
      <Route path="/jobs/:id"    element={<JobDetail />} />
      <Route path="/assets"      element={<Assets />} />
    </Routes>
  </BrowserRouter>
)
