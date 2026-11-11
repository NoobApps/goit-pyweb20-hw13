import cloudinary
import cloudinary.uploader
from config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

def upload_avatar(file, public_id: str) -> str:
    r = cloudinary.uploader.upload(
        file, 
        public_id=f"avatars/{public_id}", 
        overwrite=True, 
        transformation=[{"width": 250, "height": 250, "crop": "fill"}]
    )
    return r.get("secure_url")