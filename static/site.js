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
