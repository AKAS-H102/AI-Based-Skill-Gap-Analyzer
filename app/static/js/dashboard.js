let chart;
const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];

function selectedSkills(){return $$('.skill-row').filter(r=>r.querySelector('.pick').checked).map(r=>({skill_id:+r.dataset.id,level:+r.querySelector('.level').value}))}
async function post(url,data,timeoutMs=15000){
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),timeoutMs);
  try{
    const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':window.CSRF_TOKEN},body:JSON.stringify(data),signal:controller.signal});
    const payload=await r.json().catch(()=>({error:`Server returned an unreadable response (${r.status}).`}));
    if(!r.ok) throw new Error(payload.error||payload.message||`Request failed (${r.status}).`);
    return payload;
  }catch(e){
    if(e.name==='AbortError') throw new Error('The analysis took too long. Please try again. If it repeats, check the terminal for a server error.');
    throw e;
  }finally{clearTimeout(timer)}
}
function showAnalysisError(message){
  let box=$('#analysisError');
  if(!box){box=document.createElement('div');box.id='analysisError';box.className='alert alert-danger mt-3';box.setAttribute('role','alert');$('#processing').insertAdjacentElement('afterend',box)}
  box.textContent=message||'Analysis failed. Please try again.';
  box.classList.remove('d-none');
}
function react(){document.body.classList.remove('interaction-pulse');void document.body.offsetWidth;document.body.classList.add('interaction-pulse')}
function updateSelectionUI(){const rows=$$('.skill-row');let count=0;rows.forEach(r=>{const checked=r.querySelector('.pick').checked;r.classList.toggle('is-selected',checked);if(checked)count++});$('#selectedCount').textContent=`${count} selected`}
function populateCategories(){const cats=[...new Set($$('.skill-row').map(r=>r.dataset.category).filter(Boolean))].sort();const select=$('#categoryFilter');cats.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c.replace(/\b\w/g,x=>x.toUpperCase());select.appendChild(o)})}
function filterSkills(){const q=$('#skillSearch').value.trim().toLowerCase();const cat=$('#categoryFilter').value;let visible=0;$$('.skill-row').forEach(r=>{const ok=(!q||r.dataset.name.includes(q))&&(!cat||r.dataset.category===cat);r.style.display=ok?'grid':'none';if(ok)visible++});$('#noSkillsFound').classList.toggle('d-none',visible!==0)}

populateCategories();updateSelectionUI();
$$('.pick').forEach(x=>x.addEventListener('change',()=>{updateSelectionUI();react()}));
$$('.level').forEach(x=>x.addEventListener('change',()=>{react()}));
$('#skillSearch').addEventListener('input',filterSkills);$('#categoryFilter').addEventListener('change',filterSkills);

$('#saveSkills').onclick=async()=>{const btn=$('#saveSkills');btn.disabled=true;const old=btn.textContent;try{const d=await post('/api/skills',{skills:selectedSkills()});if(d.ok){btn.textContent='Profile saved ✓';react();setTimeout(()=>btn.textContent=old,1300)}}catch(e){showAnalysisError(e.message)}finally{btn.disabled=false}};

$('#role').addEventListener('change',()=>{if($('#role').value){$('#role').closest('.analysis-panel').classList.add('role-selected');react()}});
$('#analyze').onclick=async()=>{
  const role=$('#role').value;
  if(!role){$('#role').focus();$('#role').classList.add('shake');setTimeout(()=>$('#role').classList.remove('shake'),450);return}
  const btn=$('#analyze'), oldLabel=btn.querySelector('span').textContent, errorBox=$('#analysisError');
  btn.disabled=true;btn.querySelector('span').textContent='Analyzing…';
  if(errorBox)errorBox.classList.add('d-none');
  $('#processing').classList.remove('d-none');$('#results').classList.add('d-none');$('#pathSection').classList.add('d-none');$('.analysis-preview').classList.add('d-none');react();
  const steps=['Analyzing your skill profile…','Comparing career requirements…','Calculating skill gaps…','Analyzing dependencies…','Generating personalized learning path…'];
  let stepIndex=0;$('#processText').textContent=steps[0];
  const stepTimer=setInterval(()=>{stepIndex=(stepIndex+1)%steps.length;$('#processText').textContent=steps[stepIndex]},650);
  try{
    // Start real analysis immediately; animation runs alongside the request instead of delaying it.
    const d=await (async()=>{await post('/api/skills',{skills:selectedSkills()});return await post('/api/analyze',{role_id:+role})})();
    if(!d||!Array.isArray(d.skills)||!Array.isArray(d.path)||!Array.isArray(d.careers))throw new Error(d?.error||'The server returned incomplete analysis data.');
    render(d);$('#results').classList.remove('d-none');$('#pathSection').classList.remove('d-none');$('#pathSection').scrollIntoView({behavior:'smooth',block:'start'});
  }catch(e){showAnalysisError(e.message);$('#processing').classList.add('d-none');$('.analysis-preview').classList.remove('d-none')}
  finally{clearInterval(stepTimer);$('#processing').classList.add('d-none');btn.disabled=false;btn.querySelector('span').textContent=oldLabel}
};

function render(d){animate($('#match'),d.match,'%');$('#strong').textContent=d.skills.filter(x=>x.classification==='strong').length;$('#gaps').textContent=d.skills.filter(x=>x.gap>0).length;$('#pathCount').textContent=d.path.length;const p=d.skills.filter(x=>x.gap>0).sort((a,b)=>b.gap-a.gap).slice(0,6);$('#priorityList').innerHTML=p.length?p.map(x=>`<div class="priority"><b>${x.name}</b><span>${x.severity}</span></div>`).join(''):'<div class="empty compact">No gaps found for this role. Excellent match.</div>';drawChart(d.skills);$('#path').innerHTML=d.path.length?d.path.map((x,i)=>`<div class="node" style="animation-delay:${i*70}ms"><div class="num">${i+1}</div><h5>${x.skill_name}</h5><small>Current ${x.current_level||0} · Required ${x.required_level} · Gap ${x.gap}</small><div class="resource"><b>${x.title}</b><br>${x.hours}h · ${x.difficulty}</div><div class="progress mt-3" style="height:6px;background:rgba(255,255,255,.07)"><div class="progress-bar" style="width:${x.progress}%"></div></div><div class="d-flex gap-2 mt-3"><button class="btn btn-sm btn-outline-light flex-grow-1" onclick="window.open('${x.url}','_blank','noopener')">Resource</button><button class="btn btn-sm btn-primary complete" data-id="${x.id}">${x.done?'Completed':'Complete'}</button></div></div>`).join(''):'<div class="empty">Your current profile already covers the selected role. Keep building depth through projects.</div>';$$(".complete").forEach(b=>b.onclick=async()=>{b.disabled=true;const data=await post('/api/progress',{resource_id:+b.dataset.id,progress:100,role_id:+$('#role').value});if(data.ok){react();if(data.match!==undefined)render(data);else{b.textContent='Completed';b.closest('.node').querySelector('.progress-bar').style.width='100%'}}else b.disabled=false});$('#careers').innerHTML=d.careers.map(c=>`<div class="career"><span class="score-pill">${c.similarity}%</span><strong>${c.name}</strong><div class="muted mt-1">${c.description}</div></div>`).join('')}
function animate(el,to,suffix){let t=performance.now();function f(n){let p=Math.min((n-t)/700,1),e=1-Math.pow(1-p,3);el.textContent=(to*e).toFixed(1)+suffix;if(p<1)requestAnimationFrame(f)}requestAnimationFrame(f)}
function drawChart(rows){const ctx=$('#gapChart');if(chart)chart.destroy();const data=rows.slice(0,10);chart=new Chart(ctx,{type:'bar',data:{labels:data.map(x=>x.name),datasets:[{label:'Current',data:data.map(x=>x.current_level),borderWidth:0,borderRadius:5},{label:'Required',data:data.map(x=>x.required_level),borderWidth:0,borderRadius:5}]},options:{responsive:true,animation:{duration:900},scales:{y:{min:0,max:4,ticks:{stepSize:1,color:'#91a5c0'},grid:{color:'rgba(255,255,255,.06)'}},x:{ticks:{color:'#91a5c0',maxRotation:35,minRotation:25},grid:{display:false}}},plugins:{legend:{labels:{color:'#dfeaff',boxWidth:10,usePointStyle:true}}}}})}
