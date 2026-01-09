import os
import time
import datetime
from typing import List, Dict, Any
import threading

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
        
        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _get_element_info(self, x: int, y: int) -> Dict[str, str]:
        try:
            with auto.UIAutomationInitializerInThread():
                element = auto.ControlFromPoint(x, y)
                name = element.Name if element.Name else "Elemento desconocido"
                control_type = element.ControlTypeName if hasattr(element, 'ControlTypeName') else str(element.ControlType)
                return {"name": name, "type": control_type}
        except Exception as e:
            print(f"Error getting element info: {e}")
            return {"name": "Elemento desconocido", "type": "Unknown", "error": str(e)}

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

    def _on_click(self, x, y, button, pressed):
        if not self.running:
            return

        if pressed and button == mouse.Button.left:
            # We delay slightly to ensure the UI is stable or to catch the click effect if needed
            # But usually for 'before' state or 'during' state, immediate is okay.
            # User request: "Detectar el elemento ... Tomar una captura"
            
            # Using threading to avoid blocking the input listener
            threading.Thread(target=self._process_click, args=(x, y)).start()

    def _process_click(self, x, y):
        # 1. Detect Element
        element_info = self._get_element_info(x, y)
        element_name = element_info.get("name", "Unknown")
        
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
            "element_type": element_info.get("type", "Unknown"),
            "screenshot": screenshot_path,
            "description": f"Clic en {element_name}"
        }
        
        self.steps.append(step)
        print(f"[Captured] {step['description']} at {x}, {y}")

    def _on_press(self, key):
        if key == keyboard.Key.esc:
            print("Esc pressed. Stopping capture...")
            self.stop()
            return False # Stop listener

    def start(self):
        self.running = True
        self.steps = []
        print("Starting capture engine. Press 'Esc' to stop.")
        
        # Setup Listeners
        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self._on_press)
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        # Block main thread until listeners stop (which happens on Esc)
        self.keyboard_listener.join()
        
        # Cleanup
        if self.mouse_listener.is_alive():
            self.mouse_listener.stop()

    def stop(self):
        self.running = False
        if self.mouse_listener and self.mouse_listener.is_alive():
            self.mouse_listener.stop()
        if self.keyboard_listener and self.keyboard_listener.is_alive():
            self.keyboard_listener.stop()

    def get_steps(self):
        return self.steps
