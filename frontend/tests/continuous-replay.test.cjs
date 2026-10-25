const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const Module=require('node:module');
const ts=require('typescript');
const file=path.resolve(__dirname,'../src/lib/fleet-playback.ts');
const loaded=new Module(file,module);
loaded._compile(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,file);
const {vehicleAtMinute}=loaded.exports;
test('continuous replay uses global time rather than restarting a continuing trip',()=>{
 const trip={depart_minutes:0,return_available_minutes:180,geometry:{type:'LineString',coordinates:[[80,13],[80.1,13],[80,13]]},phases:[{status:'carrying_people',start_minutes:0,end_minutes:120,geometry:{type:'LineString',coordinates:[[80,13],[80.1,13]]}},{status:'returning',start_minutes:120,end_minutes:180,geometry:{type:'LineString',coordinates:[[80.1,13],[80,13]]}}]};
 assert.equal(vehicleAtMinute([trip],60).status,'carrying_people');
 assert.ok(Math.abs(vehicleAtMinute([trip],60).position[1]-80.05)<1e-9);
 assert.equal(vehicleAtMinute([trip],150).status,'returning');
 assert.ok(Math.abs(vehicleAtMinute([trip],150).position[1]-80.05)<1e-9);
});
