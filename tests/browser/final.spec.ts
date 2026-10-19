import {test,expect} from '@playwright/test';
import {errorMessage} from '../../src/i18n';

test('deterministic quota outcome shows localized recovery, without a model response',async({page})=>{
  // This is a UI fault injection only, never live Gemini acceptance.
  await page.route('**/api/state',async route=>{
    const response=await route.fetch(),state=await response.json();
    state.agent.configured=true;
    await route.fulfill({response,json:state});
  });
  await page.route('**/api/chat',route=>route.fulfill({json:{text:'',status:'failed',code:'UPSTREAM_RATE_LIMITED',reason:'English-only provider detail must not leak into operational UI.'}}));
  await page.goto('/');await page.getByRole('button',{name:'Explore illustrative workspace',exact:true}).click();
  for(const lang of ['en','ru','kk'] as const){
    await page.getByTestId('language').selectOption(lang);
    await page.locator('.assistant input[maxlength="6000"]').fill('Quota UI fault check');
    await page.locator('.assistant > form button').click();
    await expect(page.getByText(errorMessage('UPSTREAM_RATE_LIMITED',lang),{exact:true})).toBeVisible();
    await expect(page.getByText('English-only provider detail must not leak into operational UI.',{exact:true})).toHaveCount(0);
  }
});
