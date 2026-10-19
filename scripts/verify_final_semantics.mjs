/** One affected real-browser follow-up after clarifying student-report semantics. */
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {chromium,expect} from '@playwright/test';
const [url,stateFile]=process.argv.slice(2),local=url==='https://localhost:8017';
const out=`docs/evidence/final-semantics-${local?'local':'hosted'}-${Date.now().toString(36)}.json`;
const proof={checked_at:new Date().toISOString(),url,development_certificate_only:local,managed_agent_engine:false};
const browser=await chromium.launch({headless:true});
try{
 const context=await browser.newContext({baseURL:url,ignoreHTTPSErrors:local,storageState:stateFile});const page=await context.newPage();await page.goto('/');await page.locator('.live-access input[type=checkbox]').check();
 const pending=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/chat'&&r.request().method()==='POST',{timeout:110000});
 await page.locator('.assistant input[maxlength="6000"]').fill('Re-read the current Web project progress records. What are the logged and remaining minutes, what solver allocation do the current units require, and which of these figures are independently verified facts about completed work?');await page.locator('.assistant > form button').click();
 const response=await pending;proof.result=await response.json();assert.equal(response.status(),200);assert.equal(proof.result.status,'complete');assert(proof.result.tool_observations.some(t=>t.tool==='get_progress_summary'&&t.status==='observed'));assert(proof.result.text.includes('95')&&proof.result.text.includes('120'));assert(/student.report|self.report|reported|estimate/i.test(proof.result.text));
 await page.reload();await expect(page.locator('.live-access input[type=checkbox]')).not.toBeChecked();proof.restart_checkpoint=true;proof.passed=true;
}catch(error){proof.passed=false;proof.error=String(error);process.exitCode=1;}
finally{await fs.writeFile(out,JSON.stringify(proof,null,2));await browser.close();console.log(JSON.stringify({passed:proof.passed,evidence:out}));}
