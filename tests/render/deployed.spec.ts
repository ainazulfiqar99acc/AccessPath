import {test,expect,type Page} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs/promises';

async function scan(page:Page,name:string){
  const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
  await fs.mkdir('test-results/render/accessibility',{recursive:true});
  await fs.writeFile(`test-results/render/accessibility/${name}.json`,JSON.stringify(result.violations,null,2));
  expect(result.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))).toEqual([]);
}
async function ack(page:Page){await page.getByLabel('I will use synthetic sample answers only.').check();}
async function sample(page:Page){await page.getByRole('button',{name:'Use sample answer',exact:true}).click();}
async function next(page:Page){
  const previous=await page.locator('.wizard-card [id^="answer-"]').first().getAttribute('id');
  await page.getByRole('button',{name:'Continue',exact:true}).click();
  await expect(page.locator('.wizard-card [id^="answer-"]').first()).not.toHaveAttribute('id',previous!);
}
async function tabTo(page:Page,selector:string){
  for(let i=0;i<60;i++){
    if(await page.locator(selector).evaluate(el=>el===document.activeElement))return;
    await page.keyboard.press('Tab');
  }
  throw new Error(`Keyboard could not reach ${selector}`);
}

test('hosted scholarship: configured provider, isolated ownership, consent, portal receipt and deletion',async({page,browser,baseURL})=>{
  let id='';
  try{
    await page.goto('/');
    await expect(page.getByRole('region',{name:'Synthetic Demo'})).toBeVisible();
    await expect(page.locator('.card-action').first()).toBeDisabled();
    await ack(page);
    await page.locator('.card-action').first().click();
    await expect(page.getByRole('heading',{name:'A form you can understand.'})).toBeVisible();
    id=(await page.evaluate(()=>localStorage.getItem('accesspath-draft')))!;
    const response=page.waitForResponse(r=>r.url().endsWith('/api/forms/scholarship/explain')&&r.request().method()==='POST');
    await page.getByRole('button',{name:'Explain this form'}).click();
    const result=await response;
    expect(result.ok(),await result.text()).toBe(true);
    const ai=await result.json();expect(ai.provider).toBe('groq');expect(ai.local).toBe(false);expect(ai.fields).toHaveLength(8);
    await scan(page,'analysis');
    const stranger=await browser.newContext({baseURL,extraHTTPHeaders:{Origin:baseURL!},ignoreHTTPSErrors:process.env.ACCESSPATH_LOCAL_HOSTED_TEST==='true'});
    try{
      expect((await stranger.request.get(`/api/sessions/${id}`)).status()).toBe(404);
      expect((await stranger.request.delete(`/api/sessions/${id}`)).status()).toBe(404);
    }finally{await stranger.close();}
    await page.getByRole('button',{name:'Get ready',exact:true}).click();
    await page.locator('.checklist-item input').nth(0).check();await page.locator('.checklist-item input').nth(1).check();
    await page.getByRole('button',{name:'I’m ready to begin'}).click();
    await page.getByRole('button',{name:'Continue',exact:true}).click();await expect(page.locator('#field-error')).toContainText('sample answer');
    await sample(page);await expect(page.locator('#answer-full_name')).toHaveAttribute('readonly','');await next(page);
    await sample(page);await next(page);
    await page.locator('#answer-study_level').selectOption('undergraduate');await next(page);
    await sample(page);await next(page);
    await page.locator('#answer-has_support').selectOption('yes');await next(page);
    await sample(page);await next(page);
    await sample(page);await next(page);
    await page.locator('#answer-declaration').check();
    await page.getByRole('button',{name:'Review my answers'}).click();
    await expect(page.getByRole('heading',{name:'Looking good. Take one last look.'})).toBeVisible();
    const submit=page.getByRole('button',{name:'Confirm & submit demo'});await expect(submit).toBeDisabled();
    await scan(page,'review');
    await page.locator('.consent-panel input').check();await submit.click();
    await expect(page.getByRole('heading',{name:'You made it through.'})).toBeVisible({timeout:70000});
    await expect(page.locator('.receipt strong')).toHaveText(/^AP-[A-F0-9]+$/);
    await page.getByRole('button',{name:'View activity & privacy'}).click();
    await expect(page.getByRole('heading',{name:'Temporary hosted draft'})).toBeVisible();
    await expect(page.locator('.event-list')).not.toContainText('student@example.org');
    await page.getByRole('button',{name:'Delete hosted draft'}).click();await page.getByRole('button',{name:'Yes, delete this draft'}).click();
    await expect(page.getByRole('heading',{name:'A fresh start.'})).toBeVisible();
    expect((await page.request.get(`/api/sessions/${id}`)).status()).toBe(404);id='';
  }finally{if(id)await page.request.delete(`/api/sessions/${id}`);}
});

test('hosted keyboard-only community completion with save/resume',async({page})=>{
  let id='';
  try{
    await page.goto('/');await expect(page.locator('.card-action')).toHaveCount(3);
    await tabTo(page,'.synthetic-notice input');await page.keyboard.press('Space');
    await tabTo(page,'.form-card:nth-child(2) .card-action');await page.keyboard.press('Enter');
    await expect(page.getByRole('heading',{name:'A form you can understand.'})).toBeVisible();
    id=(await page.evaluate(()=>localStorage.getItem('accesspath-draft')))!;
    await tabTo(page,'.action-row .button-primary');await page.keyboard.press('Enter');
    await tabTo(page,'.checklist-item input');await page.keyboard.press('Space');
    await tabTo(page,'.action-row .button-primary');await page.keyboard.press('Enter');
    await tabTo(page,'.sample-answer');await page.keyboard.press('Enter');
    await tabTo(page,'.wizard-actions .button-primary');await page.keyboard.press('Enter');
    await expect(page.locator('#answer-email')).toBeVisible();
    await tabTo(page,'.sample-answer');await page.keyboard.press('Enter');
    await expect(page.locator('#answer-email')).toHaveValue('member@example.org');
    await tabTo(page,'.save-row button');await page.keyboard.press('Enter');
    await expect(page.getByRole('button',{name:'Resume form'})).toBeVisible();await page.reload();
    await expect(page.getByRole('button',{name:'Resume form'})).toBeVisible();
    await tabTo(page,'.resume-card .button');await page.keyboard.press('Enter');
    await tabTo(page,'.action-row .button-primary');await page.keyboard.press('Enter');
    await tabTo(page,'.action-row .button-primary');await page.keyboard.press('Enter');
    await expect(page.locator('#answer-email')).toHaveValue('member@example.org');
    await tabTo(page,'.wizard-actions .button-primary');await page.keyboard.press('Enter');
    await expect(page.locator('#answer-workshop')).toBeVisible();
    await tabTo(page,'#answer-workshop');await page.keyboard.press('ArrowDown');
    await tabTo(page,'.wizard-actions .button-primary');await page.keyboard.press('Enter');
    await expect(page.locator('#answer-access_notes')).toBeVisible();
    await tabTo(page,'.sample-answer');await page.keyboard.press('Enter');
    await expect(page.locator('#answer-access_notes')).not.toHaveValue('');
    await tabTo(page,'.clear-sample');await page.keyboard.press('Enter');
    await expect(page.locator('#answer-access_notes')).toHaveValue('');
    await tabTo(page,'.wizard-actions .button-primary');await page.keyboard.press('Enter');
    await tabTo(page,'#answer-declaration');await page.keyboard.press('Space');
    await tabTo(page,'.wizard-actions .button-primary');await page.keyboard.press('Enter');
    await expect(page.locator('.consent-panel input')).toBeVisible();
    await tabTo(page,'.consent-panel input');await page.keyboard.press('Space');
    await tabTo(page,'.consent-panel .button-primary');await page.keyboard.press('Enter');
    await expect(page.getByRole('heading',{name:'You made it through.'})).toBeVisible({timeout:70000});
  }finally{if(id)await page.request.delete(`/api/sessions/${id}`);}
});

test('hosted mobile reading controls and public original portal',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto('/');
  await expect(page.getByRole('region',{name:'Synthetic Demo'})).toBeVisible();
  await page.getByRole('button',{name:'Reading preferences'}).click();
  await page.getByLabel('Larger text').check();await page.getByLabel('High contrast').check();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await scan(page,'mobile-large-contrast');
  await page.goto('/forms/scholarship');await expect(page.getByRole('heading',{name:'Student scholarship application'})).toBeVisible();
  await expect(page.getByRole('complementary',{name:'Synthetic Demo'})).toBeVisible();
  await expect(page.locator('#full_name')).toBeVisible();
});
