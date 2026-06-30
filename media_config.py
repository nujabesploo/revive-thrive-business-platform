"""Central media path catalog for CloudFront/S3-backed template assets.

Keep asset keys normalized here so template code stays clean and all runtime
URLs are built through media_url(path).
"""

MEDIA_ASSETS = {
    "logo": {
        "primary": "logo/logo.png",
    },
    "hero": {
        "image": "hero/hero-image.png",
        "video": "hero/hero-video.mp4",
    },
    "gallery": {
        "technician_repair": "gallery/technician-repair.png",
        "customer_service": "gallery/customer-service.png",
        "before_after": "gallery/before-after.png",
        "screen_repair": "gallery/screen-repair.png",
    },
    "services": {
        "screen_repair": "services/screen-repair.png",
        "battery_repair": "services/battery-repair.png",
        "water_damage": "services/water-damage.png",
        "firestick_service": "services/firestick-service.png",
    },
    "audio": {
        "anthem": "audio/anthem.mp3",
    },
}
