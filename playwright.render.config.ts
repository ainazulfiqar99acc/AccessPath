import { defineConfig } from '@playwright/test';
const baseURL=process.env.ACCESSPATH_DEPLOYED_URL;
if(!baseURL)throw new Error('Set ACCESSPATH_DEPLOYED_URL to the approved actual Render URL. No deployment URL is assumed.');
const target=new URL(baseURL);
const localTest=process.env.ACCESSPATH_LOCAL_HOSTED_TEST==='true'&&target.hostname==='lvh.me'&&target.port==='9443';
if(target.protocol!=='https:'||target.username||target.password||target.pathname!=='/'||target.search||target.hash||(!target.hostname.endsWith('.onrender.com')&&!localTest))throw new Error('Use the approved HTTPS onrender.com origin, without a path or credentials.');
export default defineConfig({
  testDir:'./tests/render',fullyParallel:false,workers:1,timeout:240000,
  outputDir:'test-results/render/artifacts',
  use:{baseURL:target.origin,extraHTTPHeaders:{Origin:target.origin},ignoreHTTPSErrors:localTest,viewport:{width:1440,height:1000},trace:'retain-on-failure'},
  reporter:[['list'],['json',{outputFile:'test-results/render/results.json'}]],
});
