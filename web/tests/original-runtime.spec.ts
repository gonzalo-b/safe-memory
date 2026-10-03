/** Real owner request, native HTTP exact bytes and authenticated download; synthetic fixture only. */
import {createHash,randomBytes,randomUUID} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {expect,test} from '@playwright/test';
import {signIn,ownerPost} from './artifact-runtime-helpers';
test('original waits offline, retries failure, completes exact resources and denies after restriction',async({page},info)=>{
 const headers=await signIn(page),unique=randomUUID(),credential=randomBytes(32).toString('base64url');
 const intent=await ownerPost(page,headers,'/api/pairing/start',{});
 const c=await page.request.post('/api/device/claim',{data:{secret:intent.secret,device_name:'Synthetic original connector',library_id:'original-'+unique,credential}});expect(c.status()).toBe(200);const claim=await c.json();
 const binding=await ownerPost(page,headers,'/api/pairing/confirm',{claim_id:claim.claim_id,fingerprint:claim.fingerprint});
 const native=async(action:string,data:object={})=>{const r=await page.request.post('/api/device/'+action,{headers:{Authorization:'Bearer '+credential},data:{device_id:binding.device_id,...data}});expect(r.status()).toBe(200);return r.json();};
 try{
  await ownerPost(page,headers,'/api/sources/policy',{connection_id:binding.connection_id,include_hidden:true,include_shared_library:false,include_shared_albums:false});
  const row={native_id:'original-'+unique,source_revision:'synthetic-original-r1',media_type:'live',hidden:true,collection:'personal',capture_time:'2009-03-14T12:00:00-03:00',time_basis:'capture_offset',owner_presence:'unknown',source_modified:'2026-10-02T00:00:00Z',metadata:{fixture:true}};
  const run=await native('ingest/begin',{request_key:'sample',permission:'full',phase:'recent',selected_ids:[row.native_id]});await native('ingest/append',{run_id:run.run_id,batch_key:'one',sequence:0,checkpoint:'done',assets:[row]});await native('ingest/finish',{run_id:run.run_id});
  await page.goto('/photos');await page.getByRole('article').filter({has:page.getByText(row.native_id,{exact:true})}).getByRole('button',{name:'Open media',exact:true}).click();
  await page.getByRole('button',{name:'Refresh original status',exact:true}).click();await page.getByRole('button',{name:'Request original',exact:true}).click();await expect(page.getByText('Waiting for iPhone',{exact:true})).toBeVisible();
  let pending=await native('originals/pending');expect(pending.requests).toHaveLength(1);const requested=pending.requests[0];
  await native('originals/fail',{request_id:requested.request_id,reason:'icloud_unavailable'});await page.getByRole('button',{name:'Refresh original status'}).click();await expect(page.getByText('Original transfer failed',{exact:true})).toBeVisible();await page.getByRole('button',{name:'Retry original request'}).click();await expect(page.getByText('Waiting for iPhone',{exact:true})).toBeVisible();
  const bytes=[readFileSync(new URL('./fixtures/synthetic.jpg',import.meta.url)),readFileSync(new URL('./fixtures/synthetic.mp4',import.meta.url))];
  const resources=bytes.map((b,i)=>({resource_type:i?'paired_video':'photo',original_filename:i?'synthetic-original.mov':'synthetic-original.jpg',uniform_type_identifier:i?'com.apple.quicktime-movie':'public.jpeg',size:b.length,sha256:createHash('sha256').update(b).digest('hex')}));
  const begun=await native('originals/begin',{request_id:requested.request_id,resources});const components:string[]=[];
  for(let i=0;i<bytes.length;i++){
   const upload=begun.resources[i].upload_id,data=bytes[i].toString('base64');const first=await native('originals/chunk',{upload_id:upload,offset:0,data});expect(await native('originals/chunk',{upload_id:upload,offset:0,data})).toEqual(first);
   const done=await native('originals/complete',{upload_id:upload});expect(done.state).toBe(i===0?'transferring':'ready');components.push(done.component_id);
   if(i===0)expect((await page.request.get('/api/originals/components/'+done.component_id)).status()).toBe(409);
  }
  await ownerPost(page,headers,'/api/devices/revoke',{device_id:binding.device_id});
  await page.getByRole('button',{name:'Refresh original status'}).click();await expect(page.getByText('Original ready',{exact:true})).toBeVisible();
  for(let i=0;i<resources.length;i++){
   const downloadEvent=page.waitForEvent('download');await page.getByRole('button',{name:'Download '+resources[i].original_filename,exact:true}).click();const download=await downloadEvent;expect(download.suggestedFilename()).toBe(resources[i].original_filename);const path=await download.path();expect(path).toBeTruthy();expect(createHash('sha256').update(readFileSync(path!)).digest('hex')).toBe(resources[i].sha256);
   const ranged=await page.request.get('/api/originals/components/'+components[i],{headers:{Range:'bytes=0-15'}});expect(ranged.status()).toBe(206);expect(await ranged.body()).toEqual(bytes[i].subarray(0,16));expect(ranged.headers()['cache-control']).toBe('no-store');expect(ranged.headers()['content-disposition']).toMatch(/^attachment;/);
  }
  await page.screenshot({path:info.outputPath('real-original-ready.png'),fullPage:true,animations:'disabled'});
  await ownerPost(page,headers,'/api/sources/policy',{connection_id:binding.connection_id,include_hidden:false,include_shared_library:false,include_shared_albums:false});
  await page.getByRole('button',{name:'Refresh original status'}).click();await expect(page.getByText('Original ready',{exact:true})).toHaveCount(0);await expect(page.getByRole('button',{name:/Download synthetic-original/})).toHaveCount(0);expect((await page.request.get('/api/originals/components/'+components[0])).status()).toBe(404);
  await page.getByRole('button',{name:'Close viewer'}).click();await page.getByRole('button',{name:'Sign out',exact:true}).click();expect((await page.request.get('/api/originals/components/'+components[0])).status()).toBe(401);
 }finally{
  // Cleanup preserves every record and byte. If the session still exists, withdraw fixture consent.
  const session=await page.request.get('/api/session');if(session.status()===200){const auth=await session.json();const cleanup={Origin:'http://127.0.0.1:8767','X-CSRF-Token':auth.csrf_token};await page.request.post('/api/sources/policy',{headers:cleanup,data:{connection_id:binding.connection_id,include_hidden:false,include_shared_library:false,include_shared_albums:false}});await page.request.post('/api/devices/revoke',{headers:cleanup,data:{device_id:binding.device_id}});}
 }
});
