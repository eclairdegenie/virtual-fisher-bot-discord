import pyautogui
import time
import random
import os
import sys
import math
import numpy as np
import easyocr
import requests
import datetime
import config
import config
import re
from PIL import Image, ImageOps, ImageEnhance 

# Fix for Windows Unicode errors during EasyOCR download
sys.stdout.reconfigure(encoding='utf-8')

# Safety fail-safe
pyautogui.FAILSAFE = True

# Image file to look for
TARGET_IMAGE = "target_button.png"
CHAT_INPUT_IMAGE = "chat_input.png"
VERIFY_HEADER_IMAGE = "verify_header.png"

# Global Reader (load once)
print("Loading AI Model (EasyOCR)... this may take a moment.")
READER = easyocr.Reader(['en'], gpu=False) # Set gpu=True if CUDA is available

def human_sleep(base_seconds=4.0, variation=0.5):
    """Sleeps for a base amount of +/- random variation."""
    delay = base_seconds + random.uniform(-variation, variation)
    if delay < 0: delay = 0
    print(f"DEBUG: Sleeping for {delay:.2f} seconds...")
    time.sleep(delay)

def send_pushover_alert(message):
    """Sends a push notification via Pushover."""
    if "YOUR_PUSHOVER" in config.PUSHOVER_USER_KEY:
        return # Not configured
    
    url = "https://api.pushover.net/1/messages.json"
    payload = {
        "token": config.PUSHOVER_API_TOKEN,
        "user": config.PUSHOVER_USER_KEY,
        "message": message,
        "priority": 1 # High priority
    }
    try:
        requests.post(url, data=payload, timeout=5)
        print("Pushover notification sent.")
    except Exception as e:
        print(f"Failed to send pushover: {e}")

def send_alert(message):
    """Unified alert system (Telegram + Pushover)."""
    # 1. Telegram
    if "YOUR_TOKEN" not in config.TELEGRAM_TOKEN:
        print(f"SENDING TELEGRAM: {message}")
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": f"🚨 [BOT ALERT] 🚨\n{message}"
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Failed to send telegram: {e}")
    
    # 2. Pushover
    send_pushover_alert(message)

# Legacy alias
send_telegram_alert = send_alert

def check_for_danger_on_screen():
    """
    Captures screen, reads text, checks for danger words.
    Returns (True, found_words) if danger is detected.
    """
    print("Running AI Security Scan...")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 0. Check for explicit header image first (User Request)
    header_loc = None
    try:
        if os.path.exists(VERIFY_HEADER_IMAGE):
            # Find ALL occurrences
            all_headers = list(pyautogui.locateAllOnScreen(VERIFY_HEADER_IMAGE, confidence=0.8))
            if all_headers:
                # Sort by 'top' (Y coordinate) ascending -> Last item is at the bottom
                all_headers.sort(key=lambda b: b.top)
                header_loc = all_headers[-1]
                
                print(f"CRITICAL: Verification Header found at {header_loc} (Bottom-most of {len(all_headers)})")
                screenshot_path = f"security_scan_{timestamp}_header.png"
                pyautogui.screenshot(screenshot_path)
                return True, ["HEADER_DETECTED"], screenshot_path, header_loc
    except Exception as e:
        print(f"Header check error: {repr(e)}")

    # 1. Capture screen
    screenshot_path = f"security_scan_{timestamp}.png"
    screenshot = pyautogui.screenshot()
    screenshot.save(screenshot_path)
    
    # 2. Read text
    try:
        # detail=0 gives simple list of text
        results = READER.readtext(screenshot_path, detail=0)
        detected_text = " ".join(results).lower()
        print(f"AI Read: {detected_text[:100]}...") # Print first 100 chars
        
        found_dangers = []
        for danger in config.DANGER_WORDS:
            if danger.lower() in detected_text:
                found_dangers.append(danger)
        
        if found_dangers:
            return True, found_dangers, screenshot_path, None
        
        # Cleanup if safe
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            
        return False, [], None, None
        
    except Exception as e:
        print(f"AI Scan Failed: {repr(e)}")
        return False, [], None, None

def get_bezier_point(t, p0, p1, p2, p3):
    """Calculates a point on a cubic Bezier curve."""
    return (1-t)**3 * p0 + 3 * (1-t)**2 * t * p1 + 3 * (1-t) * t**2 * p2 + t**3 * p3

def get_random_point_in_box(box):
    """
    Returns a random (x, y) point within the box (left, top, width, height)
    using a Gaussian distribution centered on the box.
    """
    left, top, width, height = box
    
    # PADDING: Never click exactly on the edge
    padding = 5
    if width > 10: 
        left += padding
        width -= 2*padding
    if height > 10: 
        top += padding
        height -= 2*padding

    center_x = left + width / 2
    center_y = top + height / 2
    
    # Sigma controls the spread. Width/10 is much safer (more center-focused)
    sigma_x = width / 10
    sigma_y = height / 10
    
    while True:
        x = random.gauss(center_x, sigma_x)
        y = random.gauss(center_y, sigma_y)
        
        # Ensure point is actually inside valid bounds
        if left < x < left + width and top < y < top + height:
            return int(x), int(y)

def human_move_to(target_x, target_y, duration=1.0, overshoot=True):
    """
    Moves mouse to target using a human-like Bezier curve.
    Optionally adds overshoot behavior.
    """
    start_x, start_y = pyautogui.position()
    dist = math.hypot(target_x - start_x, target_y - start_y)
    
    # Reaction time: Wait a tiny bit (simulating brain processing)
    # 100ms to 300ms reaction time
    time.sleep(random.uniform(0.1, 0.3))

    # Overshoot logic: occasionally pick a fake target past the real one
    # Only if distance is significant > 50px
    if overshoot and dist > 50 and random.random() < 0.3: # 30% chance
        print("DEBUG: Overshooting...")
        overshoot_scale = min(dist * 0.1, 50) # Max 50px overshoot
        
        # Calculate vector to target
        dx = target_x - start_x
        dy = target_y - start_y
        
        # Extend it
        fake_target_x = target_x + (dx / dist) * random.uniform(20, overshoot_scale)
        fake_target_y = target_y + (dy / dist) * random.uniform(20, overshoot_scale)
        
        # Add lateral variation/error
        fake_target_x += random.uniform(-20, 20)
        fake_target_y += random.uniform(-20, 20)
        
        # Move to fake target first (faster)
        _perform_bezier_move(start_x, start_y, fake_target_x, fake_target_y, duration * 0.8)
        
        # Correction move (slower, precise)
        time.sleep(random.uniform(0.05, 0.1)) # pause to realize mistake
        _perform_bezier_move(fake_target_x, fake_target_y, target_x, target_y, duration * 0.4)
        
    else:
        # Normal move
        _perform_bezier_move(start_x, start_y, target_x, target_y, duration)

def _perform_bezier_move(start_x, start_y, target_x, target_y, duration):
    """Internal helper to execute the Bezier path generation and movement."""
    # Random offsets for control points
    dist = math.hypot(target_x - start_x, target_y - start_y)
    offset_scale = dist * 0.1 # Smoother curve (was 0.25)
     
    p0 = np.array([start_x, start_y])
    p3 = np.array([target_x, target_y])
    
    # Control points - reduced randomness to avoid "wild" swipes
    p1 = p0 + (p3 - p0) * 0.33 + np.array([random.uniform(-offset_scale, offset_scale), random.uniform(-offset_scale, offset_scale)])
    p2 = p0 + (p3 - p0) * 0.66 + np.array([random.uniform(-offset_scale, offset_scale), random.uniform(-offset_scale, offset_scale)])
    
    steps = int(duration * 60)
    if steps < 5: steps = 5
    
    for i in range(steps + 1):
        t = i / steps
        ease_t = t * t * (3 - 2 * t)
        point = get_bezier_point(ease_t, p0, p1, p2, p3)
        pyautogui.moveTo(point[0], point[1], _pause=False)
        time.sleep(duration / steps)


import threading

class VerificationBot:
    def __init__(self, log_callback=None, cooldown=3.0):
        self.running = False
        self.log_callback = log_callback
        self.thread = None
        self.cooldown = cooldown
        self.input_lock = threading.Lock()
        self.last_update_id = 0
        self.listener_active = True
        
        # Start Telegram Listener IMMEDIATELY (Daemon)
        threading.Thread(target=self._telegram_listener, daemon=True).start()

    def manual_send_command(self, command):
        """Public method to send a command from the GUI."""
        self.log(f"Manual Command Requested: {command}")
        # We need to run this in a thread or ensure it doesn't block the GUI if called directly
        # Since pyautgui controls mouse, it is blocking. 
        # Ideally, we inject this into the main loop or run it if not running.
        # For simplicity, if the bot is RUNNING, we assume the user wants to interrupt or do it now.
        # But `pyautogui` is not thread safe if two threads use it at once. 
        # A simple lock or "busy" check would be good, but for now we will just attempt it.
        # BETTER: If running, we might clash. But `_send_text_to_chat` is robust enough to retry?
        # Let's just run it. The `_run_loop` sleeps often.
        threading.Thread(target=self._send_text_to_chat, args=(command,), daemon=True).start()

    def log(self, message):
        print(message)
        if self.log_callback:
            self.log_callback(message)

    def start(self):
        if self.running:
            self.log("Bot is already running.")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
        self.log("Bot STARTED.")

    def stop(self):
        self.running = False
        self.log("Stopping bot... please wait for current action to finish.")

    def perform_sell_routine(self):
        """Finds chat, types /sell all, and submits."""
        self.log("Initiating SELL ROUTINE...")
        # Use LOCK to prevent conflict with other threads (avoids "3-finger" cursor jumps)
        with self.input_lock:
            try:
                # Look for chat input (Bottom 300px only)
                screen_w, screen_h = pyautogui.size()
                region = (0, screen_h - 300, screen_w, 300)
                location = pyautogui.locateOnScreen(CHAT_INPUT_IMAGE, confidence=0.8, region=region)
                if location:
                    self.log(f"Chat input found at: {location}")
                    # Click chat - use Gaussian randomization
                    target_x, target_y = get_random_point_in_box(location)
                     
                    # NO OVERSHOOT for UI elements - too risky for focus loss
                    human_move_to(target_x, target_y, duration=random.uniform(0.6, 1.2), overshoot=False)
                    pyautogui.click()
                    time.sleep(random.uniform(0.2, 0.5))
                    
                    # Type command
                    self.log("Typing command...")
                    pyautogui.write("/sell all", interval=random.uniform(0.05, 0.15))
                    time.sleep(random.uniform(0.2, 0.5))
                    
                    # Press Enter
                    pyautogui.press('enter')
                    self.log("Command submitted.")
                    time.sleep(random.uniform(0.5, 1.0)) # Wait a bit before resuming fishing
                    return True
                else:
                    self.log("Chat input NOT found. Skipping sell routine.")
                    return False
            except Exception as e:
                self.log(f"Error in sell routine: {e}")
                return False

    def _run_loop(self):
        # Initial check for images
        if not os.path.exists(TARGET_IMAGE):
            self.log(f"ERROR: Image '{TARGET_IMAGE}' not found.")
            self.running = False
            return
        
        click_count = 0
        sell_target = random.randint(90, 110)
        self.log(f"Next sell routine scheduled after {sell_target} clicks.")
        
        consecutive_failures = 0
        MAX_FAILURES = 5

        # Timer states for periodic commands
        last_treasure_time = 0
        last_fish_time = 0
        
        # Helper to send chat command
        def send_chat_command(command, log_func):
            try:
                log_func(f"Executing Periodic Command: {command}")
                loc = pyautogui.locateOnScreen(CHAT_INPUT_IMAGE, confidence=0.8)
                if loc:
                    tx, ty = get_random_point_in_box(loc)
                    human_move_to(tx, ty, duration=0.8, overshoot=True)
                    pyautogui.click()
                    time.sleep(random.uniform(0.3, 0.6))
                    pyautogui.write(command, interval=0.1)
                    pyautogui.press('enter')
                    time.sleep(1.0)
                    return True
                else:
                    log_func("Chat input not found for command.")
                    return False
            except Exception as e:
                log_func(f"Error sending command: {e}")
                return False

        try:
            while self.running:
                # 1. Search (loop logic)
                location = None
                try:
                    location = pyautogui.locateOnScreen(TARGET_IMAGE, confidence=0.8)
                except Exception:
                    location = None

                if location:
                    consecutive_failures = 0
                    
                    # --- 0. SAFELY EXECUTE PERIODIC COMMANDS ---
                    # Only buy if we are safely finding the target (not in a captcha)
                    now = time.time()
                    
                    # Check Treasure 20m (1200 seconds)
                    if now - last_treasure_time > 1200:
                        self.log("Safe to buy: Time for /buy Treasure20m")
                        # We pause fishing specifically to do this
                        if send_chat_command("/buy Treasure20m", self.log):
                            last_treasure_time = now
                            # Small sleep to let UI recover
                            time.sleep(1.0)
                            continue # Restart search loop to re-acquire target
                    
                    # Check Fish 5m (300 seconds)
                    if now - last_fish_time > 300:
                        self.log("Safe to buy: Time for /buy Fish5m")
                        if send_chat_command("/buy Fish5m", self.log):
                            last_fish_time = now
                            time.sleep(1.0)
                            continue 
                    
                    self.log(f"Target found at: {location}")
                    
                    target_x, target_y = get_random_point_in_box(location)
                    move_duration = random.uniform(0.6, 1.5)
                    human_move_to(target_x, target_y, duration=move_duration, overshoot=True)
                    
                    self.log("Clicking...")
                    pyautogui.click()
                    click_count += 1
                    
                    # Sell Routine
                    if click_count >= sell_target:
                        self.log("Sell target reached!")
                        if self.perform_sell_routine():
                             click_count = 0
                             sell_target = random.randint(90, 110)
                             self.log(f"Resetting counter. Next sell at {sell_target}.")
                        else:
                             self.log("Sell routine failed/skipped.")

                    human_sleep(base_seconds=self.cooldown, variation=0.5)
                
                else:
                    consecutive_failures += 1
                    # self.log(f"Target NOT found ({consecutive_failures}/{MAX_FAILURES})...")
                    
                    if consecutive_failures >= MAX_FAILURES:
                        self.log("WARNING: Target lost. Checking for ANOMALY...")
                        is_danger, words, scan_img, header_loc = check_for_danger_on_screen()
                        
                        # CAPTCHA SOLVER CHECK
                        self.log(f"Anomaly detected. Words found: {words}")
                        
                        if is_danger:
                            # Try to solve
                            if self._attempt_solve_captcha(scan_img, header_loc=header_loc):
                                consecutive_failures = 0
                                scan_img_clean(scan_img)
                                continue # Resume fishing
                            
                            # If we get here, solver failed.
                            msg = f"DANGER DETECTED! Found: {words}. STOPPING."
                            send_telegram_alert(msg)
                            self.log("CRITICAL: BOT STOPPED DUE TO DETECTION.")
                            self.running = False
                            return
                        else:
                            self.log("No danger. Pausing 60s.")
                            send_telegram_alert("Warning: Bot lost track. Pausing 60s.")
                            # Sleep in chunks to allow stopping
                            for _ in range(60):
                                if not self.running: break
                                time.sleep(1)
                            consecutive_failures = 0
                    
                    time.sleep(1.0) # wait before next search attempt

        except Exception as e:
            self.log(f"Unexpected error: {repr(e)}")
            self.running = False

    def _telegram_listener(self):
        """Background thread to listen for remote STOP commands."""
        self.log("Telegram Listener: STARTED")
        if "YOUR_TOKEN" in config.TELEGRAM_TOKEN:
            self.log("Telegram Listener: Token not configured. Stopping listener.")
            return

        base_url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}"
        
        # Runs forever (daemon), independent of main bot loop
        print("DEBUG: Telegram Thread Entered Loop")
        while True:
            try:
                # Long polling (timeout=10s)
                # print(f"DEBUG: Pinging Telegram API (Offset {self.last_update_id})...") 
                url = f"{base_url}/getUpdates?offset={self.last_update_id + 1}&timeout=10"
                resp = requests.get(url, timeout=12)
                
                if resp.status_code != 200:
                     print(f"DEBUG: Telegram API Error {resp.status_code}: {resp.text}")

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok"):
                        for result in data.get("result", []):
                            self.last_update_id = result["update_id"]
                            
                            # Check message text
                            message = result.get("message", {})
                            text = message.get("text", "").strip().upper()
                            chat_id = str(message.get("chat", {}).get("id", ""))
                            
                            print(f"[DEBUG] Telegram Msg: '{text}' from ID: '{chat_id}' (Expected: '{config.TELEGRAM_CHAT_ID}')")
                            
                            # Verify it's from the owner
                            if chat_id == str(config.TELEGRAM_CHAT_ID):
                                if text == "STOP":
                                    if self.running:
                                        self.log("🚨 REMOTE STOP RECEIVED VIA TELEGRAM 🚨")
                                        requests.post(f"{base_url}/sendMessage", json={
                                            "chat_id": chat_id,
                                            "text": "🛑 BOT STOPPED PER REMOTE REQUEST."
                                        })
                                        self.stop()
                                    else:
                                        requests.post(f"{base_url}/sendMessage", json={
                                            "chat_id": chat_id,
                                            "text": "Bot is already stopped."
                                        })
                                
                                elif text == "START":
                                    if not self.running:
                                        self.log("✅ REMOTE START RECEIVED VIA TELEGRAM")
                                        requests.post(f"{base_url}/sendMessage", json={
                                            "chat_id": chat_id,
                                            "text": "✅ BOT STARTING..."
                                        })
                                        # Must call start() from main thread ideally, but threading.Thread is fine here
                                        # self.start() handles re-launching the run_loop
                                        self.start()
                                    else:
                                        requests.post(f"{base_url}/sendMessage", json={
                                            "chat_id": chat_id,
                                            "text": "Bot is already running."
                                        })

            except Exception as e:
                print(f"DEBUG: Telegram Listener Exception: {repr(e)}")
                time.sleep(5) # Wait before retry on network error
                
            time.sleep(1)

    def _attempt_solve_captcha(self, image_path, header_loc=None):
        """
        Analyzes screen for Code OR Instructions (Context-Aware).
        If header_loc is provided, we analyze only the ROI below it.
        """
        self.log("Analyzing validation screen...")
        
        # 0. Crop Logic (Spatial Detection)
        analysis_image = image_path
        if header_loc:
            try:
                # header_loc = (left, top, width, height)
                x, y, w, h = header_loc
                # We want the area BELOW the header.
                # Let's crop from y+h to y+h+200 (approx area where code is)
                # And maybe full width of header +/- 100px? Or full screen width?
                # Safer: Full screen width, but starting from below header.
                
                screen_w, screen_h = pyautogui.size()
                crop_y = int(y + h)
                
                # --- SPATIAL REFINEMENT ---
                # Exclude sidebars by using header's X position.
                # Start 20px to the left of header (buffer)
                start_x = max(0, int(x - 20))
                # End 500px to the right (max captcha width)
                end_x = min(screen_w, int(x + 500))
                
                crop_bottom = min(crop_y + 300, screen_h) # Limit query height to 300px
                
                crop_box = (start_x, crop_y, end_x, crop_bottom)
                
                # We need to open the existing screenshot
                # NOTE: pyautogui.screenshot() returns an Image object, but here we saved it to disk.
                # Let's re-open or if we passed path, use PIL.
                from PIL import Image
                with Image.open(image_path) as img:
                    uncropped = img.crop(crop_box)
                    analysis_image = image_path.replace(".png", "_cropped.png")
                    uncropped.save(analysis_image)
                    self.log(f"Spatial Mode: Analyzing cropped area below header... ({crop_h}px height)")
            
            except Exception as e:
                self.log(f"Crop failed: {e}. Falling back to full image.")
                analysis_image = image_path
        
        # 1. Analyze image
        # Pass strict_6_char_mode=True if we have a header
        code, command, success = self._analyze_security_image(analysis_image, strict_6_char_mode=bool(header_loc))
        
        # 0. Strategy: Success has highest priority
        if success:
            self.log("SUCCESS DETECTED ('You may now continue').")
            self.log("BURST MODE: Sending /fish 10 times (3s interval)...")
            for i in range(10):
                self._send_text_to_chat("/fish")
                time.sleep(3.0)
            self.log("Burst finished. Resuming normal operation.")
            scan_img_clean(analysis_image)
            return True

        # 2. Strategy: Code has priority
        if code:
            msg = f"Code FOUND: {code}. Solving..."
            self.log(msg)
            send_telegram_alert(msg)
            if self._send_text_to_chat(f"/verify {code}"):
                time.sleep(4.0) # Wait for bot response
                
                # --- RETRY LOGIC (New) ---
                # Check for "Incorrect code" message
                check_shot = f"retry_check_{int(time.time())}.png"
                pyautogui.screenshot(check_shot)
                try:
                    res_check = READER.readtext(check_shot, detail=0)
                    text_check = " ".join(res_check).lower()
                    
                    if "incorrect" in text_check or "wrong" in text_check:
                        self.log("❌ Incorrect code detected! Initiating AUTOREGEN...")
                        scan_img_clean(check_shot)
                        scan_img_clean(analysis_image)
                        
                        self.log("Sending /verify regen...")
                        if self._send_text_to_chat("/verify regen"):
                            self.log("Waiting 6s for new captcha...")
                            time.sleep(6.0)
                            
                            # Capture new image and RECURSE (Try again)
                            new_image_path = f"regen_{int(time.time())}.png"
                            pyautogui.screenshot(new_image_path)
                            
                            # CRITICAL FIX: Re-scan for the NEW header position (it will be lower)
                            new_header_loc = None
                            if header_loc:
                                try:
                                    # Find ALL headers again
                                    all_headers = list(pyautogui.locateAllOnScreen(VERIFY_HEADER_IMAGE, confidence=0.8))
                                    if all_headers:
                                        all_headers.sort(key=lambda b: b.top)
                                        new_header_loc = all_headers[-1]
                                        self.log(f"Regen Target Update: New header found at {new_header_loc}")
                                except Exception as e:
                                    self.log(f"Failed to re-scan header: {e}")
                            
                            # Pass the NEW location (or None if failed, forcing full scan)
                            return self._attempt_solve_captcha(new_image_path, new_header_loc)
                        else:
                            self.log("Failed to send regen command.")
                            return False
                    else:
                        self.log("Code submitted. No error detected.")
                except Exception as e:
                    self.log(f"Retry check failed: {e}")
                
                # Cleanup
                scan_img_clean(check_shot)
                scan_img_clean(analysis_image)
                return True
            else:
                self.log("Failed to send code to chat.")
                return False
            
        elif command:
            # If no code, but we see an instruction like "/verify regen"
            msg = f"Instruction FOUND: '{command}'. Executing..."
            self.log(msg)
            # send_telegram_alert(msg) # Optional reduce spam
            if not self._send_text_to_chat(command):
                 self.log(f"Failed to send command: {command}")
                 return False
            
            self.log("Command sent. Waiting 8s for new image...")
            time.sleep(8.0)
            
            # Retry scan logic (2nd pass) with same spatial logic if possible
            # Need to capture new screenshot
            new_shot = image_path.replace(".png", "_retry.png")
            pyautogui.screenshot(new_shot)
            
            # Recurse? Or just manual call? Manual call safer to avoid infinite loop easily
            # Pass 2: Ignore instructions (don't regen again). Strict mode remains if header was found.
            if header_loc:
                 # Need to re-crop new image
                 try:
                    from PIL import Image
                    x, y, w, h = header_loc
                    screen_w, screen_h = pyautogui.size()
                    crop_y = int(y + h)
                    crop_h = 300
                    crop_box = (0, crop_y, screen_w, crop_h)
                    with Image.open(new_shot) as img:
                        uncropped = img.crop(crop_box)
                        analysis_image_2 = new_shot.replace(".png", "_cropped.png")
                        uncropped.save(analysis_image_2)
                 except:
                    analysis_image_2 = new_shot
            else:
                analysis_image_2 = new_shot

            code_2, _, success_2 = self._analyze_security_image(analysis_image_2, ignore_instructions=True, strict_6_char_mode=bool(header_loc))
            
            if success_2:
                self.log("SUCCESS DETECTED after action.")
                self.log("BURST MODE: Sending /fish 10 times (3s interval)...")
                for i in range(10):
                    self._send_text_to_chat("/fish")
                    time.sleep(3.0)
                return True
            
            if code_2:
                msg = f"Code FOUND after action: {code_2}"
                self.log(msg)
                send_telegram_alert(msg)
                if self._send_text_to_chat(f"/verify {code_2}"):
                    time.sleep(10)
                    return True
                else:
                    return False
            else:
                self.log("STILL no code found after executing instruction.")
                return False
                 
        else:
            self.log("No code and no specific instruction found.")
            return False

    def _analyze_security_image(self, image_path, ignore_instructions=False, strict_6_char_mode=False):
        """
        Returns tuple: (found_code, found_command_string, success_bool)
        """
        try:
            # --- PREPROCESSING (Enhanced AI) ---
            # Create a "super" version of the image for better reading
            proc_path = self._preprocess_image_for_ocr(image_path)
            
            results = READER.readtext(proc_path, detail=0)
            full_text = " ".join(results)
            
            # Use original image for fallback analysis if needed, or just trust the processed one.
            # Usually processed is strictly better.
            
            # --- 0. Detect Success ---
            if "continue" in full_text.lower() and "now" in full_text.lower():
                return None, None, True
            
            # --- 1. Detect Instructions ---
            instruction_regen_detected = False
            found_command = None
            
            if not ignore_instructions:
                # Do we see the "regen" command suggested in the text?
                # Regex: Hande "/verify regen", "verify regen", "verify  regen"
                instruction_regen_detected = bool(re.search(r'/?verify\s+regen', full_text, re.IGNORECASE))
                found_command = "/verify regen" if instruction_regen_detected else None

            # --- 2. Look for CODE ---
            # If strictly 6 chars, update regex
            # NEW: Handle spaced characters (e.g. "R d F 9 a L")
            candidates = []
            
            for word in results:
                # 1. Clean the word (remove spaces)
                clean_word = word.replace(" ", "").replace("\n", "").strip()
                
                # 2. Check regex against cleaned word
                if strict_6_char_mode:
                     if re.match(r'^[A-Za-z0-9]{6}$', clean_word):
                         candidates.append(clean_word)
                else:
                     if re.match(r'^[A-Za-z0-9]{5,8}$', clean_word):
                         candidates.append(clean_word)
            
            if strict_6_char_mode:
                self.log("STRICT MODE: Looking only for 6-character codes.")
            
            # Use blacklist from config
            blacklist = config.OCR_BLACKLIST
            
            valid_codes = []
            for c in candidates:
                # Basic blacklist filter
                if c.lower() in blacklist:
                    continue
                
                # STRICT MODE: Only ON if instructions are being respected
                # If ignore_instructions is True (Pass 2), we DISABLE strict mode
                # so we can catch codes that might be letters only.
                if instruction_regen_detected and not strict_6_char_mode: 
                   # REQUIRED: When regen is available, Code MUST have a number to be trusted.
                   has_digit = any(char.isdigit() for char in c)
                   if not has_digit:
                       continue
                
                valid_codes.append(c)

            # Pick the LAST valid code (User requested "lowest on screen")
            # EasyOCR usually returns top-to-bottom.
            found_code = valid_codes[-1] if valid_codes else None
            
            return found_code, found_command, False
            
        except Exception as e:
            self.log(f"OCR Error: {repr(e)}")
            return None, None, False

    def _send_text_to_chat(self, text):
        with self.input_lock:
            try:
                # Constrain search to bottom 300px to avoid false positives (e.g. Copy button in chat)
                screen_w, screen_h = pyautogui.size()
                region = (0, screen_h - 300, screen_w, 300)
                loc = pyautogui.locateOnScreen(CHAT_INPUT_IMAGE, confidence=0.8, region=region)
            except Exception:
                loc = None
            
            if loc:
                tx, ty = get_random_point_in_box(loc)
                human_move_to(tx, ty, duration=0.8, overshoot=False)
                pyautogui.click()
            else:
                self.log("Chat input not found. Using FALLBACK CLICK (Bottom Center).")
                # Fallback: Click bottom center where chat usually is
                sw, sh = pyautogui.size()
                pyautogui.click(sw // 2, sh - 60)
                
            time.sleep(0.5) # Wait for focus
            
            # Slower typing to ensure game registers keystrokes
            pyautogui.write(text, interval=0.25)
            
            time.sleep(1.0) # Wait 1s before pressing Enter (very safe)
            
            # Double Enter (Robust) - Requested by User
            for _ in range(2):
                pyautogui.keyDown('enter')
                time.sleep(0.15)
                pyautogui.keyUp('enter')
                time.sleep(0.2)
            
            # small delay to ensure chat closes or message sends
            time.sleep(0.5) 
            return True

    def _preprocess_image_for_ocr(self, image_path):
        """
        Enhances image for OCR: Scaling, Grayscale, Contrast.
        """
        try:
            with Image.open(image_path) as img:
                # 1. Grayscale
                gray = img.convert('L')
                
                # 2. Scale up (x2) - Huge help for small text
                new_size = tuple(2 * x for x in gray.size)
                scaled = gray.resize(new_size, Image.Resampling.LANCZOS)
                
                # 3. Increase Contrast
                enhancer = ImageEnhance.Contrast(scaled)
                contrasted = enhancer.enhance(2.0)
                
                # 4. Sharpen (Fix S vs 5 confusion)
                sharpener = ImageEnhance.Sharpness(contrasted)
                final = sharpener.enhance(2.0)
                
                out_path = image_path.replace(".png", "_proc.png")
                final.save(out_path)
                return out_path
        except Exception as e:
            self.log(f"Preprocessing failed: {e}")
            return image_path

def scan_img_clean(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass # Ignore cleanup errors to prevent crashing

if __name__ == "__main__":
    # CLI fallback
    bot = VerificationBot()
    bot.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            bot.stop()
            break
