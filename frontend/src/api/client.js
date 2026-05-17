import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const jobs = {
  list:       ()         => api.get('/jobs').then(r => r.data),
  get:        (id)       => api.get(`/jobs/${id}`).then(r => r.data),
  submit:     (data)     => api.post('/jobs', data).then(r => r.data),
  uploadFile: (formData) => api.post('/jobs/upload', formData,
                              { headers: {'Content-Type':'multipart/form-data'}
                            }).then(r => r.data),
  delete:     (id)       => api.delete(`/jobs/${id}`).then(r => r.data),
  downloadUrl:(id, lang) => `/api/jobs/${id}/download?lang=${lang}`,
}

export const assets = {
  list:        ()     => api.get('/assets').then(r => r.data),
  uploadLogo:  (fd)   => api.post('/assets/logo',  fd, {headers:{'Content-Type':'multipart/form-data'}}).then(r=>r.data),
  uploadIntro: (fd)   => api.post('/assets/intro', fd, {headers:{'Content-Type':'multipart/form-data'}}).then(r=>r.data),
  uploadOutro: (fd)   => api.post('/assets/outro', fd, {headers:{'Content-Type':'multipart/form-data'}}).then(r=>r.data),
}

export default api
