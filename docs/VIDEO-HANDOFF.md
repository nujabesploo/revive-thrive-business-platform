# Website video handoff

Prepared locally October 4, 2026. Not deployed.

The homepage now supports separate real-repair and promotional video groups. The existing Higgsfield reveal is labeled as AI-generated promotion. The real-repair group stays hidden until reviewed footage is supplied; there are no fabricated customer examples.

## What Tife should supply

1. Folder containing 2–3 real repair clips, ideally 20–45 seconds each.
2. For each: device model, symptoms, work performed, and verified result. Confirm permission to publish and remove visible customer names, notifications, passwords, serial numbers and personal photos.
3. Any spoken words, so accurate captions and a transcript can accompany the clip.
4. Choose whether Higgsfield is for repair-service ads only or also an AI UGC service offering. No separate service or pricing has been invented.

## Adding a reviewed clip

Put web-ready H.264 MP4 files and poster images in static/repairs/. Add an entry to REPAIR_VIDEOS in video_catalog.py with title, description, src, poster and label ("Customer repair · shared with permission"). Paths are relative to static/. Optional captions is a WebVTT path; optional transcript is plain text. Only use the customer-repair label once permission and authenticity are confirmed. Restart the application after changing the catalog.

This is a developer-managed catalog, not an admin upload form. Never put raw customer footage or permission documents in public static storage. Keep source footage private. Preview clips and test on mobile before deploying through the existing release process.

## Copy-ready Higgsfield ad brief

Placement: vertical 9:16 social ad, with a separate landscape 16:9 website export. Length: 15 seconds. References: approved Revive & Thrive logo, real bench/device images, and approved repair footage if supplied.

Create a warm, practical promo for Revive & Thrive Tech. Use navy, cyan and silver accents, a clean repair bench, soft natural side lighting and realistic powered-off devices. Open with a cracked-screen close-up, transition to a device inspection, finish with room for an editor-added booking CTA. Use an illustrative presenter only if selected by the owner; do not impersonate Tife or a customer. No fabricated testimonials, guaranteed turnaround, invented prices or warranty claims. No readable private screens, impossible tools, extra fingers, or generated logos/text. Label generated scenes as AI promotional imagery. Add final brand text and captions in editing and inspect anatomy and tool use before publication.

Suggested voiceover: "Cracked screen, tired battery, or charging trouble? Tell Revive & Thrive Tech what happened. We'll discuss the next step for your device. Request a repair at revivethrivetech.com."

Generation is not submitted. Confirm creative direction and current credit cost before using paid generation. Website deployment and real repair uploads remain pending.
