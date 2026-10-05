"""Approved public videos. Keep customer footage out until permission is confirmed."""

# Add reviewed customer clips here; see docs/VIDEO-HANDOFF.md for the fields.
REPAIR_VIDEOS = []

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
