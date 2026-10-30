// Exercise the real UI rendering with an in-memory DOM; no browser or network.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class Node {
  constructor(tag) { this.tag=tag;this.children=[];this._text='';this.value='';this.dataset={};this.hidden=false;this.className='';this.classList={toggle(){},add(){},remove(){}}; }
  set textContent(value) { this._text=String(value);this.children=[]; }
  get textContent() { return this._text+this.children.map(c=>c.textContent||'').join(''); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text='';this.children=[...children]; }
  setAttribute() {}
  addEventListener() {}
}
const nodes=new Map();
const tabs=['normalization','fusion','dataset','extraction'].map(source=>{const n=new Node('button');n.dataset.source=source;return n;});
const document={createElement:tag=>new Node(tag),querySelector:()=>({content:'synthetic-token'}),
  querySelectorAll:()=>tabs,getElementById:id=>{if(!nodes.has(id))nodes.set(id,new Node('div'));return nodes.get(id);}};
const context=vm.createContext({document,fetch:()=>new Promise(()=>{}),setInterval(){},console});
vm.runInContext(fs.readFileSync(path.join(__dirname,'../manual_testing/pipeline_ui/app.js'),'utf8'),context);

const top1={rank:1,dish:'cup_cakes',confidence:.6};
context.classification={top1,class_count:121,display_name_en:'Cupcakes'};
let rendered=vm.runInContext("stageNode({id:'classification',name:'Dish',status:'complete',message:'',data:classification},3)",context);
assert.equal(rendered.children.filter(n=>n.className==='prediction').length,1);
assert.ok(rendered.textContent.includes('60.00%'));
assert.ok(rendered.textContent.includes('Cupcakes'));
assert.ok(!rendered.textContent.includes('cup_cakes'));
context.classification={top3:[top1,{rank:2,dish:'second_dish',confidence:.3},{rank:3,dish:'third_dish',confidence:.1}],class_count:121,display_name_en:'Cupcakes'};
rendered=vm.runInContext("stageNode({id:'classification',name:'Dish',status:'complete',message:'',data:classification},3)",context);
assert.equal(rendered.children.filter(n=>n.className==='prediction').length,1);
assert.ok(!rendered.textContent.includes('second dish'));
assert.ok(!rendered.textContent.includes('third dish'));

const evidence=[{source:'Dataset',original_name:'Milk',confidence:null,allergens:['Milk']},
                {source:'Claude',original_name:'milk',confidence:12,allergens:[]}];
const member={id:'ingredient_001',name:'Milk',sources:['Dataset','Claude'],allergens:['Milk'],evidence};
const item={...member,members:[member],reason:'Same base ingredient.',member_ids:['ingredient_001'],allergen_coverage:{}};
const merged={ingredients:[item],allergens:['Milk'],allergen_causing_ingredients:{Milk:[{ingredient:'Milk',sources:['Dataset'],evidence:[evidence[0]]}]},mapping_disagreements:[],normalization_method:'case_whitespace_v1'};
const normalized={...merged,allergen_causing_ingredients:{Milk:[{ingredient:'Milk',sources:['Dataset'],evidence:[evidence[0]],original_members:[{id:'ingredient_001',name:'Milk',evidence:[evidence[0]]}]}]}};
const ids=['upload','quality','food_gate','classification','ood','dataset','extraction','fusion','normalization'];
const result={decision:'accepted',final_dish:'cup_cakes',final_dish_display_name_en:'Cupcakes',message:'Complete',normalization_performed:true,semantic_normalization_performed:true,
  stages:ids.map(id=>({id,name:id,status:'complete',message:'Complete',data:id==='classification'?{top1,class_count:121,display_name_en:'Cupcakes'}:id==='fusion'?merged:id==='normalization'?normalized:null}))};
function render(value){context.fixture=value;vm.runInContext("jobs.set('synthetic',{id:'synthetic',filename:'synthetic.png',result:fixture});selected='synthetic';source='normalization';lastVersion='';render()",context);}
render(result);
assert.equal(nodes.get('headline').textContent,'Cupcakes');
assert.ok(nodes.get('rawData').textContent.includes('cup_cakes'));
assert.equal(result.final_dish,'cup_cakes');
const chicken=JSON.parse(JSON.stringify(result));chicken.final_dish='dajaj-mashwi';chicken.final_dish_display_name_en='Grilled Chicken';chicken.stages[3].data={top1:{rank:1,dish:'dajaj-mashwi',confidence:.8},class_count:121,display_name_en:'Grilled Chicken'};
render(chicken);
assert.equal(nodes.get('headline').textContent,'Grilled Chicken');
assert.ok(nodes.get('stages').textContent.includes('Grilled Chicken'));
assert.ok(!nodes.get('stages').textContent.includes('dajaj-mashwi'));
assert.ok(nodes.get('rawData').textContent.includes('dajaj-mashwi'));
render(result);
assert.equal(nodes.get('ingredients').hidden,false);
assert.equal(nodes.get('normalizationTab').hidden,false);
assert.equal(nodes.get('progressCount').textContent,'9 of 9 completed');
assert.equal(nodes.get('normalizationPhase').textContent,'Names normalized by Claude');
assert.ok(nodes.get('tableNote').textContent.includes('Names grouped by Claude'));
assert.ok(nodes.get('allergens').textContent.includes('Milk — Dataset'));

const error=JSON.parse(JSON.stringify(result));error.decision='error';error.semantic_normalization_performed=false;error.stopped_at='normalization';error.stages[8].status='error';error.stages[8].data={error_code:'timeout'};
render(error);
assert.equal(nodes.get('ingredients').hidden,true,'A successful pre-normalization merge must not appear as a final result after normalization failure.');

const legacy=JSON.parse(JSON.stringify(result));legacy.semantic_normalization_performed=false;legacy.stages.pop();
render(legacy);
assert.equal(nodes.get('ingredients').hidden,false);
assert.equal(nodes.get('normalizationTab').hidden,true);
assert.equal(nodes.get('progressCount').textContent,'8 of 8 completed');
assert.ok(nodes.get('tableNote').textContent.includes('before semantic normalization'));
const withoutDisplay=JSON.parse(JSON.stringify(result));delete withoutDisplay.final_dish_display_name_en;
render(withoutDisplay);
assert.equal(nodes.get('headline').textContent,'Display name unavailable');
const rejected=JSON.parse(JSON.stringify(result));rejected.decision='rejected';rejected.stopped_at='ood';rejected.final_dish=null;rejected.final_dish_display_name_en=null;
render(rejected);
assert.equal(nodes.get('headline').textContent,'A different photo is needed');
console.log('UI checks passed: English dish names, raw identifiers retained, no raw-name fallback, rejection and normalization states.');
