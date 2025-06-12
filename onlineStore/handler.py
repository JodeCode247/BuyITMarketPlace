import cloudinary
import cloudinary.uploader
from django.conf import settings
from PIL import Image
import io
from .send_email import send_test_email
from .models import Cart
from django.db import transaction

# Configuration       
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True  # Recommended for HTTPS delivery
)


def compress_image(image_file, quality=85, format="JPEG"):
    try:
        img = Image.open(image_file)

        # Convert to RGB if it's not (for JPEG compatibility)
        if img.mode not in ('L', 'RGB'):
            img = img.convert('RGB')

        output = io.BytesIO()
        img.save(output, format=format, optimize=True, quality=quality)
        compressed_data = output.getvalue()
        compressed_size = len(compressed_data)
        print(f"Compressed image size: {compressed_size} bytes")
        output.seek(0)  # Reset the buffer's position to the beginning
        return output
    except Exception as e:
        print(f"Error compressing image: {e}")
        return None
    

def upload_to_drive(image_file):
    try:
        upload_result = cloudinary.uploader.upload(image_file,public_id=f"product_{image_file.name}")  # Optional: Customize public ID
        # Store the URL in the product instance or return it

        return upload_result # Return the secure URL of the uploaded image
    except Exception as e:
        print(f"Cloudinary upload failed: {e}")
        return None


def merge_carts(request, user):
    anonymous_cart_id = request.session.get('cart_id')

    if anonymous_cart_id:
        try:
            # Get the anonymous cart
            anonymous_cart = Cart.objects.get(cart_id=anonymous_cart_id, user__isnull=True)
        except Cart.DoesNotExist:
            # Anonymous cart somehow not found or already associated with a user
            # Clear the session ID and exit
            if 'cart_id' in request.session:
                del request.session['cart_id']
            return

        user_cart, created = Cart.objects.get_or_create(user=user)

        with transaction.atomic(): # Ensure database operations are atomic
            for anonymous_item in anonymous_cart.cartItems.all():
                # Check if the product already exists in the user's cart
                existing_user_item = user_cart.cartItems.filter(product=anonymous_item.product).first()

                if existing_user_item:
                    existing_user_item.quantity += anonymous_item.quantity
                    existing_user_item.save()
                else:
                    # If product does not exist, move the item to the user's cart
                    anonymous_item.cart = user_cart
                    anonymous_item.save()

            anonymous_cart.delete()

        # Clear the anonymous cart ID from the session
        if 'cart_id' in request.session:
            del request.session['cart_id']



