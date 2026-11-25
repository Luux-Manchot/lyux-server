import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'

const PORT = Number(process.env.PORT || 80)
const DIST_DIR = path.resolve(process.env.DIST_DIR || '/app/dist')
const API_HOST = process.env.API_HOST || 'host.docker.internal'
const API_PORT = Number(process.env.API_PORT || 8000)

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
  '.ttf': 'font/ttf',
  '.eot': 'application/vnd.ms-fontobject',
}

function proxyToApi(req, res) {
  const proxyReq = http.request(
    {
      hostname: API_HOST,
      port: API_PORT,
      path: req.url,
      method: req.method,
      headers: { ...req.headers, host: `${API_HOST}:${API_PORT}` },
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode || 502, proxyRes.headers)
      proxyRes.pipe(res)
    },
  )
  proxyReq.on('error', (err) => {
    res.writeHead(502, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify({ detail: `API indisponible: ${err.message}` }))
  })
  req.pipe(proxyReq)
}

const server = http.createServer((req, res) => {
  const urlPath = (req.url || '/').split('?')[0]
  if (urlPath.startsWith('/api/') || urlPath.startsWith('/docs') || urlPath === '/openapi.json') {
    proxyToApi(req, res)
    return
  }

  const safePath = path.normalize(urlPath).replace(/^(\.\.[/\\])+/, '')
  let filePath = path.join(DIST_DIR, safePath === '/' ? 'index.html' : safePath)
  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    filePath = path.join(DIST_DIR, 'index.html')
  }

  const ext = path.extname(filePath).toLowerCase()
  res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' })
  fs.createReadStream(filePath).pipe(res)
})

server.listen(PORT, '0.0.0.0', () => {
  console.log(`lyux-admin-ui listening on :${PORT} (API -> ${API_HOST}:${API_PORT})`)
})
