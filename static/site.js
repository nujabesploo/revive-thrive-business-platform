// Small site JS: dark mode toggle persisted to localStorage
(function(){
  const toggle = document.getElementById('dark-toggle');
  const root = document.documentElement;
  function setDark(isDark){
    if(isDark) root.classList.add('dark'); else root.classList.remove('dark');
    localStorage.setItem('rnt-dark', isDark ? '1' : '0');
  }
  // initialize
  try{
    const pref = localStorage.getItem('rnt-dark');
    if(pref === null){
      // respect user/system prefers-color-scheme
      const dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      setDark(dark);
    } else {
      setDark(pref === '1');
    }
  }catch(e){}
  if(toggle){
    toggle.addEventListener('click', ()=>{
      const isDark = root.classList.contains('dark');
      setDark(!isDark);
    });
  }
})();
