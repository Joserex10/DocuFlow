from PIL import Image, ImageDraw
import os

def draw_indicator(image_path: str, x: int, y: int, radius: int = 30, color: str = '#FF9900', width: int = 5):
    """
    Draws a visual indicator (circle) at the specified coordinates on the image.
    Uses supersampling for antialiasing.
    """
    try:
        if not os.path.exists(image_path):
            print(f"Error: Image not found at {image_path}")
            return

        with Image.open(image_path).convert("RGBA") as base:
            # Create a separate layer for the indicator to handle transparency/antialiasing better if needed
            # For best antialiasing of the circle, we'll draw it 4x larger on a temp image and resize down
            scale_factor = 4
            overlay_size = (radius * 2 * scale_factor, radius * 2 * scale_factor)
            
            # Create high-res circle layer
            circle_img = Image.new('RGBA', overlay_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(circle_img)
            
            # Draw the circle (full size of the temp image, minus padding if we wanted)
            # Coordinates in the high-res image: 0 to size
            # We explicitly subtract width/2 to keep it inside
            offset = width * scale_factor / 2
            draw.ellipse(
                [offset, offset, overlay_size[0] - offset, overlay_size[1] - offset],
                outline=color,
                width=width * scale_factor
            )
            
            # Resize down to target size with high-quality resampling
            target_size = (radius * 2, radius * 2)
            circle_img = circle_img.resize(target_size, resample=Image.Resampling.LANCZOS)
            
            # Calculate position to paste (centered on x, y)
            paste_x = x - radius
            paste_y = y - radius
            
            # Paste onto base image using the circle image itself as the mask
            base.paste(circle_img, (paste_x, paste_y), circle_img)
            
            # Save back (convert to RGB if original was likely not supporting alpha, e.g. PNG screenshots usually support it though)
            # If we want to overwrite as PNG:
            base.save(image_path, "PNG")
            
    except Exception as e:
        print(f"Error drawing indicator: {e}")
