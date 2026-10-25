const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const Module=require('node:module');
const ts=require('typescript');
function load(name){const file=path.resolve(__dirname,'../src/lib/'+name+'.ts');const m=new Module(file,module);m._compile(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,file);return m.exports;}
const {rainfallMmPerHour}=load('rainfall');
const {canApplyWeather}=load('realtime');
test('physical low rainfall never becomes a legacy preset level',()=>{for(let n=0;n<=5;n++){assert.equal(rainfallMmPerHour({rainfall_intensity_mm_hr:n,rainfall_input_unit:'mm_per_hour'}),n);}assert.equal(rainfallMmPerHour({rainfall_intensity_mm_hr:3}),90);});
test('only recent valid weather can be applied',()=>{const now=Date.parse('2026-10-25T06:00:00Z');const source={status:'fresh',error:null,fetched_at:'2026-10-25T06:00:00Z',data:{observed_at:'2026-10-25T06:00:00Z',hourly_at:'2026-10-25T06:00:00Z',rainfall_mm_hr:2}};assert.equal(canApplyWeather(source,now),true);assert.equal(canApplyWeather({...source,error:'offline'},now),false);assert.equal(canApplyWeather(source,now+3600000),false);assert.equal(canApplyWeather({...source,data:{...source.data,rainfall_mm_hr:999}},now),false);});
