// Dark / light mode, remembered between visits
(function(){
  const root=document.documentElement;
  try{ if(localStorage.getItem('sm-theme')==='dark') root.dataset.theme='dark'; }catch(e){}
  document.addEventListener('DOMContentLoaded',()=>{
    const b=document.getElementById('themeToggle'); if(!b) return;
    b.addEventListener('click',()=>{
      const dark=root.dataset.theme==='dark';
      if(dark) delete root.dataset.theme; else root.dataset.theme='dark';
      try{ localStorage.setItem('sm-theme',dark?'light':'dark'); }catch(e){}
    });
  });
})();
