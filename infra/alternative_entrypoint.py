"""One free service/worker; internal MCP remains doubly authenticated."""
import os
import secrets
import uvicorn
port=int(os.getenv('PORT','10000'))
os.environ['RELAY_MCP_URL']=f'http://127.0.0.1:{port}/_relay/mcp/'
os.environ.setdefault('RELAY_CONTEXT_SECRET',secrets.token_hex(32))
os.environ.setdefault('RELAY_MCP_SERVICE_SECRET',secrets.token_hex(32))
uvicorn.run('relay.gateway:app',host='0.0.0.0',port=port,workers=1,access_log=False,proxy_headers=True)
