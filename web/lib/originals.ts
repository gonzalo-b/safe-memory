import { ApiError } from './api.ts';
export type OriginalState='waiting_for_device'|'transferring'|'failed'|'ready';
export interface OriginalResource {ordinal:number;resource_type:string;original_filename:string;uniform_type_identifier:string;size:number;sha256:string;component_id:string|null}
export interface OriginalRequest {request_id:string;asset_id:string;revision:number;state:OriginalState;error_code:string|null;resources:OriginalResource[]}
export interface OriginalStatus {request:OriginalRequest|null}
const id=(value:unknown):value is string=>typeof value==='string'&&/^[a-f0-9]{32}$/.test(value);
export function originalPath(identity:string,action:'status'|'retry'|'download'):string {
 if(!id(identity))throw new Error('A local original ID is required.');
 return action==='status'?`/api/photos/${identity}/originals`:action==='retry'?`/api/originals/${identity}/retry`:`/api/originals/components/${identity}`;
}
export function validOriginalStatus(value:unknown,asset:string):value is OriginalStatus {
 if(!value||typeof value!=='object'||!('request' in value))return false;
 const r=(value as OriginalStatus).request;if(r===null)return true;
 if(!r||!id(r.request_id)||r.asset_id!==asset||!Number.isSafeInteger(r.revision)||r.revision<1||!['waiting_for_device','transferring','failed','ready'].includes(r.state)||!Array.isArray(r.resources)||r.resources.length>8)return false;
 if(r.state==='ready'&&!r.resources.length)return false;
 return r.resources.every((resource,index)=>resource&&resource.ordinal===index&&['photo','video','paired_video','alternate_photo','audio'].includes(resource.resource_type)&&typeof resource.original_filename==='string'&&resource.original_filename.length>0&&resource.original_filename.length<=255&&!['.','..'].includes(resource.original_filename)&&!/[\/\\\p{C}]/u.test(resource.original_filename)&&/^[A-Za-z0-9.-]{1,128}$/.test(resource.uniform_type_identifier)&&Number.isSafeInteger(resource.size)&&resource.size>0&&resource.size<=256*1024*1024&&/^[a-f0-9]{64}$/.test(resource.sha256)&&(id(resource.component_id)||(resource.component_id===null&&r.state!=='ready')));
}
export async function originalRequest<T>(identity:string,action:'status'|'retry'|'download',options:{method?:'GET'|'POST'|'HEAD';csrf?:string;key?:string;signal:AbortSignal}):Promise<T> {
 const method=options.method||'GET';if(method==='POST'&&!options.csrf)throw new ApiError(403,'csrf','Sign in again to verify this request.');
 let response:Response;
 try {response=await fetch(originalPath(identity,action),{method,credentials:'same-origin',cache:'no-store',redirect:'error',signal:options.signal,headers:method==='POST'?{'Content-Type':'application/json','X-CSRF-Token':options.csrf!}:undefined,...(method==='POST'?{body:JSON.stringify({request_key:options.key})}:{})});}
 catch(error){if(options.signal.aborted)throw error;throw new ApiError(0,'network','Could not reach Memory. Try again with the same request.');}
 if(!response.ok)throw new ApiError(response.status,'request_failed',response.status===404?'This original is unavailable.':response.status===409?'This item changed. Refresh its original status.':response.status===507?'The private storage limit was reached.':response.status===401?'Sign in to continue.':'This request did not finish. Refresh and try again.');
 if(method==='HEAD')return undefined as T;
 try{return await response.json() as T;}catch{throw new ApiError(502,'invalid_response','The response could not be read. Refresh and try again.');}
}
