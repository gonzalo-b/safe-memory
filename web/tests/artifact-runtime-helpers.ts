import {expect,type Page} from '@playwright/test';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
export const receiptDir=process.env.MEMORY_ARTIFACT_RECEIPTS||'/private/tmp/memory-artifacts-restart-receipts';
export async function signIn(page:Page){const username=process.env.MEMORY_TEST_USERNAME,password=process.env.MEMORY_TEST_PASSWORD;if(!username||!password)throw new Error('Supply explicitly synthetic runtime credentials.');await page.goto('/artifacts');await page.getByRole('textbox',{name:'Username'}).fill(username);await page.getByLabel('Password',{exact:true}).fill(password);await page.getByRole('button',{name:'Sign in',exact:true}).click();await expect(page.getByRole('heading',{name:'Private galleries',exact:true})).toBeVisible();const session=await(await page.request.get('/api/session')).json();expect(session.fixture).toBe(true);return {Origin:'http://127.0.0.1:8767','X-CSRF-Token':session.csrf_token};}
export async function ownerPost(page:Page,headers:Record<string,string>,path:string,data:object){const r=await page.request.post(path,{headers,data});expect(r.status()).toBe(200);return r.json();}
export interface RestartReceipt {artifact_id:string;title:string;connection_id:string;device_id:string;included:string;excluded:string;revision:number}
export function saveReceipt(project:string,data:RestartReceipt){mkdirSync(receiptDir,{recursive:true});writeFileSync(join(receiptDir,project+'.json'),JSON.stringify(data,null,2)+'\n',{mode:0o600});}
export function loadReceipt(project:string):RestartReceipt{return JSON.parse(readFileSync(join(receiptDir,project+'.json'),'utf8'));}
