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

  // Progressive reveal for key sections/components.
  const revealItems = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window && revealItems.length) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    revealItems.forEach((item) => observer.observe(item));
  } else {
    revealItems.forEach((item) => item.classList.add('is-visible'));
  }
})();
