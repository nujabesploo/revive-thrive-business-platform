document.documentElement.classList.remove("dark");
document.querySelectorAll("[data-reveal]").forEach(item=>item.classList.add("is-visible"));

// Explicit playback respects visitor motion and data preferences.
document.querySelectorAll('[data-film-play]').forEach(button => {
  const video = button.parentElement.querySelector('video');
  button.addEventListener('click', async () => {
    try { if (video.paused) await video.play(); else video.pause(); }
    catch (_) { button.textContent = 'Use the video controls to play'; }
  });
  video.addEventListener('play', () => { button.textContent = 'Pause film'; });
  video.addEventListener('pause', () => { button.textContent = 'Play the repair film ↗'; });
});

// Show the selected repair without sending form contents to analytics or storage.
const bookingForm = document.querySelector('[data-booking-form]');
if (bookingForm) {
  const summary = bookingForm.querySelector('[data-booking-summary]');
  const updateSummary = () => {
    const device = bookingForm.elements.device_type.value;
    const service = bookingForm.elements.service_needed.value;
    const image = document.querySelector('[data-device-image]');
    if (image) {
      const category = ['Samsung', 'Android'].includes(device) ? 'samsung' : ['Tablet', 'Other'].includes(device) ? 'other' : 'iphone';
      image.src = 'https://d2spdapo89woam.cloudfront.net/releases/20260919/higgsfield/' + category + '-higgsfield.jpg';
      image.alt = (device || 'Phone') + ' repair illustration';
    }
    summary.textContent = device || service
      ? [device, service].filter(Boolean).join(' · ') + ' — we’ll confirm your quote before repair.'
      : 'Choose your device and repair below to start your request.';
  };
  bookingForm.elements.device_type.addEventListener('change', updateSummary);
  bookingForm.elements.service_needed.addEventListener('change', updateSummary);
  updateSummary();
}

// Current-page orientation and subtle pointer depth; no tracking or background loop.
document.querySelectorAll('.site-nav a').forEach(link => {
  if (new URL(link.href).pathname === location.pathname) link.setAttribute('aria-current', 'page');
});
const depthPreference = matchMedia('(prefers-reduced-motion: no-preference) and (hover: hover) and (pointer: fine)');
const depthCards = document.querySelectorAll('.service-tile, .device-card, .form-scene, .stat-card');
depthCards.forEach(card => {
  card.classList.add('depth-card');
  const reset = () => { card.style.removeProperty('--rx'); card.style.removeProperty('--ry'); };
  card.addEventListener('pointermove', event => {
    if (!depthPreference.matches) return;
    const rect = card.getBoundingClientRect();
    card.style.setProperty('--rx', `${((.5 - (event.clientY - rect.top) / rect.height) * 4).toFixed(2)}deg`);
    card.style.setProperty('--ry', `${(((event.clientX - rect.left) / rect.width - .5) * 4).toFixed(2)}deg`);
  }, {passive:true});
  card.addEventListener('pointerleave', reset);
  depthPreference.addEventListener('change', reset);
});

// Progressive enhancement: the server-rendered finder also works without JS/API.
const repairFinder = document.querySelector('[data-repair-finder]');
if (repairFinder) {
  fetch('/api/v1/repair-catalog', {credentials: 'omit'})
    .then(response => { if (!response.ok) throw new Error('Catalog unavailable'); return response.json(); })
    .then(catalog => {
      for (const [name, choices] of [['device_type', catalog.devices], ['service_needed', catalog.services]]) {
        if (!Array.isArray(choices) || !choices.length || !choices.every(value => typeof value === 'string')) continue;
        const select = repairFinder.elements[name];
        const selected = select.value;
        // Do not replace a selection after a visitor has started using the form.
        if (repairFinder.contains(document.activeElement)) continue;
        select.replaceChildren(...choices.map(value => new Option(value, value)));
        if (choices.includes(selected)) select.value = selected;
      }
    }).catch(() => { /* Keep usable server-rendered options if offline. */ });
}

// Music is opt-in and pauses whenever a customer starts a video.
(() => {
 const audio = document.getElementById('ambient-music');
 const button = document.getElementById('ambient-toggle');
 const status = document.getElementById('ambient-status');
 if (!audio || !button || !status) return;
 audio.volume = 0.18;
 const sync = () => {button.textContent = audio.paused ? 'Play background music' : 'Pause background music'; button.setAttribute('aria-pressed', String(!audio.paused)); status.textContent = audio.paused ? 'Optional lo-fi music · off' : 'Optional lo-fi music · on';};
 button.addEventListener('click', async () => {
   if (!audio.paused) {audio.pause(); return;}
   if ([...document.querySelectorAll('video')].some(v => !v.paused)) {status.textContent = 'Pause the video before starting background music.'; return;}
   try {await audio.play();} catch (_) {status.textContent = 'Music could not load. Please try again.';}
 });
 audio.addEventListener('play', sync); audio.addEventListener('pause', sync);
 document.querySelectorAll('video').forEach(v => v.addEventListener('play', () => audio.pause()));
 document.addEventListener('visibilitychange', () => {if(document.hidden) audio.pause();});
})();
