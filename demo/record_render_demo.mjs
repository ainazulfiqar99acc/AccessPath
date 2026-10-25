// Run only after the user approves and deploys the real public application.
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
const target=new URL(process.env.ACCESSPATH_DEPLOYED_URL||'about:blank');
if(target.protocol!=='https:'||!target.hostname.endsWith('.onrender.com')||target.username||target.password||target.pathname!=='/'||target.search||target.hash)throw new Error('Set ACCESSPATH_DEPLOYED_URL to the approved actual HTTPS onrender.com origin. No local/test-double recording is accepted.');
const base=target.origin,output='demo/assets/render';
await fs.mkdir(`${output}/video/raw`,{recursive:true});await fs.mkdir(`${output}/screenshots`,{recursive:true});
const browser=await chromium.launch();
const context=await browser.newContext({viewport:{width:1920,height:1080},extraHTTPHeaders:{Origin:base},reducedMotion:'reduce',recordVideo:{dir:`${output}/video/raw`,size:{width:1920,height:1080}}});
const started=performance.now(),markers={};
const mark=name=>{markers[name]=Number(((performance.now()-started)/1000).toFixed(3));};
const page=await context.newPage();
let id='',complete=false,inference,receipt;
const pause=seconds=>page.waitForTimeout(seconds*1000);
const shot=name=>page.screenshot({path:`${output}/screenshots/${name}.png`,fullPage:true});
async function sample(){await page.getByRole('button',{name:'Use sample answer',exact:true}).click();await pause(1);}
async function next(){
  const old=await page.locator('.wizard-card [id^="answer-"]').first().getAttribute('id');
  await page.getByRole('button',{name:'Continue',exact:true}).click();
  await page.waitForFunction(previous=>document.querySelector('.wizard-card [id^="answer-"]')?.id!==previous,old);
  await pause(2);
}
try{
  const health=await (await context.request.get(`${base}/api/health`)).json();
  if(health.deployment?.mode!=='hosted'||!health.deployment.synthetic_only||health.model.local)throw new Error('The target is not the actual hosted synthetic-demo configuration.');
  await page.goto(base);await page.getByRole('region',{name:'Synthetic Demo'}).waitFor();mark('opening');await pause(6);await shot('workspace');
  await page.goto(`${base}/forms/scholarship`);mark('original');await pause(7);await page.getByRole('button',{name:'Lodge application'}).click();await pause(2);await shot('original-portal');
  await page.goto(base);await page.getByLabel('I will use synthetic sample answers only.').check();await page.locator('.card-action').first().click();
  await page.getByRole('heading',{name:'A form you can understand.'}).waitFor();id=await page.evaluate(()=>localStorage.getItem('accesspath-draft'));mark('evidence');
  const pending=page.waitForResponse(r=>r.url().endsWith('/api/forms/scholarship/explain')&&r.request().method()==='POST',{timeout:150000});
  await page.getByRole('button',{name:'Explain this form'}).click();const response=await pending;
  if(!response.ok())throw new Error('Real hosted inference failed. No replacement explanation was inserted.');
  inference=await response.json();if(inference.provider!=='groq'||inference.local||inference.fields?.length!==8)throw new Error('Unexpected hosted inference evidence.');
  await page.getByText('A little less jargon.').waitFor();await pause(7);await shot('processing-evidence');
  await page.getByRole('button',{name:'Get ready',exact:true}).click();mark('preparation');await pause(2);
  for(const checkbox of await page.locator('.checklist-item input').all()){await checkbox.check();await pause(1);}
  await page.getByRole('button',{name:'I’m ready to begin'}).click();mark('questions');await pause(2);
  await sample();await next();await sample();await next();
  await page.locator('#answer-study_level').selectOption('undergraduate');await next();await sample();await next();
  await page.locator('#answer-has_support').selectOption('no');await next();mark('statement');await sample();await pause(4);await shot('guided-step');await next();
  await page.locator('#answer-declaration').check();await page.getByRole('button',{name:'Review my answers'}).click();
  await page.getByRole('heading',{name:'Looking good. Take one last look.'}).waitFor();mark('confirmation');await pause(6);await shot('confirmation');
  const send=page.getByRole('button',{name:'Confirm & submit demo'});if(await send.isEnabled())throw new Error('Consent gate started enabled.');
  await page.locator('.consent-panel input').check();await pause(2);await send.click();
  await page.getByRole('heading',{name:'You made it through.'}).waitFor({timeout:70000});receipt=await page.locator('.receipt strong').innerText();if(!/^AP-[A-F0-9]+$/.test(receipt))throw new Error('No genuine portal receipt.');
  mark('receipt');await pause(8);await shot('outcome');
  await page.getByRole('button',{name:'View activity & privacy'}).click();mark('privacy');await pause(5);await shot('privacy');
  await page.getByRole('button',{name:'Delete hosted draft'}).click();await page.getByRole('button',{name:'Yes, delete this draft'}).click();await page.getByRole('heading',{name:'A fresh start.'}).waitFor();id='';await pause(3);complete=true;
}finally{
  if(id)await context.request.delete(`${base}/api/sessions/${id}`).catch(()=>{});
  const video=page.video();await context.close();const raw=await video.path();await browser.close();
  if(!complete)throw new Error('Public recording failed. No completed hosted demo was claimed or replaced.');
  const candidate=`${output}/video/candidate_silent.mp4`;
  const encoded=spawnSync('ffmpeg',['-y','-i',raw,'-c:v','libx264','-preset','fast','-crf','21','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',candidate],{encoding:'utf8'});
  if(encoded.status!==0)throw new Error('Public recording conversion failed.');
  const decoded=spawnSync('ffmpeg',['-v','error','-i',candidate,'-f','null','-'],{encoding:'utf8'});if(decoded.status!==0)throw new Error('Public demo failed full decoding.');
  await fs.rename(candidate,`${output}/video/demo_silent.mp4`);
  await fs.writeFile(`${output}/recording-evidence.json`,JSON.stringify({recorded_at:new Date().toISOString(),public_url:base,synthetic_only:true,markers,receipt,deleted:true,inference,full_decode_passed:true,narration_status:'Pending generation from this actual hosted recording; the earlier local narration is not a hosted-privacy description.'},null,2));
  console.log(`Actual public recording: ${output}/video/demo_silent.mp4`);
}
