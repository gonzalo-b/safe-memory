import { expect, test, type Page } from '@playwright/test';
const asset='a'.repeat(32), tripId='b'.repeat(32),areaId='c'.repeat(32);
const fact={capture_time:'2024-02-29T23:30:00-03:00',capture_day:'2024-02-29',time_basis:'source_offset_local_day',location:{place:'<script>private place</script>',lat:35,lon:139},geography:{country_code:'JP',country:'Japan',city_id:'tokyo',city:'Tokyo'},media_type:'photo',owner_presence:'unknown',continuous_presence:false,evidence:{asset_id:asset,revision:1,connection_id:'d'.repeat(32)},people:[]};
const coverage={scope:'current_authorized_sample',whole_library:false,indexed_records:2,unknown_time_records:1,located_records:1,first_observed_day:'2024-02-29',last_observed_day:'2024-02-29',unindexed_current_records:1,excluded_records:null};
const baseTrip={trip_id:tripId,revision:1,state:'inferred',title:'Inferred trip',start:'2024-02-29',end:'2024-03-01',boundary_basis:'observed_local_dates_not_departure_or_return',kind:'overnight_candidate',observed_start:'2024-02-29',observed_end:'2024-03-01',observed_day_count:2,unknown_time_records:0,observed_dates:['2024-02-29','2024-03-01'],observed_dates_has_more:false,gaps:[],gaps_complete:true,continuous_presence:false,owner_presence_confirmed:false,evidence_count:1,evidence:[],lineage:[],definition_version:'indexed-photos-1'};
async function backend(page:Page){
  const state={status:200,mutationStatus:200,answerDelay:false,release:()=>{},posts:[] as {path:string;body:Record<string,unknown>;csrf:string}[],trip:{...baseTrip},tripVisible:true,areaSaved:false,generation:'synthetic-generation',areaConfirmed:false};
  await page.route('**/api/**',async route=>{
    const request=route.request(),url=new URL(request.url()),path=url.pathname;
    if(path==='/api/session')return route.fulfill({json:{owner:{id:'owner',display_name:'Fixture'},csrf_token:'synthetic-csrf',fixture:true}});
    if(path==='/api/debug')return route.fulfill({json:{version:'test',environment:'synthetic',health:{storage:'ok',audit:'ok'},operations:[],audit:[],fixture:true}});
    if(path==='/api/ingestion/progress')return route.fulfill({json:{scans:[]}});
    if(!path.startsWith('/api/knowledge/'))return route.fulfill({status:501,json:{}});
    if(request.method()==='POST')state.posts.push({path,body:request.postDataJSON(),csrf:request.headers()['x-csrf-token']});
    if(state.status!==200)return route.fulfill({status:state.status,json:{error:{message:'private path'}}});
    if(path==='/api/knowledge/catalog')return route.fulfill({json:{capabilities:['travel.where_on_date','travel.where_in_range','travel.where_in_year','travel.countries_visited','travel.cities_visited','photos.statistics','photos.on_this_day','travel.occasion_history','photos.records'],definition_version:'indexed-photos-1',generation:state.generation,coverage,people:'unavailable',status:'partial'}});
    if(path==='/api/knowledge/answer'){
      if(state.answerDelay)await new Promise<void>(resolve=>{state.release=resolve;});
      const body=request.postDataJSON();let data:unknown=[fact,{...fact,capture_time:null,capture_day:null,location:{},evidence:undefined}];
      if(body.capability==='travel.occasion_history')data=[{date:'2024-02-29',status:'observed',observation_count:1,observations:[fact]},{date:'2020-02-29',status:'unknown',observation_count:0,observations:[]}];
      if(body.capability==='photos.statistics')data={records:0,photos:0,videos:0,live_photos:0,unknown_time:0};
      return route.fulfill({json:{capability:body.capability,definition_version:'indexed-photos-1',generation:state.generation,status:body.capability==='photos.statistics'?'no_evidence':'partial',data,next_cursor:body.cursor?null:'synthetic-cursor',coverage,time_basis:'source_offset_local_day_unknown_if_instant_only',counting_rule:'one_current_authorized_asset',freshness:{built_at:1790985600,stale:true,source_check:'unknown'},markdown:'<script>never render raw</script>',limitations:[]}});
    }
    if(path==='/api/knowledge/evidence/'+asset)return route.fulfill({json:fact});
    if(path==='/api/knowledge/trips'&&request.method()==='GET')return route.fulfill({json:{data:state.tripVisible?[state.trip,{...state.trip,trip_id:'e'.repeat(32),title:'Second trip'}]:[],next_cursor:null}});
    if(path==='/api/knowledge/trips/'+tripId||path==='/api/knowledge/trips/'+'e'.repeat(32))return route.fulfill({json:{...state.trip,evidence:[fact],next_cursor:null}});
    if(path==='/api/knowledge/areas'&&request.method()==='GET')return route.fulfill({json:{data:[{id:areaId,revision:1,label:state.areaSaved?'Historical residence':'Suggested area (2024)',lat:35,lon:139,radius_km:15,start:'2024-01-01',end:'2025-01-01',confirmed:state.areaConfirmed?1:0}],next_cursor:null}});
    if(state.mutationStatus!==200)return route.fulfill({status:state.mutationStatus,json:{}});
    if(path==='/api/knowledge/trips/correct'){
      const body=request.postDataJSON();state.trip.revision++;state.trip.state='confirmed';if(body.payload?.title)state.trip.title=body.payload.title;
      if(body.action==='dismiss')state.tripVisible=false;
      return route.fulfill({json:{operation_id:'operation',trip_ids:[tripId],revisions:{[tripId]:state.trip.revision},status:'applied'}});
    }
    if(path==='/api/knowledge/areas'){state.areaSaved=true;state.areaConfirmed=request.postDataJSON().area.confirmed;return route.fulfill({json:{area_id:areaId,revision:2}});}
    if(path==='/api/knowledge/rebuild'){state.generation='rebuilt-generation';return route.fulfill({json:{generation:state.generation,definition_version:'indexed-photos-1',built_at:1790985600}});}
    return route.fulfill({status:404,json:{}});
  });return state;
}
test('knowledge queries preserve unknown dates, explicit evidence and bounded POST pagination',async({page},info)=>{
  const state=await backend(page);await page.goto('/blocks');
  await page.getByLabel('Local date',{exact:true}).fill('2024-02-29');await page.getByRole('button',{name:'Run query',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Unknown local day',exact:true})).toBeVisible();await expect(page.getByText('Owner presence unknown',{exact:true}).first()).toBeVisible();
  await expect(page.getByText('<script>private place</script>',{exact:true}).first()).toBeVisible();expect(await page.locator('script').filter({hasText:'never render raw'}).count()).toBe(0);
  expect(state.posts[0].body).toMatchObject({capability:'travel.where_on_date',params:{date:'2024-02-29'}});
  await page.getByRole('button',{name:'Inspect evidence',exact:true}).first().click();await expect(page.getByRole('region',{name:'Evidence details'})).toContainText('2024-02-29T23:30:00-03:00');await page.getByRole('button',{name:'Close evidence'}).click();
  await page.getByRole('button',{name:'Next result page'}).click();expect(state.posts.at(-1)?.body.cursor).toBe('synthetic-cursor');
  await page.setViewportSize({width:320,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:info.outputPath('knowledge.png'),fullPage:true});
});
test('occasion query keeps exact leap default and unknown calendar years while zero is limited',async({page})=>{
  const state=await backend(page);await page.goto('/blocks');await page.getByRole('button',{name:'Occasion history',exact:true}).click();
  await page.getByLabel('Month and day',{exact:true}).fill('02-29');await page.getByLabel('Occurrences',{exact:true}).fill('2');await page.getByLabel('As of local date',{exact:true}).fill('2026-10-02');await page.getByRole('button',{name:'Run query',exact:true}).click();
  await expect(page.getByText('2020-02-29',{exact:true})).toBeVisible();await expect(page.getByText('Unknown occurrence',{exact:true})).toBeVisible();expect(state.posts.at(-1)?.body.params).toMatchObject({month_day:'02-29',count:2,as_of:'2026-10-02',leap_day_policy:'leap_years_only'});
  await page.getByRole('button',{name:'Photo statistics',exact:true}).click();await page.getByRole('button',{name:'Run query',exact:true}).click();await expect(page.getByText('No admissible evidence for this query.',{exact:true})).toBeVisible();await expect(page.getByText('A zero here does not mean your whole library has no records.',{exact:true})).toBeVisible();
});
test('query refresh clears old private results on loading failure and session loss',async({page})=>{
  const state=await backend(page);await page.goto('/blocks');await page.getByLabel('Local date',{exact:true}).fill('2024-02-29');await page.getByRole('button',{name:'Run query',exact:true}).click();await expect(page.getByText('<script>private place</script>',{exact:true}).first()).toBeVisible();
  state.answerDelay=true;await page.getByRole('button',{name:'Run query',exact:true}).click();await expect(page.getByText('Running query…',{exact:true})).toBeVisible();await expect(page.getByText('<script>private place</script>',{exact:true})).toHaveCount(0);state.release();state.answerDelay=false;
  await expect(page.getByRole('button',{name:'Run query',exact:true})).toBeEnabled();state.status=503;await page.getByRole('button',{name:'Run query',exact:true}).click();await expect(page.getByRole('main').getByRole('alert')).toContainText('temporarily unavailable');await expect(page.getByText('<script>private place</script>',{exact:true})).toHaveCount(0);
  state.status=401;await page.getByRole('button',{name:'Run query',exact:true}).click();await expect(page.getByRole('heading',{name:'Welcome to Memory'})).toBeVisible();
});
test('trip correction forms send current revisions and real refresh drives results',async({page})=>{
  const state=await backend(page);await page.goto('/trips');await page.getByRole('button',{name:'Open trip Inferred trip',exact:true}).click();await page.getByRole('button',{name:'Rename trip',exact:true}).click();await page.getByLabel('Trip title',{exact:true}).fill('Owner title');await page.getByRole('button',{name:'Save trip change',exact:true}).click();
  await expect(page.getByText('Trip change saved.',{exact:true})).toBeVisible();expect(state.posts.at(-1)?.body).toMatchObject({action:'rename',trip_id:tripId,expected_revision:1,payload:{title:'Owner title'}});expect(state.posts.at(-1)?.csrf).toBe('synthetic-csrf');
  await page.getByRole('button',{name:'Open trip Owner title',exact:true}).click();await page.getByRole('button',{name:'Edit dates',exact:true}).click();await page.getByLabel('Trip start',{exact:true}).fill('2024-02-28');await page.getByLabel('Trip end',{exact:true}).fill('2024-03-02');await page.getByRole('button',{name:'Save trip change',exact:true}).click();expect(state.posts.at(-1)?.body).toMatchObject({action:'dates',expected_revision:2,payload:{start:'2024-02-28',end:'2024-03-02'}});
  await page.getByRole('button',{name:'Open trip Owner title',exact:true}).click();await page.getByRole('button',{name:'Confirm trip',exact:true}).click();await page.getByRole('button',{name:'Save trip change',exact:true}).click();expect(state.posts.at(-1)?.body.action).toBe('confirm');
});
test('manual merge split and dismiss are explicit owner corrections',async({page})=>{
  const state=await backend(page);await page.goto('/trips');await page.getByRole('button',{name:'Add manual trip',exact:true}).click();await page.getByLabel('Trip title',{exact:true}).fill('Manual visit');await page.getByLabel('Trip start',{exact:true}).fill('2024-02-29');await page.getByLabel('Trip end',{exact:true}).fill('2024-03-01');await page.getByRole('button',{name:'Save trip change',exact:true}).click();expect(state.posts.at(-1)?.body.action).toBe('manual');
  await page.getByRole('checkbox',{name:'Select Manual visit',exact:true}).click();await page.getByRole('checkbox',{name:'Select Second trip',exact:true}).click();await page.getByRole('button',{name:'Merge selected trips',exact:true}).click();await page.getByRole('button',{name:'Save trip change',exact:true}).click();expect(state.posts.at(-1)?.body.action).toBe('merge');
  await page.getByRole('button',{name:'Open trip Manual visit',exact:true}).click();await page.getByRole('button',{name:'Split trip',exact:true}).click();await page.getByLabel('First date of second trip',{exact:true}).fill('2024-03-01');await page.getByRole('button',{name:'Save trip change',exact:true}).click();expect(state.posts.at(-1)?.body.action).toBe('split');
  await page.getByRole('button',{name:'Open trip Manual visit',exact:true}).click();await page.getByRole('button',{name:'Dismiss trip',exact:true}).click();await page.getByRole('button',{name:'Save trip change',exact:true}).click();await expect(page.getByText('No currently admissible trips.',{exact:true})).toBeVisible();expect(state.posts.at(-1)?.body.action).toBe('dismiss');
});
test('historical areas require explicit confirmation and failed mutation never claims success',async({page},info)=>{
  const state=await backend(page);await page.goto('/trips');await page.getByRole('button',{name:'Historical areas',exact:true}).click();await expect(page.getByText('Inferred suggestion',{exact:true})).toBeVisible();await page.getByRole('button',{name:'Review area Suggested area (2024)',exact:true}).click();await page.getByLabel('Area label',{exact:true}).fill('Historical residence');await page.getByRole('checkbox',{name:'Use this confirmed historical area for commuting',exact:true}).click();
  state.mutationStatus=409;await page.getByRole('button',{name:'Save historical area',exact:true}).click();await expect(page.getByRole('main').getByRole('alert')).toContainText('changed');await expect(page.getByText('Historical area saved.',{exact:true})).toHaveCount(0);
  state.mutationStatus=200;await page.getByRole('button',{name:'Refresh areas',exact:true}).click();await page.getByRole('button',{name:'Review area Suggested area (2024)',exact:true}).click();await page.getByLabel('Area label',{exact:true}).fill('Historical residence');await page.getByRole('checkbox',{name:'Use this confirmed historical area for commuting',exact:true}).click();await page.getByRole('button',{name:'Save historical area',exact:true}).click();expect(state.posts.at(-1)?.body).toMatchObject({area_id:areaId,expected_revision:1,area:{confirmed:true}});await expect(page.getByText('Historical area saved.',{exact:true})).toBeVisible();
  await page.setViewportSize({width:320,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:info.outputPath('historical-areas.png'),fullPage:true});
});
test('Debug rebuild uses CSRF and only acknowledges an actual generation receipt',async({page})=>{
  const state=await backend(page);await page.goto('/debug');const panel=page.getByRole('region',{name:'Photos knowledge'});await panel.getByRole('button',{name:'Rebuild Photos knowledge',exact:true}).click();await expect(panel.getByText('Photos knowledge rebuilt.',{exact:true})).toBeVisible();await expect(panel.getByText('rebuilt-generation',{exact:true})).toBeVisible();expect(state.posts.at(-1)?.csrf).toBe('synthetic-csrf');expect(state.posts.at(-1)?.body.request_key).toBeTruthy();
});

test('denied evidence inspection clears the prior answer and its cached coverage',async({page})=>{
  const state=await backend(page);await page.goto('/blocks');await page.getByLabel('Local date',{exact:true}).fill('2024-02-29');await page.getByRole('button',{name:'Run query',exact:true}).click();await expect(page.getByText('<script>private place</script>',{exact:true})).toBeVisible();
  state.status=403;await page.getByRole('button',{name:'Inspect evidence',exact:true}).click();await expect(page.getByRole('region',{name:'Evidence details'}).getByRole('alert')).toContainText('not permitted');await expect(page.getByText('<script>private place</script>',{exact:true})).toHaveCount(0);await expect(page.getByText('Indexed records',{exact:true})).toHaveCount(0);
});
