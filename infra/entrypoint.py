import os
import uvicorn
role=os.getenv('RELAY_SERVICE','gateway')
if role not in ('gateway','mcp'):
    raise RuntimeError('Unknown RELAY_SERVICE')
uvicorn.run('relay.mcp_server:app' if role=='mcp' else 'relay.gateway:app',host='0.0.0.0',port=int(os.getenv('PORT','8080')),workers=1)
