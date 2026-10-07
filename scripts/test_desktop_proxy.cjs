/** Narrow global-agent override: exercise electron/get's actual proxy bootstrap API. */
const assert=require('node:assert/strict'),http=require('node:http'),{createRequire}=require('node:module'),{resolve}=require('node:path')
const desktop=createRequire(resolve(__dirname,'../apps/desktop/package.json'))
const builder=createRequire(desktop.resolve('app-builder-lib'))
const get=builder('@electron/get')
async function listen(server) {await new Promise(r=>server.listen(0,'127.0.0.1',r));return server.address().port}
async function request(url) {return new Promise((resolve,reject)=>http.get(url,response=>{let text='';response.on('data',c=>text+=c);response.on('end',()=>resolve(text))}).on('error',reject))}
;(async()=>{
  let proxied=0
  const proxy=http.createServer((req,res)=>{assert.equal(req.url,'http://calligraphy-release-smoke.invalid/');proxied++;res.end('proxy-ok')})
  const origin=http.createServer((_req,res)=>res.end('direct-ok'))
  const port=await listen(proxy),direct=await listen(origin)
  try {
    process.env.GLOBAL_AGENT_HTTP_PROXY=`http://127.0.0.1:${port}`
    process.env.GLOBAL_AGENT_NO_PROXY='127.0.0.1'
    get.initializeProxy()
    assert.equal(await request('http://calligraphy-release-smoke.invalid/'),'proxy-ok')
    assert.equal(await request(`http://127.0.0.1:${direct}`),'direct-ok')
    assert.equal(proxied,1)
    console.log('PASS: electron/get proxy bootstrap, HTTP proxy routing and NO_PROXY with pinned global-agent 4.1.3')
  } finally {proxy.close();origin.close()}
})().catch(error=>{console.error(error);process.exitCode=1})
