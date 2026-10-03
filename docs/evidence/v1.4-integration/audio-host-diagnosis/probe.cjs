const { chromium } = require('/private/tmp/memory-v1-originals/web/node_modules/playwright');
const fs = require('node:fs');
const url='data:video/mp4;base64,'+fs.readFileSync('/private/tmp/memory-media-diagnosis/trace-video.mp4').toString('base64');
(async()=>{
for(const variant of [
 {name:'default',args:[],muted:false},
 {name:'element-muted',args:[],muted:true},
 {name:'disable-audio-output',args:['--disable-audio-output'],muted:false},
 {name:'audio-service-in-process',args:['--disable-features=AudioServiceOutOfProcess'],muted:false}
]){
 const browser=await chromium.launch({headless:true,args:variant.args});
 const page=await browser.newPage(); const cdp=await page.context().newCDPSession(page);const media=[];
 for(const type of ['playerErrorsRaised','playerMessagesLogged','playerPropertiesChanged'])cdp.on('Media.'+type,event=>media.push({type,...event}));
 await cdp.send('Media.enable');
 await page.setContent('<video controls playsinline></video>');
 await page.locator('video').evaluate((v,{url,muted})=>{v.src=url;v.muted=muted;return v.play();},{url,muted:variant.muted});
 const samples=[];
 for(let i=0;i<3;i++){
  await page.waitForTimeout(700);
  samples.push(await page.locator('video').evaluate(v=>({currentTime:v.currentTime,duration:v.duration,readyState:v.readyState,networkState:v.networkState,paused:v.paused,ended:v.ended,error:v.error?{code:v.error.code,message:v.error.message}:null,buffered:Array.from({length:v.buffered.length},(_,i)=>[v.buffered.start(i),v.buffered.end(i)]),audioDecoded:v.webkitAudioDecodedByteCount,videoDecoded:v.webkitVideoDecodedByteCount,frames:v.getVideoPlaybackQuality().totalVideoFrames})));
 }
 console.log(JSON.stringify({variant:variant.name,browser:browser.version(),samples,media}));
 await browser.close();
}
})().catch(error=>{console.error(error);process.exit(1)});
