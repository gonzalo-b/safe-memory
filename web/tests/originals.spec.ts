import {expect,test,type Page} from '@playwright/test';
const asset='a'.repeat(32),identity='b'.repeat(32),component='c'.repeat(32);
async function backend(page:Page){
 const state={value:null as Record<string,unknown>|null,status:200,downloadStatus:200,failSave:false,saves:[] as {request_key:string}[],downloads:0};
 const receipt=()=>({request_id:identity,asset_id:asset,revision:1,state:'waiting_for_device',error_code:null,resources:[]});
 await page.context().route('**/api/**',async route=>{const r=route.request(),path=new URL(r.url()).pathname;
  if(path==='/api/session')return route.fulfill({json:{owner:{id:'fixture',display_name:'Fixture'},csrf_token:'synthetic-csrf',fixture:true}});
  if(path==='/api/photos')return route.fulfill({json:{fixture:true,assets:[{id:asset,native_id:'Synthetic original',media_type:'photo',hidden:0,collection:'personal',capture_time:null,capture_day:null,time_basis:'unknown',owner_presence:'unknown',media_state:'not_transferred'}]}});
  if(path===`/api/photos/${asset}/media`)return route.fulfill({json:{asset_id:asset,state:'not_transferred',components:[]}});
  if(path===`/api/photos/${asset}/originals`||path===`/api/originals/${identity}/retry`){
   if(r.method()==='POST'){state.saves.push(r.postDataJSON());expect(r.headers()['x-csrf-token']).toBe('synthetic-csrf');state.value=receipt();if(state.failSave)return route.abort('failed');return route.fulfill({json:state.value});}
   return route.fulfill({status:state.status,json:state.status===200?{request:state.value}:{error:{message:'PRIVATE_TRACE'}}});
  }
  if(path===`/api/originals/components/${component}`){state.downloads++;return route.fulfill({status:state.downloadStatus,headers:{'Content-Type':'application/octet-stream','Content-Disposition':'attachment; filename="source.heic"'},body:r.method()==='HEAD'?'':'synthetic-original'});}
  return route.fulfill({status:501,json:{}});
 });
 await page.goto('/photos');await page.getByRole('button',{name:'Open media',exact:true}).click();return state;
}
test('explicit original request waits honestly and lost acknowledgement retries the same key',async({page})=>{
 const s=await backend(page);await page.getByRole('button',{name:'Refresh original status',exact:true}).click();await expect(page.getByText('No original has been requested for this revision.')).toBeVisible();s.failSave=true;
 await page.getByRole('button',{name:'Request original',exact:true}).click();await expect(page.getByRole('button',{name:'Retry same request'})).toBeVisible();s.failSave=false;await page.getByRole('button',{name:'Retry same request'}).click();await expect(page.getByText('Waiting for iPhone',{exact:true})).toBeVisible();expect(s.saves.length).toBe(2);expect(s.saves[0]).toEqual(s.saves[1]);await expect(page.getByText('The request is saved. This does not indicate that your iPhone is online.')).toBeVisible();
});
test('failed original retries explicitly and restricted status clears descriptors',async({page})=>{
 const s=await backend(page);s.value={request_id:identity,asset_id:asset,revision:1,state:'failed',error_code:'icloud_unavailable',resources:[]};await page.getByRole('button',{name:'Refresh original status'}).click();await page.getByRole('button',{name:'Retry original request'}).click();await expect(page.getByText('Waiting for iPhone',{exact:true})).toBeVisible();s.status=404;await page.getByRole('button',{name:'Refresh original status'}).click();await expect(page.getByText('Waiting for iPhone',{exact:true})).toHaveCount(0);await expect(page.getByText('PRIVATE_TRACE')).toHaveCount(0);await expect(page.getByRole('button',{name:/Download /})).toHaveCount(0);
});
test('ready original downloads privately and HEAD denial clears stale output',async({page},info)=>{
 const s=await backend(page);s.value={request_id:identity,asset_id:asset,revision:1,state:'ready',error_code:null,resources:[{ordinal:0,resource_type:'photo',original_filename:'source.heic',uniform_type_identifier:'public.heic',size:18,sha256:'d'.repeat(64),component_id:component}]};await page.getByRole('button',{name:'Refresh original status'}).click();await expect(page.getByText('Original ready',{exact:true})).toBeVisible();const download=page.waitForEvent('download');await page.getByRole('button',{name:'Download source.heic'}).click();const saved=await download;expect(saved.suggestedFilename()).toBe('source.heic');expect(new URL(saved.url()).pathname).toBe(`/api/originals/components/${component}`);expect(s.downloads).toBeGreaterThanOrEqual(1);/* Browser-managed download GET can bypass route interception; exact downloaded bytes are verified by original-runtime.spec.ts. */
 await page.setViewportSize({width:320,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:info.outputPath('original-ready-320.png'),fullPage:true,animations:'disabled'});
 s.downloadStatus=404;await page.getByRole('button',{name:'Download source.heic'}).click();await expect(page.getByRole('button',{name:'Download source.heic'})).toHaveCount(0);
});

test('authoritative refresh after changed revision starts a new request key',async({page})=>{
 const s=await backend(page);await page.getByRole('button',{name:'Refresh original status'}).click();s.failSave=true;await page.getByRole('button',{name:'Request original',exact:true}).click();await expect(page.getByRole('button',{name:'Retry same request'})).toBeVisible();const oldKey=s.saves[0].request_key;
 s.value=null;s.failSave=false;await page.getByRole('button',{name:'Refresh original status'}).click();await page.getByRole('button',{name:'Request original',exact:true}).click();await expect(page.getByText('Waiting for iPhone',{exact:true})).toBeVisible();expect(s.saves[1].request_key).not.toBe(oldKey);
});
