import cloudinary
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url

def upload_image(file):
    try:
        cloudinary.config(
            cloud_name = "duinokary",
            api_key = "486596162731176",
            api_secret = "kgMjiPd8pRMfRsRTzKMcofQvVb4"
        )
        folder = 'agrieco-connect'
        upload_result = upload(file, folder=folder)
        return upload_result['secure_url']
    except Exception as e:
        print(e)
        throw = {
            "message": "An error occurred while uploading the image",
            "error": str(e)
        }
