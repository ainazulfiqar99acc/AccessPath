import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
const base='http://127.0.0.1:3103';
const output='demo/assets';
await fs.mkdir(`${output}/video/raw`,{recursive:true});
await fs.mkdir(`${output}/screenshots`,{recursive:true});
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1920,height:1080},recordVideo:{dir:`${output}/video/raw`,size:{width:1920,height:1080}},reducedMotion:'reduce'});
const page=await context.newPage();
let draftId='';
const pause=async(seconds)=>page.waitForTimeout(seconds*1000);
const shot=async(name)=>page.screenshot({path:`${output}/screenshots/${name}.png`});
async function next(){await page.getByRole('button',{name:'Continue',exact:true}).click();await pause(3);}
try{
  await page.goto(base);await page.getByRole('article').first().waitFor();await pause(7);await shot('hero');
  await page.goto('http://127.0.0.1:9314/forms/scholarship');await pause(9);await shot('original-portal');
  await page.getByRole('button',{name:'Lodge application'}).click();await pause(3);
  await page.goto(base);await page.getByRole('article').filter({has:page.getByRole('heading',{name:'Student scholarship application'})}).getByRole('button').click();
  draftId=await page.evaluate(()=>localStorage.getItem('accesspath-draft'));
  await pause(4);
  // Ensure the demonstration includes fresh real inference, not a simulated response or a cache hit.
  const fresh=spawnSync(process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python',['-c','from backend.storage import db\nwith db() as c: c.execute("DELETE FROM explanations")'],{encoding:'utf8'});
  if(fresh.status!==0)throw new Error('Could not clear source-only explanation cache for recording.');
  await page.getByRole('button',{name:'Explain this form'}).click();
  await page.getByText('A little less jargon.').waitFor({timeout:260000});await pause(8);await shot('processing-evidence');
  await page.getByRole('button',{name:'Get ready',exact:true}).click();await pause(4);
  await page.getByRole('main').getByRole('checkbox').nth(0).check();await pause(1);
  await page.getByRole('main').getByRole('checkbox').nth(1).check();await pause(3);await shot('preparation');
  await page.getByRole('button',{name:'I’m ready to begin'}).click();await pause(3);
  // All values are explicitly synthetic demonstration inputs.
  await page.locator('#answer-full_name').pressSequentially('Synthetic Demo Student',{delay:65});await next();
  await page.locator('#answer-email').pressSequentially('student@example.org',{delay:65});await next();
  await page.locator('#answer-study_level').selectOption('undergraduate');await next();
  await page.locator('#answer-enrollment').pressSequentially('DEMO-2026',{delay:90});await next();
  await page.locator('#answer-has_support').selectOption('no');await next();
  await page.locator('#answer-statement').pressSequentially('I want to study accessible design and make everyday services easier to use.',{delay:40});await pause(4);await shot('guided-step');await next();
  await page.locator('#answer-declaration').check();await pause(3);
  await page.getByRole('button',{name:'Review my answers'}).click();await pause(7);await shot('confirmation');
  if(await page.getByRole('button',{name:'Confirm & submit demo'}).isEnabled())throw new Error('Consent gate must begin disabled.');
  await page.getByRole('checkbox').check();await pause(3);
  await page.getByRole('button',{name:'Confirm & submit demo'}).click();await page.getByRole('heading',{name:'You made it through.'}).waitFor({timeout:45000});await pause(7);await shot('outcome');
  await page.getByRole('button',{name:'View activity & privacy'}).click();await pause(6);await shot('privacy-activity');
  await page.getByRole('button',{name:'Delete local draft'}).click();await pause(2);
  await page.getByRole('button',{name:'Yes, delete this draft'}).click();await page.getByRole('heading',{name:'A fresh start.'}).waitFor();draftId='';await pause(4);
}finally{
  if(draftId)await page.request.delete(`${base}/api/sessions/${draftId}`).catch(()=>{});
  const video=page.video();await context.close();
  const raw=await video.path();await browser.close();
  const result=spawnSync('ffmpeg',['-y','-i',raw,'-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',`${output}/video/demo_silent.mp4`],{encoding:'utf8'});
  if(result.status!==0)throw new Error(`FFmpeg conversion failed: ${result.stderr.slice(-1000)}`);
  console.log(`Silent recording saved to ${output}/video/demo_silent.mp4`);
}
