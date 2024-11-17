import customtkinter
from tkinter import messagebox, font
from client import Client, hash_key
from text_editor import TextEditor
import os

# Set appearance and theme
current_dir = os.path.dirname(os.path.abspath(__file__))
theme_path = os.path.join(current_dir, "theme.json")
ico_path = os.path.join(current_dir, "icon.ico")
customtkinter.set_appearance_mode("system")
customtkinter.set_default_color_theme("dark-blue")

text_editor_frame = None  # Initialize globally

# Function to request new copy of document
def request_new_copy():
    print("Requesting new copy from the server...")
    # Future implementation to request the server copy of the document

# Main GUI for text editor
def launch_text_editor(client_name, clients=[], debug_mode=False):
    global text_editor_frame
    customtkinter.set_appearance_mode("light")
    try:
        customtkinter.set_default_color_theme(theme_path)
    except Exception as e:
        print(f"Error loading theme from {theme_path}: {e}")
        customtkinter.set_default_color_theme("blue")  # Fallback to default theme

    editor_root = customtkinter.CTk()
    editor_root.title("CoWrite Text Editor")
    if os.path.exists(ico_path):
        editor_root.iconbitmap(ico_path)
    editor_root.geometry("900x700") 

    frame = customtkinter.CTkFrame(master=editor_root, fg_color="#D9D9D9")
    frame.pack(pady=10, padx=10, fill="both", expand=True)

    # Toolbar Frame
    toolbar_frame = customtkinter.CTkFrame(master=frame, fg_color="#E8E8E8")
    toolbar_frame.pack(fill="x", padx=5, pady=5)

    # Text Editor
    text_editor_frame = TextEditor(
        frame,
        client_name=client_name,
        clients=clients,
        debug_mode=debug_mode,
        request_new_copy_callback=request_new_copy  # Pass the callback here
    )
    text_editor_frame.pack(pady=10, padx=10, fill="both", expand=True)

    text_editor = text_editor_frame.text_editor

    # State variables for font customization
    current_font = font.Font(family="Segoe UI", size=12)
    bold_active = False
    italic_active = False

    def toggle_bold():
        nonlocal bold_active
        bold_active = not bold_active
        update_font()

    def toggle_italic():
        nonlocal italic_active
        italic_active = not italic_active
        update_font()

    def update_font():
        font_weight = "bold" if bold_active else "normal"
        font_slant = "italic" if italic_active else "roman"
        current_font.config(weight=font_weight, slant=font_slant)
        text_editor.configure(font=current_font)

    def change_font_style(new_font):
        current_font.config(family=new_font)
        text_editor.configure(font=current_font)

    def change_font_size(new_size):
        current_font.config(size=new_size)
        text_editor.configure(font=current_font)

    def save_file():
        file_content = text_editor.get("1.0", "end-1c")
        with open("output.txt", "w") as file:
            file.write(file_content)
        messagebox.showinfo("Saved", "File saved successfully!")

    # Toolbar Buttons
    bold_button = customtkinter.CTkButton(toolbar_frame, text="Bold", command=toggle_bold, width=10)
    bold_button.pack(side="left", padx=5)

    italic_button = customtkinter.CTkButton(toolbar_frame, text="Italic", command=toggle_italic, width=10)
    italic_button.pack(side="left", padx=5)

    # Font Style Dropdown
    font_styles = ["Segoe UI", "Arial", "Courier", "Times New Roman", "Helvetica", "Verdana"]
    font_style_menu = customtkinter.CTkOptionMenu(toolbar_frame, values=font_styles, command=change_font_style)
    font_style_menu.set("Segoe UI")
    font_style_menu.pack(side="left", padx=5)

    # Font Size Dropdown
    font_sizes = [str(size) for size in range(8, 32, 2)]
    font_size_menu = customtkinter.CTkOptionMenu(toolbar_frame, values=font_sizes, command=lambda size: change_font_size(int(size)))
    font_size_menu.set("12")
    font_size_menu.pack(side="left", padx=5)

    # Save Button
    save_button = customtkinter.CTkButton(toolbar_frame, text="Save", command=save_file)
    save_button.pack(side="left", padx=5)

    # If in debug mode, add client switching buttons and controls
    if debug_mode:
        text_editor_frame.create_debug_controls(toolbar_frame)

    editor_root.mainloop()

# Main GUI for connection
def launch_connection_gui():
    root = customtkinter.CTk()
    root.title("CoWrite Client")
    root.geometry("720x540")  # Increased window size
    if os.path.exists(ico_path):
        root.iconbitmap(ico_path)

    # Frame
    frame = customtkinter.CTkFrame(master=root)
    frame.pack(pady=20, padx=60, fill="both", expand=True)

    # Label
    label = customtkinter.CTkLabel(master=frame, text="Connect To Host", font=("Segoe UI", 30))
    label.pack(pady=24, padx=20)

    # Name Field
    name_entry = customtkinter.CTkEntry(master=frame, placeholder_text="Your Name", font=("Segoe UI", 15))
    name_entry.pack(pady=12, padx=10)

    # Fields
    entry1 = customtkinter.CTkEntry(master=frame, placeholder_text="IP", font=("Segoe UI", 15))
    entry1.pack(pady=12, padx=10)

    entry2 = customtkinter.CTkEntry(master=frame, placeholder_text="Port", font=("Segoe UI", 15))
    entry2.pack(pady=12, padx=10)

    entry3 = customtkinter.CTkEntry(master=frame, placeholder_text="Key (Password)", font=("Segoe UI", 15), show="*")
    entry3.pack(pady=12, padx=10)

    # Connect button
    def handle_connect():
        name = name_entry.get()
        ip = entry1.get()
        port = entry2.get()
        key = entry3.get()

        if not name or not ip or not port or not key:
            messagebox.showerror("Error", "All fields are required!")
            return

        hashed_key = hash_key(key)
        # Placeholder logic to connect to the server
        print(f"Connecting as {name} to {ip}:{port} with hashed key: {hashed_key}")

        # Simulating success/failure
        success = True  # Replace with actual logic
        if success:
            request_new_copy()  # Call the function upon successful connection
            root.destroy()
            launch_text_editor(client_name=name)
        else:
            messagebox.showerror("Error", "Connection failed. Please try again.")

    button = customtkinter.CTkButton(master=frame, text="Connect", command=handle_connect)
    button.pack(pady=12, padx=10)

    # Debug button
    def handle_debug():
        name = name_entry.get() or "Client1"
        root.destroy()
        # In debug mode, we can define multiple clients
        clients = [Client(f"Client{i+1}", color) for i, color in enumerate(['#FF6666', '#66FF66', '#6666FF'])]
        launch_text_editor(client_name=name, clients=clients, debug_mode=True)

    debug_button = customtkinter.CTkButton(master=frame, text="Debug Mode", command=handle_debug)
    debug_button.pack(pady=12, padx=10)

    root.mainloop()

if __name__ == "__main__":
    launch_connection_gui()
