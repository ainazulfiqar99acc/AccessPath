import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs/promises';

async function checkA11y(page:Page,name:string){
  const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
  await fs.mkdir('test-results/accessibility',{recursive:true});
  await fs.writeFile(`test-results/accessibility/${name}.json`,JSON.stringify(result.violations,null,2));
  expect(result.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))).toEqual([]);
}
async function chooseScholarship(page:Page){
  await page.goto('/');
  await page.getByRole('article').filter({has:page.getByRole('heading',{name:'Student scholarship application'})}).getByRole('button').click();
  await expect(page.getByRole('heading',{name:'A form you can understand.'})).toBeVisible();
}
async function next(page:Page){await page.getByRole('button',{name:'Continue',exact:true}).click();}

test('workspace accessibility, mobile layout and reading preferences',async({page})=>{
  await page.goto('/');
  await expect(page.getByRole('article')).toHaveCount(3);
  await checkA11y(page,'workspace');
  await fs.mkdir('demo/assets/screenshots',{recursive:true});
  await page.screenshot({path:'demo/assets/screenshots/workspace.png',fullPage:true});
  await page.getByRole('button',{name:'Reading preferences'}).click();
  await page.getByLabel('Larger text').check();
  await page.getByLabel('High contrast').check();
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await checkA11y(page,'mobile-large-contrast');
  await page.screenshot({path:'demo/assets/screenshots/mobile.png',fullPage:true});
});

test('real local scholarship completion, explicit confirmation and deletion',async({page})=>{
  test.setTimeout(300000);
  let identifier='';
  try{
    await chooseScholarship(page);
    identifier=(await page.evaluate(()=>localStorage.getItem('accesspath-draft')))!;
    await page.getByRole('button',{name:'Explain this form'}).click();
    await expect(page.getByText('A little less jargon.')).toBeVisible({timeout:250000});
    await checkA11y(page,'analysis');
    await page.screenshot({path:'demo/assets/screenshots/analysis.png',fullPage:true});
    await page.getByRole('button',{name:'Get ready',exact:true}).click();
    await checkA11y(page,'checklist');
    await page.getByRole('main').getByRole('checkbox').nth(0).check();
    await page.getByRole('main').getByRole('checkbox').nth(1).check();
    await page.getByRole('button',{name:'I’m ready to begin'}).click();
    await next(page);
    await expect(page.locator('#answer-full_name')).toBeFocused();
    await expect(page.locator('#field-error')).not.toBeEmpty();
    await page.locator('#answer-full_name').fill('Synthetic Demo Student');await next(page);
    await page.locator('#answer-email').fill('student@example.org');await next(page);
    await page.locator('#answer-study_level').selectOption('undergraduate');await next(page);
    await page.locator('#answer-enrollment').fill('DEMO-2026');await next(page);
    await page.locator('#answer-has_support').selectOption('yes');await next(page);
    await expect(page.locator('#answer-support_details')).toBeVisible();
    await page.locator('#answer-support_details').fill('Synthetic Learning Fund');await next(page);
    await page.locator('#answer-statement').fill('I want to study accessible design and make everyday services easier to use.');
    await checkA11y(page,'wizard');
    await page.screenshot({path:'demo/assets/screenshots/wizard.png',fullPage:true});
    await next(page);
    await page.locator('#answer-declaration').check();
    await page.getByRole('button',{name:'Review my answers'}).click();
    await expect(page.getByRole('heading',{name:'Looking good. Take one last look.'})).toBeVisible();
    const send=page.getByRole('button',{name:'Confirm & submit demo'});
    await expect(send).toBeDisabled();
    await checkA11y(page,'review');
    await page.screenshot({path:'demo/assets/screenshots/review.png',fullPage:true});
    await page.getByRole('checkbox').check();
    await send.click();
    await expect(page.getByRole('heading',{name:'You made it through.'})).toBeVisible({timeout:45000});
    await expect(page.locator('.receipt strong')).toHaveText(/^AP-[A-F0-9]+$/);
    await checkA11y(page,'success');
    await page.screenshot({path:'demo/assets/screenshots/completed.png',fullPage:true});
    await page.getByRole('button',{name:'View activity & privacy'}).click();
    await expect(page.getByText('submission confirmed',{exact:true})).toBeVisible();
    await expect(page.locator('.event-list')).not.toContainText('student@example.org');
    await checkA11y(page,'activity');
    await page.getByRole('button',{name:'Delete local draft'}).click();
    await page.getByRole('button',{name:'Yes, delete this draft'}).click();
    await expect(page.getByRole('heading',{name:'A fresh start.'})).toBeVisible();
    identifier='';
  }finally{if(identifier)await page.request.delete(`/api/sessions/${identifier}`);}
});

test('keyboard-only completion, save/resume and optional field on community form',async({page})=>{
  let identifier='';
  async function tabTo(selector:string){
    for(let i=0;i<35;i++){
      if(await page.locator(selector).evaluate(el=>el===document.activeElement))return;
      await page.keyboard.press('Tab');
    }
    throw new Error(`Keyboard could not reach ${selector}`);
  }
  try{
    await page.goto('/');
    await expect(page.getByRole('article')).toHaveCount(3);
    await tabTo('.form-card:nth-child(2) .card-action');await page.keyboard.press('Enter');
    await expect(page.getByRole('heading',{name:'A form you can understand.'})).toBeVisible();
    identifier=(await page.evaluate(()=>localStorage.getItem('accesspath-draft')))!;
    await tabTo('.action-row .button-primary');await page.keyboard.press('Enter');
    await tabTo('.checklist-item input');await page.keyboard.press('Space');
    await tabTo('.action-row .button-primary');await page.keyboard.press('Enter');
    await tabTo('#answer-full_name');await page.keyboard.type('Synthetic Community Member');
    await tabTo('.wizard-actions .button-primary');await page.keyboard.press('Enter');
    await tabTo('#answer-email');await page.keyboard.type('member@example.org');
    await tabTo('.save-row button');await page.keyboard.press('Enter');
    await expect(page.getByRole('button',{name:'Resume form'})).toBeVisible();
    await page.reload();
    await expect(page.getByRole('button',{name:'Resume form'})).toBeVisible();
    await tabTo('.resume-card .button');await page.keyboard.press('Enter');
    await tabTo('.action-row .button-primary');await page.keyboard.press('Enter');
    await tabTo('.action-row .button-primary');await page.keyboard.press('Enter');
    await expect(page.locator('#answer-email')).toHaveValue('member@example.org');
    await tabTo('.wizard-actions .button-primary');await page.keyboard.press('Enter');
    await tabTo('#answer-workshop');await page.keyboard.press('ArrowDown');await page.keyboard.press('Tab');
    await tabTo('.wizard-actions .button-primary');await page.keyboard.press('Enter');
    await expect(page.locator('#answer-access_notes')).toBeVisible();
    await tabTo('.wizard-actions .button-primary');await page.keyboard.press('Enter');
    await tabTo('#answer-declaration');await page.keyboard.press('Space');
    await tabTo('.wizard-actions .button-primary');await page.keyboard.press('Enter');
    await expect(page.getByRole('heading',{name:'Looking good. Take one last look.'})).toBeVisible();
    await tabTo('.consent-panel input');await page.keyboard.press('Space');
    await tabTo('.consent-panel .button-primary');await page.keyboard.press('Enter');
    await expect(page.getByRole('heading',{name:'You made it through.'})).toBeVisible({timeout:45000});
  }finally{if(identifier)await page.request.delete(`/api/sessions/${identifier}`);}
});

test('household form uses actual portal constraints',async({request})=>{
  const created=await request.post('/api/sessions',{data:{form_id:'benefit'}});
  const d=await created.json();const url=`/api/sessions/${d.id}`;
  try{
    const values={full_name:'Synthetic Household Member',email:'household@example.org',household_size:'3',topic:'food',declaration:true};
    await request.put(`${url}/answers`,{data:{answers:values,checklist:['household_count']}});
    const p=await (await request.post(`${url}/prepare`)).json();
    const sent=await request.post(`${url}/submit`,{data:{confirmation:true,action_token:p.action_token}});
    expect(sent.ok()).toBe(true);expect((await sent.json()).receipt).toMatch(/^AP-/);
  }finally{await request.delete(url);}
});

test('a plain-text proxy failure shows a readable retry message and preserves the draft',async({page})=>{
  let identifier='';
  try{
    await chooseScholarship(page);
    identifier=(await page.evaluate(()=>localStorage.getItem('accesspath-draft')))!;
    await page.route('**/api/forms/scholarship/explain',route=>route.fulfill({status:504,contentType:'text/plain',body:'Gateway Timeout'}));
    await page.getByRole('button',{name:'Explain this form'}).click();
    await expect(page.getByRole('main').getByRole('alert')).toContainText('Your draft is still saved. Please retry.');
    await expect(page.getByRole('main').getByRole('alert')).not.toContainText('JSON');
    await expect(page.getByText('Original instructions available').first()).toBeVisible();
    expect((await page.request.get(`/api/sessions/${identifier}`)).ok()).toBe(true);
  }finally{if(identifier)await page.request.delete(`/api/sessions/${identifier}`);}
});
