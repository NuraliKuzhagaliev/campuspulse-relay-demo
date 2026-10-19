import {test,expect} from '@playwright/test';

test('public reset clears another open tab and renews its CSRF context',async({page,context,baseURL})=>{
  test.skip(!baseURL?.startsWith('https:') && process.env.RELAY_PUBLIC_MODE_TEST!=='1','Public two-tab cookie/reset contract; local public mode is covered by HTTP tests.');
  await page.goto('/');await page.getByRole('button',{name:'Enter public demo',exact:true}).click();
  const name='two-tab-'+Date.now()+'.md';
  await page.locator('input[type=file]').setInputFiles({name,mimeType:'text/markdown',buffer:Buffer.from('Assignment: Two-tab draft\nCourse: Isolation\nTerm: Test 2026\nAssignment ID: tabs\nDue: 2026-11-20T18:00:00+05:00\nEffort: 60 minutes')});
  await expect(page.locator('.source-list').getByText(name,{exact:true})).toBeVisible();
  const second=await context.newPage();await second.goto('/');await second.getByRole('button',{name:'Enter public demo',exact:true}).click();
  await second.getByRole('button',{name:'Evidence',exact:true}).click();
  await expect(second.locator('.source-list').getByText(name,{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Start a fresh demo',exact:true}).click();
  await second.bringToFront();
  await expect(second.locator('.source-list').getByText(name,{exact:true})).toHaveCount(0,{timeout:10000});
  await second.getByRole('button',{name:'Repair my week',exact:true}).click();
  await expect(second.getByRole('alert')).toContainText('Resolve the deadline conflict');
  await expect(second.getByRole('alert')).not.toContainText('workspace request protection');
  await second.close();
});
