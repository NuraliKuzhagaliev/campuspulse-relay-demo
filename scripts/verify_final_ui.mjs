/** UI-only acceptance of the private alternative route; makes no inference requests. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {chromium,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
const [url,invitationFile,existingState]=process.argv.slice(2);
assert(url?.startsWith('https://') && invitationFile);
const local=url==='https://localhost:8017';
const privateData=JSON.parse(await fs.readFile(invitationFile,'utf8'));
const id=Date.now().toString(36),folder=path.join(process.cwd(),'.local/final-ui',id);
await fs.mkdir(folder,{recursive:true});
const out=path.join(process.cwd(),'docs/evidence',`final-ui-${local?'local':'hosted'}-${id}.json`);
const proof={checked_at:new Date().toISOString(),url,development_certificate_only:local,inference_calls:0,checks:{}};
const browser=await chromium.launch({headless:true});
try {
 const context=await browser.newContext({baseURL:url,ignoreHTTPSErrors:local,viewport:{width:1440,height:900},...(existingState==='--state'?{storageState:invitationFile}:{})});
 const page=await context.newPage();await page.goto('/');
 if(existingState!=='--state'){
 await page.getByText('Use a private AI invitation',{exact:true}).click();
 await page.getByLabel('Owner-issued one-use judge invitation').fill(privateData.invitations[0].token);
 await Promise.all([page.waitForNavigation({waitUntil:'load'}),page.getByRole('button',{name:'Open isolated demo',exact:true}).click()]);
 }
 await expect(page.locator('.live-access input[type=checkbox]')).toBeVisible();
 await context.storageState({path:path.join(folder,'private-storage-state.json')});
 let modelCalls=0;page.on('request',r=>{if(new URL(r.url()).pathname==='/api/chat')modelCalls++;});
 const layouts=[];
 for(const lang of ['en','ru','kk'])for(const width of [390,768,1280,1440]){
   await page.getByTestId('language').selectOption(lang);await page.setViewportSize({width,height:900});
   const fits=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1);
   layouts.push({lang,width,fits});assert(fits);
 }
 proof.checks.layouts=layouts;
 await page.getByTestId('language').selectOption('en');await page.setViewportSize({width:1440,height:900});
 const report=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa']).analyze();
 proof.checks.axe={violations:report.violations.map(v=>({id:v.id,impact:v.impact,description:v.description,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),passes:report.passes.length};
 await page.screenshot({path:path.join(folder,'private-ui.png'),fullPage:true});
 await page.locator('.live-access input[type=checkbox]').check();await page.reload();
 await expect(page.locator('.live-access input[type=checkbox]')).not.toBeChecked();
 proof.checks.consent_reset_after_reload=true;
 assert.equal((await page.request.post('/internal/ai-invitations',{data:{count:2,hours:2,timestamp:Math.floor(Date.now()/1000),nonce:'a'.repeat(32)}})).status(),403);
 assert.equal((await page.request.post('/_relay/mcp/',{data:{}})).status(),403);
 proof.checks.unsigned_operator_and_mcp_denied=true;
 assert.equal(modelCalls,0);assert.equal(report.violations.length,0);
 proof.passed=true;
} catch(error){proof.passed=false;proof.error=String(error);process.exitCode=1;}
finally{await fs.writeFile(out,JSON.stringify(proof,null,2));await browser.close();console.log(JSON.stringify({passed:proof.passed,evidence:out}));}
