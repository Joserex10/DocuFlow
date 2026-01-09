import os
import time
import datetime
import threading
from typing import List, Dict, Any

import uiautomation as auto
from pynput import mouse, keyboard
from PIL import ImageGrab

class CaptureEngine:
    def __init__(self, output_dir: str = "temp_screenshots"):
        self.output_dir = output_dir
        self.steps: List[Dict[str, Any]] = []
        self.running = False
        self.mouse_listener = None
        self.keyboard_listener = None
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Keyboard buffer (list of chars)
        self.text_buffer: List[str] = []
        
        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _get_element_info(self, x: int, y: int) -> Dict[str, str]:
        try:
            with auto.UIAutomationInitializerInThread():
                element = auto.ControlFromPoint(x, y)
                name = element.Name if element.Name else None
                control_type = element.ControlTypeName if hasattr(element, 'ControlTypeName') else str(element.ControlType)
                return {"name": name, "type": control_type}
        except Exception as e:
            print(f"Error getting element info: {e}")
            return {"name": None, "type": "Unknown", "error": str(e)}

    def _take_screenshot(self) -> str:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            screenshot = ImageGrab.grab()
            screenshot.save(filepath)
            return filepath
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return ""

    def _flush_buffer(self, suffix: str = ""):
        """
        Creates a step from the current text buffer and clears it.
        """
        text_content = "".join(self.text_buffer)
        if not text_content:
            return

        # Take screenshot for the typing step as requested for consistency
        screenshot_path = self._take_screenshot()
        
        description = f'Escribir "{text_content}"{suffix}'
        
        step = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": "type",
            "text": text_content,
            "screenshot": screenshot_path,
            "description": description,
            "element_name": "Teclado",
            "element_type": "Input",
            "coordinates": None
        }
        
        self.steps.append(step)
        print(f"[Captured] {description}")
        
        self.text_buffer = []

    def _on_click(self, x, y, button, pressed):
        if not self.running:
            return

        if pressed and button == mouse.Button.left:
             threading.Thread(target=self._process_click, args=(x, y)).start()

    def _process_click(self, x, y):
        with self.lock:
            # Check for typing before click
            if self.text_buffer:
                self._flush_buffer()
        
            # 1. Detect Element
            element_info = self._get_element_info(x, y)
            element_name = element_info.get("name")
            element_type = element_info.get("type", "Unknown")
            
            # Determine description and fallback for name
            if not element_name or element_name == "Elemento desconocido" or element_name.strip() == "":
                 description = "Haz clic en la zona resaltada (ver imagen)"
                 element_name = "Zona Interactiva"
            else:
                 description = f"Clic en {element_name}"

            # 2. Screenshot
            screenshot_path = self._take_screenshot()
            
            # 2.5 Draw Indicator
            if screenshot_path:
                try:
                    from utils.image_processor import draw_indicator
                    draw_indicator(screenshot_path, x, y)
                except Exception as e:
                    print(f"Failed to draw indicator: {e}")
            
            # 3. Store Step
            step = {
                "timestamp": datetime.datetime.now().isoformat(),
                "action": "click",
                "button": "left",
                "coordinates": (x, y),
                "element_name": element_name,
                "element_type": element_type,
                "screenshot": screenshot_path,
                "description": description
            }
            
            self.steps.append(step)
            print(f"[Captured] {description} at {x}, {y}")

    def _on_press(self, key):
        if key == keyboard.Key.esc:
            print("Esc pressed. Stopping capture...")
            self.stop()
            return False

        with self.lock:
            # Handle buffer limits? (optional, preventing huge memory usage)
            
            if key == keyboard.Key.enter:
                self._flush_buffer(suffix=" y presionar Enter")
            
            elif key == keyboard.Key.backspace:
                if self.text_buffer:
                    self.text_buffer.pop()
            
            elif key == keyboard.Key.space:
                self.text_buffer.append(" ")
                
            else:
                # Ignore special keys, capture only printable
                try:
                    if hasattr(key, 'char') and key.char:
                        self.text_buffer.append(key.char)
                except AttributeError:
                    pass

    def start(self):
        self.running = True
        self.steps = []
        self.text_buffer = []
        print("Starting capture engine. Press 'Esc' to stop.")
        
        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self._on_press)
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        self.keyboard_listener.join()
        
        if self.mouse_listener.is_alive():
            self.mouse_listener.stop()

    def stop(self):
        self.running = False
        if self.mouse_listener and self.mouse_listener.is_alive():
            self.mouse_listener.stop()
        if self.keyboard_listener and self.keyboard_listener.is_alive():
            self.keyboard_listener.stop()

    def get_steps(self):
        # We might want to flush if there's remaining text when stopping?
        # User requirement didn't specify, but it's good practice.
        # However, flushing implies taking a screenshot, which might be weird after Esc.
        # I'll skipped flushing on stop for now unless user asks, or maybe just save the text without screenshot?
        # Let's keep it simple as requested.
        return self.steps
