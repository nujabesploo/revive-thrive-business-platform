# S3 Media Migration Checklist

This guide standardizes media object keys so Flask templates can use clean paths through `media_url(path)`.

## Target Object Keys

```
logo/logo.png

hero/hero-image.png
hero/hero-video.mp4

gallery/technician-repair.png
gallery/customer-service.png
gallery/before-after.png
gallery/screen-repair.png

services/screen-repair.png
services/battery-repair.png
services/water-damage.png
services/firestick-service.png

audio/anthem.mp3
```

## 1) Verify Required Files Exist in S3

Use AWS Console (S3 bucket `revive-thrive-assets`) or AWS CLI.

Example CLI listing:

```bash
aws s3 ls s3://revive-thrive-assets --recursive
```

## 2) Copy or Rename Messy Keys to Clean Keys

S3 does not support direct rename; use copy then delete.

Examples:

```bash
aws s3 cp "s3://revive-thrive-assets/logo/IMG_0500.PNG" "s3://revive-thrive-assets/logo/logo.png"
aws s3 cp "s3://revive-thrive-assets/hero/revive-commercial-vertical.mp4" "s3://revive-thrive-assets/hero/hero-video.mp4"
aws s3 cp "s3://revive-thrive-assets/gallery/ai-image-generator-1781998795888.png" "s3://revive-thrive-assets/gallery/technician-repair.png"
aws s3 cp "s3://revive-thrive-assets/audio/GRND LVLS ANTHEM (3).mp3" "s3://revive-thrive-assets/audio/anthem.mp3"
```

After validation, optionally remove old keys:

```bash
aws s3 rm "s3://revive-thrive-assets/old/path/file.ext"
```

## 3) Validate CloudFront Access

Test object URLs:

```bash
curl -I https://<cloudfront-domain>/hero/hero-image.png
curl -I https://<cloudfront-domain>/hero/hero-video.mp4
curl -I https://<cloudfront-domain>/audio/anthem.mp3
```

## 4) Invalidate CloudFront Cache

```bash
aws cloudfront create-invalidation --distribution-id <DISTRIBUTION_ID> --paths "/*"
```

## 5) Runtime Verification

- Confirm `.env` has `MEDIA_BASE_URL=https://<cloudfront-domain>`
- Restart app services on EC2
- Load homepage and verify media renders from CloudFront
