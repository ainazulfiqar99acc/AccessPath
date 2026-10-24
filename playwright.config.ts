import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir:'./tests/e2e', fullyParallel:false, workers:1, timeout:90000,
  use:{baseURL:'http://127.0.0.1:3103',viewport:{width:1440,height:1000},trace:'retain-on-failure'},
  reporter:[['list'],['json',{outputFile:'test-results/results.json'}]],
});
