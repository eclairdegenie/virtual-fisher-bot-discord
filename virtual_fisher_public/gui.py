import customtkinter
import tkinter
from main import VerificationBot
import threading

# Configuration
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Human-Like Auto-Bot Controller")
        self.geometry("600x700")

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) # Log area expands (Moved to row 3)

        # Header
        self.label = customtkinter.CTkLabel(self, text="Human-Like Auto-Bot", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=20)

        # Buttons Frame
        self.button_frame = customtkinter.CTkFrame(self)
        self.button_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)

        self.start_button = customtkinter.CTkButton(self.button_frame, text="START BOT", command=self.start_bot, fg_color="green", hover_color="darkgreen")
        self.start_button.grid(row=0, column=0, padx=10, pady=10)

        self.stop_button = customtkinter.CTkButton(self.button_frame, text="STOP BOT", command=self.stop_bot, fg_color="red", hover_color="darkred", state="disabled")
        self.stop_button.grid(row=0, column=1, padx=10, pady=10)

        # Settings & Commands Frame
        self.settings_frame = customtkinter.CTkFrame(self)
        self.settings_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.settings_frame.grid_columnconfigure(0, weight=1)

        # Cooldown Slider
        self.cooldown_label = customtkinter.CTkLabel(self.settings_frame, text="Cooldown: 3.0s")
        self.cooldown_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        
        self.cooldown_slider = customtkinter.CTkSlider(self.settings_frame, from_=1, to=10, number_of_steps=18, command=self.update_cooldown)
        self.cooldown_slider.set(3.0)
        self.cooldown_slider.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        # Quick Commands
        self.cmd_frame = customtkinter.CTkFrame(self.settings_frame, fg_color="transparent")
        self.cmd_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.cmd_frame.grid_columnconfigure((0, 1), weight=1)

        self.btn_rod = customtkinter.CTkButton(self.cmd_frame, text="Rod Support", command=self.send_rod_support)
        self.btn_rod.grid(row=0, column=0, padx=5, pady=5)

        self.btn_sell = customtkinter.CTkButton(self.cmd_frame, text="Sell All", command=self.send_sell_all, fg_color="orange", hover_color="darkorange")
        self.btn_sell.grid(row=0, column=1, padx=5, pady=5)

        # Custom Command
        self.custom_cmd_entry = customtkinter.CTkEntry(self.settings_frame, placeholder_text="Type command (e.g. /info)")
        self.custom_cmd_entry.grid(row=3, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        self.btn_send_custom = customtkinter.CTkButton(self.settings_frame, text="Send Custom Command", command=self.send_custom_command)
        self.btn_send_custom.grid(row=4, column=0, padx=10, pady=(0, 10))

        # Log Area
        self.log_textbox = customtkinter.CTkTextbox(self, width=500, height=300)
        self.log_textbox.grid(row=3, column=0, padx=20, pady=20, sticky="nsew")
        self.log_textbox.configure(state="disabled") # Read-only

        # Bot Instance
        self.bot = VerificationBot(log_callback=self.append_log)

    def append_log(self, message):
        """Callback to add message to the text box in a thread-safe way."""
        def _update():
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", message + "\n")
            self.log_textbox.see("end") # Auto-scroll
            self.log_textbox.configure(state="disabled")
        
        self.after(0, _update)

    def start_bot(self):
        self.append_log(">>> Starting Bot...")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.bot.start()

    def stop_bot(self):
        self.append_log(">>> Stopping Bot...")
        self.bot.stop()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def update_cooldown(self, value):
        self.cooldown_label.configure(text=f"Cooldown: {round(value, 1)}s")
        self.bot.cooldown = value
        self.append_log(f"Cooldown updated to {round(value, 1)}s")

    def send_rod_support(self):
        self.bot.manual_send_command("/rod supporter rod")

    def send_sell_all(self):
        self.bot.manual_send_command("/sell all")

    def send_custom_command(self):
        cmd = self.custom_cmd_entry.get()
        if cmd:
            self.bot.manual_send_command(cmd)
            self.custom_cmd_entry.delete(0, "end")

    def on_closing(self):
        if self.bot.running:
            self.bot.stop()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
