#!/usr/bin/env python3
"""
Display module for the music player using Adafruit 2.8" TFT LCD
"""

import time
import busio
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.ili9341 as ili9341
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
import io

class MusicDisplay:
    def __init__(self, rotation=90):
        """
        Initialize the 2.8" TFT display
        """
        # Volume bar visibility tracking
        self.last_volume_change_time = 0
        self.volume_display_duration = 3.0  # Show volume bar for 3 seconds
        
        # Dynamic color based on album art
        self.current_bg_color = None
        self.current_accent_color = None
        
        # Configuration for display
        # CS pin will be tied to GND and is always active. tying it to CE0 causes GPIO busy, im not sure why
        cs_pin = None# digitalio.DigitalInOut(board.CE0)
        dc_pin = digitalio.DigitalInOut(board.D25)  # GPIO 25
        reset_pin = digitalio.DigitalInOut(board.D24)  # GPIO 24
        
        # Setup SPI bus
        spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        
        # Create the display object
        self.display = ili9341.ILI9341(
            spi,
            cs=cs_pin,
            dc=dc_pin,
            rst=reset_pin,
            width=240,
            height=320,
            rotation=rotation
        )
        
        self.width = 320
        self.height = 240
            
        # Create drawing objects
        self.image = Image.new("RGB", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        
        # Load fonts with better hierarchy
        try:
            self.font_splash = ImageFont.truetype("/home/pi/.fonts/InterVariable.ttf", 40)
            self.font_splash_sub = ImageFont.truetype("/home/pi/.fonts/InterVariable.ttf", 18)
            self.font_title = ImageFont.truetype("/home/pi/.fonts/InterVariable.ttf", 24)  # Bigger and bold
            self.font_subtitle = ImageFont.truetype("/home/pi/.fonts/InterVariable.ttf", 18)
            self.font_small = ImageFont.truetype("/home/pi/.fonts/InterVariable.ttf", 12)
        except:
            print("Failed to load fonts, using default")
            # Fallback to default font
            self.font_splash = ImageFont.load_default()
            self.font_splash_sub = ImageFont.load_default()
            self.font_title = ImageFont.load_default()
            self.font_subtitle = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            
        # Modern color palette
        self.BLACK = (0, 0, 0)
        self.DARK_BG = (20, 25, 35)  # Dark blue-gray background
        self.WHITE = (255, 255, 255)
        self.BLUE = (0, 122, 255)  # Modern iOS-style blue
        self.GREEN = (52, 199, 89)  # Modern green
        self.RED = (255, 59, 48)  # Modern red
        self.GRAY = (142, 142, 147)  # Subtle gray for secondary text
        self.VOLUME_BAR_BG = (60, 65, 75)  # Dark gray for volume bar background
        
        # Clear display
        self.clear()
        
    def clear(self, color=None):
        """Clear the display"""
        if color is None:
            # Use dynamic background color if available, otherwise default
            color = self.current_bg_color if self.current_bg_color else self.DARK_BG
        self.draw.rectangle((0, 0, self.width, self.height), fill=color)
        self.display.image(self.image)
    
    def cleanup(self):
        try:
            self.clear()
        except:
            print("Screen failed to clear")
        
    def show_splash(self):
        """Show modern splash screen"""
        self.clear()
        
        # Main title - centered
        title = "MusicBox"
        # Get text bounding box for centering
        bbox = self.draw.textbbox((0, 0), title, font=self.font_splash)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.width - text_width) // 2
        y = self.height // 2 - 40
        self.draw.text((x, y), title, font=self.font_splash, fill=self.WHITE)
        
        # Subtitle message
        subtitle = "Connect USB Drive"
        bbox = self.draw.textbbox((0, 0), subtitle, font=self.font_splash_sub)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        y = self.height // 2 + 20
        self.draw.text((x, y), subtitle, font=self.font_splash_sub, fill=self.GRAY)
        
        # Small instruction
        instruction = "Insert media to begin"
        bbox = self.draw.textbbox((0, 0), instruction, font=self.font_small)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        y = self.height // 2 + 50
        self.draw.text((x, y), instruction, font=self.font_small, fill=self.GRAY)
        
        self.display.image(self.image)
        
    def update_now_playing(self, filename, state="PLAYING", volume=80, 
                           current_index=0, total_tracks=0, force_show_volume=False):
        """
        Update the now playing screen with modern design
        
        Args:
            filename: Current song filename
            state: Player state (PLAYING, PAUSED, STOPPED)
            volume: Current volume percentage (0-100)
            current_index: Current track number
            total_tracks: Total number of tracks
            force_show_volume: Force display of volume bar (when volume is being adjusted)
        """
        self.clear()
        
        # Check if volume bar should be shown
        show_volume = force_show_volume or self._should_show_volume_bar()
        
        # Volume bar area (right edge, 30px wide when visible)
        volume_bar_width = 30 if show_volume else 0
        main_content_width = self.width - volume_bar_width
        
        # Draw vertical volume bar on the right edge (only if visible)
        if show_volume:
            self._draw_vertical_volume_bar(volume, volume_bar_width)
        
        # Extract song and album info from metadata
        song_name, album_name = self._extract_metadata(filename)
        
        # Fetch and display large album art (centered in available space)
        artwork_size = 160  # Album art size that leaves room for text
        artwork_x = (main_content_width - artwork_size) // 2
        artwork_y = 15
        
        # Load album art and extract dominant color
        artwork_image = None
        if state == "PLAYING" or state == "PAUSED":
            has_art, artwork_image = self.paste_album_art(filename, artwork_x, artwork_y, artwork_size, return_image=True)
            if has_art and artwork_image:
                # Extract dominant color from album art
                self._extract_colors_from_artwork(artwork_image)
            if not has_art:
                # Draw placeholder if no album art
                self._draw_album_art_placeholder(artwork_x, artwork_y, artwork_size)
                self.current_bg_color = self.DARK_BG  # Reset to default
                self.current_accent_color = self.GREEN
        else:
            self._draw_album_art_placeholder(artwork_x, artwork_y, artwork_size)
            self.current_bg_color = self.DARK_BG
            self.current_accent_color = self.GREEN
        
        # Song title (below album art) - left aligned
        title_y = artwork_y + artwork_size + 10
        text_x = 50  # Left margin
        text_max_width = main_content_width - text_x - 10  # Account for left margin + right padding
        
        # Draw text area background with 10% opacity black for readability
        text_area_padding = 12
        album_y = title_y + 30
        text_area_x1 = text_x - text_area_padding
        text_area_y1 = title_y - text_area_padding
        text_area_x2 = main_content_width - 10
        text_area_y2 = album_y + 25  # Height to cover both song and album text with padding
        self._draw_text_background(text_area_x1, text_area_y1, text_area_x2, text_area_y2)
        
        # Now draw the text on top of the background
        self._draw_text_with_truncate(song_name, text_x, title_y, self.font_title, 
                                      self.WHITE, max_width=text_max_width)
        
        # Album name (below song title, smaller and gray) - left aligned
        self._draw_text_with_truncate(album_name, text_x, album_y, self.font_subtitle, 
                                      self.GRAY, max_width=text_max_width)
        
        # Draw pause overlay if paused
        if state == "PAUSED":
            self._draw_pause_overlay()
        
        # Update display
        self.display.image(self.image)
    
    def _extract_colors_from_artwork(self, artwork_image):
        """
        Extract dominant color from album artwork for background
        
        Args:
            artwork_image: PIL Image object of the album art
        """
        try:
            # Resize image for faster color analysis
            small_image = artwork_image.resize((50, 50), Image.LANCZOS)
            
            # Get all pixels
            pixels = list(small_image.getdata())
            
            # Calculate average color with a bias towards darker/more saturated colors
            # This gives a more aesthetically pleasing background
            r_total = 0
            g_total = 0
            b_total = 0
            count = 0
            
            for pixel in pixels:
                if isinstance(pixel, tuple) and len(pixel) >= 3:
                    r, g, b = pixel[0], pixel[1], pixel[2]
                    # Weight darker pixels more heavily
                    brightness = (r + g + b) / 3
                    weight = 1.0 if brightness < 128 else 0.5
                    r_total += r * weight
                    g_total += g * weight
                    b_total += b * weight
                    count += weight
            
            if count > 0:
                avg_r = int(r_total / count)
                avg_g = int(g_total / count)
                avg_b = int(b_total / count)
                
                # Darken the color for background (multiply by 0.4 to make it darker)
                bg_r = int(avg_r * 0.4)
                bg_g = int(avg_g * 0.4)
                bg_b = int(avg_b * 0.4)
                
                self.current_bg_color = (bg_r, bg_g, bg_b)
                
                # Use slightly brighter version for accent (volume bar)
                accent_r = min(255, int(avg_r * 0.8))
                accent_g = min(255, int(avg_g * 0.8))
                accent_b = min(255, int(avg_b * 0.8))
                self.current_accent_color = (accent_r, accent_g, accent_b)
            else:
                # Fallback to default colors
                self.current_bg_color = self.DARK_BG
                self.current_accent_color = self.GREEN
                
        except Exception as e:
            print(f"Error extracting colors: {e}")
            self.current_bg_color = self.DARK_BG
            self.current_accent_color = self.GREEN
    
    def _draw_text_background(self, x1, y1, x2, y2):
        """
        Draw a semi-transparent black background for text area
        
        Args:
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner
        """
        try:
            # Create overlay with 10% opacity black
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle((x1, y1, x2, y2), fill=(0, 0, 0, 26))  # 10% opacity = 26/255
            
            # Convert base image to RGBA for blending
            base = self.image.convert('RGBA')
            
            # Composite the overlay
            composited = Image.alpha_composite(base, overlay)
            
            # Convert back to RGB
            self.image = composited.convert('RGB')
            self.draw = ImageDraw.Draw(self.image)
        except Exception as e:
            print(f"Error drawing text background: {e}")
    
    def _draw_pause_overlay(self):
        """
        Draw a semi-transparent pause overlay with pause icon
        """
        # Create a semi-transparent white overlay using PIL
        overlay = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 64))  # 25% opacity
        
        # Convert base image to RGBA for blending
        base = self.image.convert('RGBA')
        
        # Composite the overlay
        composited = Image.alpha_composite(base, overlay)
        
        # Convert back to RGB
        self.image = composited.convert('RGB')
        self.draw = ImageDraw.Draw(self.image)
        
        # Draw pause icon (two vertical bars) in center
        icon_width = 60
        icon_height = 80
        bar_width = 18
        gap = 14
        
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Left bar
        left_bar_x = center_x - gap // 2 - bar_width
        self.draw.rectangle(
            (left_bar_x, center_y - icon_height // 2, 
             left_bar_x + bar_width, center_y + icon_height // 2),
            fill=self.WHITE
        )
        
        # Right bar
        right_bar_x = center_x + gap // 2
        self.draw.rectangle(
            (right_bar_x, center_y - icon_height // 2,
             right_bar_x + bar_width, center_y + icon_height // 2),
            fill=self.WHITE
        )
    
    def notify_volume_change(self):
        """
        Call this method when volume is changed to trigger display of volume bar
        """
        self.last_volume_change_time = time.time()
    
    def _should_show_volume_bar(self):
        """
        Check if volume bar should be shown based on time since last change
        
        Returns:
            True if volume bar should be visible, False otherwise
        """
        if self.last_volume_change_time == 0:
            return False
        
        elapsed = time.time() - self.last_volume_change_time
        return elapsed < self.volume_display_duration
    
    def _draw_vertical_volume_bar(self, volume, bar_width):
        """
        Draw vertical volume bar with 10 segments on the right edge
        
        Args:
            volume: Volume percentage (0-100)
            bar_width: Width of the volume bar area
        """
        bar_x = self.width - bar_width
        
        # Volume percentage text at the top
        vol_text = f"{volume}%"
        bbox = self.draw.textbbox((0, 0), vol_text, font=self.font_small)
        text_width = bbox[2] - bbox[0]
        text_x = bar_x + (bar_width - text_width) // 2
        text_y = 10
        self.draw.text((text_x, text_y), vol_text, font=self.font_small, fill=self.GRAY)
        
        # Smaller, more subtle volume bar
        bar_height = 140  # Total height for volume indicators
        bar_start_y = 35  # Start below the percentage text
        
        # Number of segments (0-10)
        num_segments = 10
        segment_height = 10  # Smaller notches
        segment_gap = 4
        segment_width = 16  # Narrower segments
        
        # Calculate how many segments should be filled
        filled_segments = int((volume / 100) * num_segments)
        
        # Draw each segment (from top to bottom, filling from bottom up)
        for i in range(num_segments):
            seg_y = bar_start_y + i * (segment_height + segment_gap)
            seg_x = bar_x + (bar_width - segment_width) // 2
            
            # Determine if this segment should be filled
            # Top segment is index 9, bottom is index 0
            segment_index = num_segments - i - 1
            
            if segment_index < filled_segments:
                # Filled segment - use accent color from album art
                fill_color = self.current_accent_color if self.current_accent_color else self.GREEN
                self.draw.rectangle(
                    (seg_x, seg_y, seg_x + segment_width, seg_y + segment_height),
                    fill=fill_color
                )
            else:
                # Empty segment - use dark background
                self.draw.rectangle(
                    (seg_x, seg_y, seg_x + segment_width, seg_y + segment_height),
                    fill=self.VOLUME_BAR_BG
                )
    
    def _draw_text_with_truncate(self, text, x, y, font, color, max_width=None):
        """
        Draw text at specified position with optional truncation
        
        Args:
            text: Text to draw
            x: X coordinate
            y: Y coordinate
            font: Font to use
            color: Text color
            max_width: Maximum width before truncation
        """
        # Truncate if needed
        if max_width:
            bbox = self.draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            if text_width > max_width:
                # Truncate and add ellipsis
                while text_width > max_width and len(text) > 3:
                    text = text[:-1]
                    bbox = self.draw.textbbox((0, 0), text + "...", font=font)
                    text_width = bbox[2] - bbox[0]
                text = text + "..."
        
        self.draw.text((x, y), text, font=font, fill=color)
    
    def _draw_centered_text(self, text, y, font, color, max_width=None, full_width=False):
        """
        Draw text centered horizontally, with optional truncation
        
        Args:
            text: Text to draw
            y: Y coordinate
            font: Font to use
            color: Text color
            max_width: Maximum width before truncation
            full_width: If True, center in full display width (for splash screen)
        """
        # Truncate if needed
        if max_width:
            bbox = self.draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            if text_width > max_width:
                # Truncate and add ellipsis
                while text_width > max_width and len(text) > 3:
                    text = text[:-1]
                    bbox = self.draw.textbbox((0, 0), text + "...", font=font)
                    text_width = bbox[2] - bbox[0]
                text = text + "..."
        
        # Center the text
        if full_width:
            # Use full width (for splash screen)
            content_width = self.width
        else:
            # Account for potential volume bar
            volume_bar_width = 30 if self._should_show_volume_bar() else 0
            content_width = self.width - volume_bar_width
        
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (content_width - text_width) // 2
        
        self.draw.text((x, y), text, font=font, fill=color)
    
    def _draw_album_art_placeholder(self, x, y, size):
        """
        Draw a placeholder when no album art is available
        
        Args:
            x, y: Top-left coordinates
            size: Size of the square placeholder
        """
        # Dark gray rounded rectangle
        self.draw.rectangle((x, y, x + size, y + size), fill=self.VOLUME_BAR_BG)
        
        # Draw a music note symbol in the center
        note_text = "♪"
        bbox = self.draw.textbbox((0, 0), note_text, font=self.font_splash)
        note_width = bbox[2] - bbox[0]
        note_height = bbox[3] - bbox[1]
        note_x = x + (size - note_width) // 2
        note_y = y + (size - note_height) // 2
        self.draw.text((note_x, note_y), note_text, font=self.font_splash, fill=self.GRAY)
    
    def _extract_metadata(self, filename):
        """
        Extract song name and album from MP3 metadata
        
        Args:
            filename: Path to MP3 file
            
        Returns:
            Tuple of (song_name, album_name)
        """
        song_name = "Unknown Track"
        album_name = "Unknown Album"
        
        try:
            audio = MP3(filename)
            
            # Try to get title from ID3 tags
            if 'TIT2' in audio:
                song_name = str(audio['TIT2'])
            else:
                # Fallback to filename
                song_name = filename.split('/')[-1].rsplit('.', 1)[0]
            
            # Try to get album from ID3 tags
            if 'TALB' in audio:
                album_name = str(audio['TALB'])
        except:
            # Fallback to filename
            song_name = filename.split('/')[-1].rsplit('.', 1)[0]
        
        return song_name, album_name
        
    def paste_album_art(self, mp3_file, x=None, y=None, size=None, return_image=False):
        """
        Extract and display album art from MP3 file
        
        Args:
            mp3_file: Path to MP3 file
            x: X position (default: centered)
            y: Y position (default: 40)
            size: Size of the square artwork (default: 200)
            return_image: If True, return tuple of (success, image), else just success
        
        Returns:
            If return_image is True: tuple of (success, PIL.Image or None)
            If return_image is False: True if album art was found and displayed, False otherwise
        """
        if size is None:
            size = 200
        if x is None:
            x = (self.width - 30 - size) // 2  # Account for volume bar
        if y is None:
            y = 20
            
        try:
            audio = ID3(mp3_file)
            
            # Look for album art in APIC frames
            for tag in audio.values():
                if isinstance(tag, APIC):
                    # Load image from tag data
                    artwork = Image.open(io.BytesIO(tag.data))
                    
                    # Resize to fit display
                    artwork = artwork.resize((size, size), Image.LANCZOS)
                    
                    # Paste onto display image
                    self.image.paste(artwork, (x, y))
                    
                    if return_image:
                        return True, artwork
                    return True
        except:
            pass
        
        if return_image:
            return False, None
        return False