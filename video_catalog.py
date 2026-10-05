"""Approved public videos. Keep customer footage out until permission is confirmed."""

# Add reviewed customer clips here; see docs/VIDEO-HANDOFF.md for the fields.
REPAIR_VIDEOS = [
    {"title": "iPhone 13 screen repair", "description": "A time-lapse look at the repair bench, with an original lo-fi instrumental.", "src": "motion/repairs/screen-repair-promo.mp4", "poster": "motion/repairs/screen-poster.jpg", "label": "Real repair footage", "transcript": "Screen repair process shown in time-lapse. Opening October 20, 2026 at Grow DeSoto Market Place, booth #701, 324 E Belt Line Rd, DeSoto TX 75115. Monday–Sunday, 9 a.m.–6 p.m. Central. No spoken audio."},
    {"title": "iPhone 13 battery replacement", "description": "A closer look at battery replacement work. Footage plays at twice the original speed with an original lo-fi instrumental.", "src": "motion/repairs/battery-repair-promo.mp4", "poster": "motion/repairs/battery-poster.jpg", "label": "Real repair footage", "transcript": "Battery replacement work at the repair bench. Opening October 20, 2026 at Grow DeSoto Market Place, booth #701, 324 E Belt Line Rd, DeSoto TX 75115. Monday–Sunday, 9 a.m.–6 p.m. Central. No spoken audio."}
]

PROMO_VIDEOS = [
    {
        "title": "Inside the device",
        "description": "A Blender-made 3D product film exploring device components. An illustrative animation, not footage of a customer repair.",
        "src": "motion/v2/repair-intro.mp4",
        "poster": "motion/v2/repair-poster.png",
        "label": "Blender 3D brand film",
    },
    {
        "title": "A fresh start for your device",
        "description": "An AI-generated product animation introducing our repair services. This is promotional imagery, not footage of a customer repair.",
        "src": "motion/higgsfield-reveal.mp4",
        "poster": "motion/repair-poster.png",
        "label": "AI-generated promotion",
    }
]
