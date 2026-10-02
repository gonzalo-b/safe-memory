/* Presentation only. The caller supplies already-authorized content. */
const routes = Object.freeze({
  overview: ['Overview', 'home'], sources: ['Sources', 'plug'],
  photos: ['Memory', 'grid'], blocks: ['Blocks', 'block'], trips: ['Trips', 'map-pin'],
  artifacts: ['Artifacts', 'layers'], audit: ['Access history', 'pulse'],
  debug: ['Debug', 'terminal'], settings: ['Settings', 'settings'], more: ['More', 'more-horizontal'],
});
const primary = ['overview', 'sources', 'photos', 'artifacts'];
const secondary = ['blocks', 'trips', 'audit', 'debug', 'settings'];
const mobile = ['overview', 'photos', 'artifacts', 'more'];
function element(tag, className, text) {
  const node = document.createElement(tag); node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function icon(name) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.classList.add('m-icon'); svg.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS(svg.namespaceURI, 'use');
  use.setAttribute('href', new URL(`./memory-ds/sprite.svg#m-i-${name}`, import.meta.url).href);
  svg.append(use); return svg;
}
function link(id, className) {
  const [title, symbol] = routes[id]; const a=element('a', className);
  a.href=`#${id}`; a.setAttribute('aria-label', title);
  a.append(icon(symbol), element('span', '', title)); return a;
}
export function mountShell(root, renderContent) {
  const abort=new AbortController(); const options={signal:abort.signal};
  const skip=element('a','memory-skip m-btn m-btn--primary','Skip to content');
  skip.href='#memory-content';
  const shell=element('div','m-shell');
  const sidebar=element('aside','m-sidebar m-shell__sidebar');
  sidebar.append(element('div','m-sidebar__brand','Memory'));
  const navigation=element('nav',''); navigation.setAttribute('aria-label','Primary navigation');
  primary.forEach(id=>navigation.append(link(id,'m-navitem')));
  navigation.append(element('div','m-sidebar__section','Photos Vault'));
  secondary.forEach(id=>navigation.append(link(id,'m-navitem'))); sidebar.append(navigation);
  const main=element('main','m-shell__main');
  const wash=element('div','m-wash m-wash--sm'); wash.setAttribute('aria-hidden','true');
  const top=element('header','m-topbar'); top.append(element('span','m-topbar__title','Memory'));
  const themeGroup=element('div','m-topbar__end m-seg memory-theme');
  themeGroup.setAttribute('role','group'); themeGroup.setAttribute('aria-label','Color theme');
  const themeButtons=[];
  const chooseTheme=(value)=>{
    if(value==='system')delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme=value;
    for(const button of themeButtons)button.setAttribute('aria-pressed',String(button.dataset.themeChoice===value));
    try { if(value==='system')localStorage.removeItem('m-theme');else localStorage.setItem('m-theme',value); } catch (_) {}
  };
  for(const [value,symbol] of [['system','monitor'],['light','sun'],['dark','moon']]){
    const button=element('button','m-seg__item');button.type='button';button.dataset.themeChoice=value;
    const label=value[0].toUpperCase()+value.slice(1)+' theme';
    button.setAttribute('aria-label',label);button.title=label;button.append(icon(symbol));
    button.setAttribute('aria-pressed',String(value===(document.documentElement.dataset.theme||'system')));
    button.addEventListener('click',()=>chooseTheme(value),options);
    themeButtons.push(button);themeGroup.append(button);
  }
  top.append(themeGroup);
  const body=element('div','m-shell__body memory-scroll');
  const content=element('div','m-shell__content');content.id='memory-content';content.tabIndex=-1;
  body.append(content);main.append(wash,top,body);shell.append(sidebar,main);
  const bottom=element('nav','m-bottomnav m-bottomnav--fixed memory-mobile-nav');
  bottom.setAttribute('aria-label','Primary navigation');mobile.forEach(id=>bottom.append(link(id,'m-bottomnav__item')));
  root.replaceChildren(skip,shell,bottom);
  skip.addEventListener('click',event=>{event.preventDefault();content.focus();},options);
  const render=(focus)=>{
    const route=location.hash.slice(1)||'overview';const entry=Object.hasOwn(routes,route) ? routes[route] : null;
    const title=entry ? entry[0] : 'Page not found';
    content.replaceChildren(); const heading=element('h1','m-page memory-heading',title);heading.tabIndex=-1;
    content.append(heading);document.title=`${title} · Memory`;
    for(const a of root.querySelectorAll('a[aria-current]'))a.removeAttribute('aria-current');
    for(const a of navigation.querySelectorAll('a'))if(a.hash===`#${route}`)a.setAttribute('aria-current','page');
    const mobileRoute=mobile.includes(route)?route:'more';
    for(const a of bottom.querySelectorAll('a'))if(a.hash===`#${mobileRoute}`)a.setAttribute('aria-current','page');
    if(!entry){content.append(element('p','m-body','Choose a destination from navigation.'));}
    else if(route==='more'){
      const more=element('nav','memory-more');more.setAttribute('aria-label','More destinations');
      ['sources',...secondary].forEach(id=>more.append(link(id,'m-navitem')));content.append(more);
    }else renderContent({route,content});
    body.scrollTop=0;if(focus)heading.focus();
  };
  window.addEventListener('hashchange',()=>render(true),options);render(false);
  return {destroy(){abort.abort();root.replaceChildren();}};
}
