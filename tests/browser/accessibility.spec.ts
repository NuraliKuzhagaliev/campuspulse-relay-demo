import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
test('primary states meet WCAG 2 AA automated rules',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Explore illustrative workspace'}).click();
 for(const view of ['My week','Evidence','Connections']){
  await page.getByRole('button',{name:view,exact:true}).click();
  const results=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(results.violations.map(v=>({id:v.id,description:v.description,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))).toEqual([]);
 }
});
