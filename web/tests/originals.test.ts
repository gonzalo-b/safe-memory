import assert from 'node:assert/strict';
import { test } from 'node:test';
import { originalPath, validOriginalStatus } from '../lib/originals.ts';
test('original routes are exact same-origin IDs and malformed descriptors never become links',()=>{
 const id='a'.repeat(32);assert.equal(originalPath(id,'status'),`/api/photos/${id}/originals`);assert.equal(originalPath(id,'download'),`/api/originals/components/${id}`);
 for(const bad of ['../x','https://evil.test/file',id+'?x=1','A'.repeat(32)])assert.throws(()=>originalPath(bad,'download'));
 assert.equal(validOriginalStatus({request:null},id),true);
 const request={request_id:id,asset_id:id,revision:1,state:'ready',error_code:null,resources:[{ordinal:0,resource_type:'photo',original_filename:'original.heic',uniform_type_identifier:'public.heic',size:10,sha256:'b'.repeat(64),component_id:'c'.repeat(32)}]};
 assert.equal(validOriginalStatus({request},id),true);
 for(const change of [{component_id:'https://evil.test/file'},{size:-1},{ordinal:2},{original_filename:'../x'}])assert.equal(validOriginalStatus({request:{...request,resources:[{...request.resources[0],...change}]}},id),false);
 assert.equal(validOriginalStatus({request:{...request,resources:[]}},id),false);
 assert.equal(validOriginalStatus({request:{...request,asset_id:'d'.repeat(32)}},id),false);
});
