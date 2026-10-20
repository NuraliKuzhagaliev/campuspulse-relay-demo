/** Dedicated synthetic public workspace screenshots. Zero model/Google calls. */
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {chromium,expect as baseExpect} from '@playwright/test';
const expect=baseExpect.configure({timeout:20000}),base='https://campuspulse-relay-demo.onrender.com',folder='docs/images/presentation-0.5.2';
await fs.mkdir(folder,{recursive:true});
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1600,height:1050},locale:'ru-RU',timezoneId:'Asia/Almaty',ignoreHTTPSErrors:false});
const p=await context.newPage();const evidence={version:'0.5.2',url:base,synthetic:true,model_calls:0,google_writes:0,screenshots:[],passed:false};
async function idle(){await expect(p.locator('.working')).toHaveCount(0);}
async function shot(name,locator){await idle();await locator.screenshot({path:folder+'/'+name+'.png'});evidence.screenshots.push(name+'.png');}
async function nav(name){await p.getByRole('button',{name,exact:true}).click();await idle();}
try{
 await p.goto(base,{timeout:60000});await expect(p.getByTestId('language')).toBeVisible();const health=await (await p.request.get(base+'/api/health')).json();assert.equal(health.version,'0.5.2');evidence.deployed_commit=health.deployed_commit;
 const entry=p.getByRole('button',{name:'Enter public demo',exact:true});if(await entry.isVisible())await entry.click();
 const load=p.waitForEvent('domcontentloaded');await p.getByRole('button',{name:'Open example',exact:true}).click();await load;
 await expect(p.getByTestId('language')).toBeVisible();
 // English UI keeps exact capture selectors stable; deck explanations are Russian.
 await p.getByTestId('language').selectOption('en');await nav('Evidence');
 await shot('conflict',p.locator('.conflict-card').first());
 const session=await (await p.request.get(base+'/api/session')).json();
 let state=await (await p.request.get(base+'/api/state')).json();
 const conflict=state.conflicts[0];
 const resolve=await p.request.post(base+'/api/conflicts/'+conflict.id+'/resolve',{headers:{'Origin':base,'X-Relay-CSRF':session.csrf},data:{fact_id:[...conflict.facts].sort((a,b)=>a.value.localeCompare(b.value))[0].id}});assert(resolve.ok());
 await p.reload();await nav('My week');await p.getByRole('button',{name:'Repair my week',exact:true}).click();await idle();
 state=await (await p.request.get(base+'/api/state')).json();assert(state.plan.feasible);evidence.plan={required:state.plan.required_minutes,capacity:state.plan.capacity_minutes};
 const timeline=p.locator('.timeline-card').first();
 if(await timeline.count())await shot('week',timeline);else{await p.getByText('A little structure. A lot more clarity.',{exact:true}).scrollIntoViewIfNeeded();await shot('week',p.locator('body'));}
 await nav('Recovery');await shot('plan-summary',p.locator('.plan-summary'));
 await p.getByRole('button',{name:'Lose Wednesday afternoon',exact:true}).click();await idle();await shot('what-if',p.locator('.plan-summary'));
 await p.getByRole('button',{name:'Return to baseline',exact:true}).click();await p.getByRole('button',{name:'Review calendar actions',exact:true}).click();await idle();
 await expect(p.getByRole('button',{name:'Approve illustrative local actions',exact:true})).toBeVisible();
 const dialog=p.getByRole('dialog');await dialog.scrollIntoViewIfNeeded();const box=await dialog.boundingBox(),digest=await dialog.locator('.digest').boundingBox();assert(box&&digest);await p.screenshot({path:folder+'/calendar-preview.png',clip:{x:box.x,y:box.y,width:box.width,height:digest.y-box.y-8}});evidence.screenshots.push('calendar-preview.png');
 await p.getByRole('button',{name:'Approve illustrative local actions',exact:true}).click();await idle();
 await shot('illustrative-receipt',p.locator('.receipt').first());
 await nav('Evidence');await p.getByRole('button',{name:/Progress & continuity/}).click();
 const progress=p.getByTestId('progress-panel');await progress.getByLabel('Actual minutes to record',{exact:true}).fill('45');await progress.getByRole('button',{name:'Log work manually',exact:true}).click();await expect(progress.locator('.effort-comparison')).toContainText('45');await progress.getByLabel('Remaining minutes',{exact:true}).fill('95');await progress.getByRole('button',{name:'Save remaining estimate',exact:true}).click();await expect(progress.locator('.effort-comparison')).toContainText('95');await shot('progress',progress);await shot('progress-numbers',progress.locator('.effort-comparison'));
 await p.getByRole('button',{name:'Workspace Passport',exact:true}).click();await shot('passport',p.getByTestId('passport-panel'));
 // A separate own-data workspace supplies a current-version review capture.
 const ownload=p.waitForEvent('domcontentloaded');await p.getByRole('button',{name:'Use my own data',exact:true}).click();await ownload;
 await p.locator('input[type=file]').first().setInputFiles({name:'judge-new-document.md',mimeType:'text/markdown',buffer:Buffer.from('Assignment: Urban sound map\nCourse: Field observations\nTerm: Autumn 2026\nAssignment ID: noise-73\nDue: 2026-10-23T19:00:00+05:00\nEffort: 53 minutes\nRubric:\n- [ ] Describe three observation points\n- [ ] Include a measurement table\nThis is a synthetic presentation example.')});
 await idle();await expect(p.getByRole('button',{name:'Review extracted fields',exact:true})).toBeVisible();await p.getByRole('button',{name:'Review extracted fields',exact:true}).click();await idle();
 await shot('assignment-review',p.getByTestId('review-entity').first());
 await nav('My week');
 for(const language of ['en','ru','kk']){await p.getByTestId('language').selectOption(language);const planning=p.locator('.planning-context');if(!(await planning.evaluate(e=>e.open)))await planning.locator('summary').click();await planning.locator('.date-open').first().click();await shot('date-'+language,p.locator('.localized-calendar'));await p.keyboard.press('Escape');}
 evidence.passed=true;
}finally{
 await browser.close();await fs.writeFile('docs/evidence/presentation-captures-0.5.2.json',JSON.stringify(evidence,null,2)+'\n');
}
console.log(JSON.stringify(evidence));
