// Plan page: tick off days (saved per subject) + 25-minute focus timer
document.addEventListener('DOMContentLoaded',()=>{
  const boxes=[...document.querySelectorAll('.day-item input')], bar=document.getElementById('bar');
  const key='sm-plan-'+SUBJECT_KEY;
  let saved=[]; try{ saved=JSON.parse(localStorage.getItem(key)||'[]'); }catch(e){}
  let ready = !LOGGED_IN;   // wait for server data before saving, so we never overwrite it
  function update(){
    boxes.forEach(b=>b.closest('.day-item').classList.toggle('done',b.checked));
    bar.style.width=(boxes.filter(b=>b.checked).length/boxes.length*100)+'%';
    const days=boxes.map(b=>b.checked);
    try{ localStorage.setItem(key,JSON.stringify(days)); }catch(e){}
    if(LOGGED_IN&&ready) fetch('/api/progress/'+SUBJECT_KEY,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({days})});
  }
  boxes.forEach((b,i)=>{ b.checked=!!saved[i]; b.addEventListener('change',update); });
  update();
  if(LOGGED_IN) fetch('/api/progress/'+SUBJECT_KEY).then(r=>r.json()).then(d=>{
    if(d.days&&d.days.length) boxes.forEach((b,i)=>b.checked=!!d.days[i]);
    ready=true; update();
  });

  const t=document.getElementById('time'); let left=1500,id=null;
  const show=()=>t.textContent=String(Math.floor(left/60)).padStart(2,'0')+':'+String(left%60).padStart(2,'0');
  document.getElementById('tStart').addEventListener('click',e=>{
    if(id){clearInterval(id);id=null;e.target.textContent='Start';return;}
    e.target.textContent='Pause';
    id=setInterval(()=>{ left--; show(); if(left<=0){clearInterval(id);id=null;e.target.textContent='Start';left=300;show();alert('Time for a 5 minute break!');} },1000);
  });
  document.getElementById('tReset').addEventListener('click',()=>{clearInterval(id);id=null;left=1500;show();document.getElementById('tStart').textContent='Start';});
});
