// Local development proxy only; no public TLS or native certificate acceptance claim.
const https = require('node:https');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const directory=path.join(__dirname,'../.local/final-integration/tls');
https.createServer({key:fs.readFileSync(path.join(directory,'key.pem')),cert:fs.readFileSync(path.join(directory,'cert.pem'))},(request,response)=>{
  if(!request.url.startsWith('/')) {response.writeHead(400);response.end();return;}
  const upstream=http.request({host:'127.0.0.1',port:8016,path:request.url,method:request.method,headers:{...request.headers,'x-forwarded-proto':'https'}}, result=>{
    response.writeHead(result.statusCode,result.headers); result.pipe(response);
  });
  upstream.on('error',()=>{if(!response.headersSent)response.writeHead(502);response.end('Local staging backend unavailable.');});
  request.pipe(upstream);
}).listen(8017,'127.0.0.1',()=>process.stdout.write('Loopback-only HTTPS staging: https://localhost:8017\n'));
