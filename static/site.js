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
