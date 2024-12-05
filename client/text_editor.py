import customtkinter
from tkinter import Text
from client import Client
import threading
import json
import queue

# imagine spending 90% of your time writing a text editor for a distributed systems project

# TODO:
# Line numbers don't update when scrolling
# Line locking visuals don't update 

class TextEditor(customtkinter.CTkFrame):
    def __init__(self, master, client_name, send_queue, receive_queue, clients=[], debug_mode=False, request_new_copy_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.debug_mode = debug_mode
        self.client_name = client_name
        self.send_queue = send_queue
        self.receive_queue = receive_queue
        self.input_buffer = ""
        self.batch_timer = None
        self.batch_interval = 500  # milliseconds
        self.request_new_copy_callback = request_new_copy_callback
        self.cursor_active = False  # Initialize cursor_active
        self.last_cursor_line = '1'

        if debug_mode:
            self.clients = clients
        else:
            self.clients = [Client(client_name, self.generate_color(0))]
        self.current_client = self.get_client_by_name(client_name)

        self.invisible_textboxes = {}
        for client in self.clients:
            invisible_text = Text(self, width=0, height=0)
            invisible_text.pack_forget()
            self.invisible_textboxes[client.name] = invisible_text
            invisible_text.mark_set(client.cursor_mark_name, '1.0')

        self.line_numbers = Text(self, width=4, font=("Segoe UI", 12), state="disabled", bg="#EAEAEA")
        self.text_editor = Text(self, wrap="word", font=("Segoe UI", 12), undo=True, bg="#F5F5F5", fg="#333333")

        self.line_numbers.pack(side="left", fill="y")
        self.text_editor.pack(side="right", fill="both", expand=True)

        self.bind_events()

        self.update_line_numbers()
        self.update_other_cursors()

        self.create_cursor_legend()

        if not self.cursor_active:
            self.cursor_active = True
            self.text_editor.focus_set()
            self.text_editor.mark_set('insert', '1.0')
            self.update_current_cursor()

        # Start a thread to handle incoming messages
        threading.Thread(target=self.handle_incoming_messages, daemon=True).start()

    def bind_events(self):
        self.text_editor.bind("<KeyPress>", self.on_key_press)
        self.text_editor.bind("<KeyRelease>", self.on_key_release)
        self.text_editor.bind("<Button-1>", self.on_mouse_click)
        self.text_editor.bind("<ButtonRelease>", self.on_mouse_release)
        self.text_editor.bind("<B1-Motion>", self.on_mouse_drag)
        self.text_editor.bind("<<Selection>>", self.on_selection)
        self.text_editor.bind("<BackSpace>", self.on_backspace)
        self.text_editor.bind("<Delete>", self.on_delete_key)
        self.text_editor.bind("<KeyRelease>", self.on_cursor_move)
        self.text_editor.bind("<ButtonRelease>", self.on_cursor_move)

        navigation_keys = ["<Up>", "<Down>", "<Left>", "<Right>", "<Home>", "<End>", "<Prior>", "<Next>"]
        for key in navigation_keys:
            self.text_editor.bind(key, self.on_arrow_key)

        # Replace default insert and delete with safe versions
        self.text_editor.original_insert = self.text_editor.insert
        self.text_editor.original_delete = self.text_editor.delete
        self.text_editor.insert = self.safe_insert
        self.text_editor.delete = self.safe_delete

    def generate_color(self, index):
        colors = ['#FF6666', '#66FF66', '#6666FF', '#FFA500', '#FF66FF']
        return colors[index % len(colors)]

    def get_client_by_name(self, name):
        for client in self.clients:
            if client.name == name:
                return client
        return None

    def create_cursor_legend(self):
        if hasattr(self, 'legend_frame'):
            self.legend_frame.destroy()
        self.legend_frame = customtkinter.CTkFrame(self)
        self.legend_frame.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10)

        for client in self.clients:
            if client.name != self.current_client.name:
                color = client.color
                label = customtkinter.CTkLabel(
                    self.legend_frame,
                    text=client.name,
                    fg_color=color,
                    width=80,
                    height=20,
                    corner_radius=5,
                )
                label.pack(pady=2)

    def create_debug_controls(self, parent_frame):
        debug_controls_frame = customtkinter.CTkFrame(parent_frame, fg_color="transparent")
        debug_controls_frame.pack(side='left', padx=5)

        self.client_frame = customtkinter.CTkFrame(master=debug_controls_frame, fg_color="transparent")
        self.client_frame.pack(side='left', padx=5)

        self.update_client_buttons()

        add_remove_frame = customtkinter.CTkFrame(master=debug_controls_frame, fg_color="transparent")
        add_remove_frame.pack(side='left', padx=5)

        add_button = customtkinter.CTkButton(
            add_remove_frame,
            text="Add Client",
            command=self.add_client,
            width=80,
        )
        add_button.pack(side="left", padx=5)

        remove_button = customtkinter.CTkButton(
            add_remove_frame,
            text="Remove Client",
            command=self.remove_client,
            width=100,
        )
        remove_button.pack(side="left", padx=5)

    def update_client_buttons(self):
        for widget in self.client_frame.winfo_children():
            widget.destroy()

        for client in self.clients:
            client_button = customtkinter.CTkButton(
                self.client_frame,
                text=client.name,
                command=lambda c=client.name: self.set_current_client(c),
                width=10
            )
            client_button.pack(side="left", padx=2)

    # debug mode
    def add_client(self):
        new_client_name = f"Client{len(self.clients) + 1}"
        new_client_color = self.generate_color(len(self.clients))
        new_client = Client(new_client_name, new_client_color)
        self.clients.append(new_client)
        invisible_text = Text(self, width=0, height=0)
        invisible_text.pack_forget()
        self.invisible_textboxes[new_client.name] = invisible_text
        invisible_text.mark_set(new_client.cursor_mark_name, '1.0')
        self.create_cursor_legend()
        self.update_client_buttons()
        print(f"Added {new_client_name}")

    # debug mode
    def remove_client(self):
        if len(self.clients) > 1:
            removed_client = self.clients.pop()
            self.text_editor.tag_remove(f"line_lock_{removed_client.name}", "1.0", "end")
            self.text_editor.tag_delete(f"line_lock_{removed_client.name}")
            self.text_editor.mark_unset(removed_client.cursor_mark_name)
            self.invisible_textboxes.pop(removed_client.name, None)
            self.create_cursor_legend()
            self.update_client_buttons()
            print(f"Removed {removed_client.name}")
        else:
            messagebox.showinfo("Info", "Cannot remove the last client.")

    def safe_insert(self, index, chars, *args):
        line_start = f"{index.split('.')[0]}.0"
        tags = self.text_editor.tag_names(line_start)
        for tag in tags:
            if tag.startswith("line_lock_") and tag != f"line_lock_{self.current_client.name}":
                # Cannot insert into a locked line
                return "break"
        self.text_editor.original_insert(index, chars, *args)

    def safe_delete(self, index1, index2=None):
        if index2 is None:
            index2 = index1 + "+1c"
        start_line = int(self.text_editor.index(index1).split('.')[0])
        end_line = int(self.text_editor.index(index2).split('.')[0])
        for line in range(start_line, end_line + 1):
            line_start = f"{line}.0"
            tags = self.text_editor.tag_names(line_start)
            for tag in tags:
                if tag.startswith("line_lock_") and tag != f"line_lock_{self.current_client.name}":
                    # Cannot delete from a locked line
                    return "break"
        self.text_editor.original_delete(index1, index2)

    def on_key_press(self, event=None):
        if not self.cursor_active:
            return "break"
        # Check if the current line is locked by another client
        cursor_pos = self.text_editor.index('insert')
        line_start = f"{cursor_pos.split('.')[0]}.0"
        tags = self.text_editor.tag_names(line_start)
        for tag in tags:
            if tag.startswith("line_lock_") and tag != f"line_lock_{self.current_client.name}":
                # Cannot edit a line locked by another client
                return "break"
        # Append the character to input buffer if it's a printable character or newline/tab
        if event.char and (event.char.isprintable() or event.char in ('\n', '\r', '\t')):
            # Convert carriage return to newline if necessary
            if event.char == '\r':
                self.input_buffer += '\n'
            else:
                self.input_buffer += event.char
            # Start the batch timer if not already running
            if self.batch_timer is None:
                self.batch_timer = self.text_editor.after(self.batch_interval, self.send_batched_input)
        # Allow the key press
        return None


    def on_key_release(self, event=None):
            self.update_current_cursor()
            self.update_line_numbers()
            self.update_other_cursors()
            self.update_line_locks()
            if not self.cursor_active:
                return
            # Start the batch timer if not already running
            if self.batch_timer is None:
                self.batch_timer = self.text_editor.after(self.batch_interval, self.send_batched_input)

    def send_batched_input(self):
        if self.input_buffer:
            cursor_pos = self.text_editor.index('insert')
            index = self.get_char_index(cursor_pos)
            start_index = index - len(self.input_buffer)
            message = {
                'command': 'ADD',
                'clientName': self.client_name,
                'startIndex': start_index,
                'content': self.input_buffer
            }
            print(f"Sending ADD message to server: {message}")  # Debug statement
            self.send_queue.put(json.dumps(message))
            self.input_buffer = ""
        self.batch_timer = None  # Reset the batch timer


    def on_cursor_move(self, event=None):
        if not self.cursor_active:
            return
        if 'insert' not in self.text_editor.mark_names():
            return
        cursor_pos = self.text_editor.index('insert')
        current_line = cursor_pos.split('.')[0]
        if self.last_cursor_line != current_line:
            self.last_cursor_line = current_line
            index = self.get_char_index(cursor_pos)
            message = {
                'command': 'CURSOR_MOVE',
                'clientName': self.current_client.name,
                'cursorLocation': index
            }
            self.send_queue.put(json.dumps(message))
            self.update_line_locks()

    def get_char_index(self, cursor_pos):
        # Convert 'line.column' to a character index
        count = self.text_editor.count("1.0", cursor_pos, "chars")[0]
        return int(count)


    def handle_incoming_messages(self):
        while True:
            try:
                message = self.receive_queue.get()
                self.process_server_message(message)
            except Exception as e:
                print(f"Error handling incoming message: {e}")

    def process_server_message(self, message):
        data = json.loads(message)
        command = data.get('command')
        if command == 'ADD':
            self.apply_add(data)
        elif command == 'REMOVE':
            self.apply_remove(data)
        elif command == 'CURSOR_MOVE':
            self.update_client_cursor(data)
        elif command == 'DOCUMENT':
            self.load_document(data)
        elif command == 'NEWCLIENT':
            self.add_new_client(data)
        elif command == 'CLIENTS_LIST':
            self.add_existing_clients(data)

    def add_existing_clients(self, data):
        client_list = data.get('clientList', [])
        for client_name in client_list:
            if client_name != self.client_name:
                new_client = Client(client_name, self.generate_color(len(self.clients)))
                self.clients.append(new_client)
                # Initialize cursor position and other necessary attributes
                invisible_text = Text(self, width=0, height=0)
                invisible_text.pack_forget()
                self.invisible_textboxes[new_client.name] = invisible_text
                invisible_text.mark_set(new_client.cursor_mark_name, '1.0')
                self.create_cursor_legend()
        self.update_line_locks_visual()
        self.update_line_locks()

    def add_new_client(self, data):
        client_name = data.get('clientName')
        if client_name and client_name != self.client_name:
            new_client = Client(client_name, self.generate_color(len(self.clients)))
            self.clients.append(new_client)
            # Initialize cursor position and other necessary attributes
            invisible_text = Text(self, width=0, height=0)
            invisible_text.pack_forget()
            self.invisible_textboxes[new_client.name] = invisible_text
            invisible_text.mark_set(new_client.cursor_mark_name, '1.0')
            self.create_cursor_legend()
            self.update_line_locks_visual()
            self.update_line_locks()
            print(f"Added new client: {new_client.name}")
        else:
            print(f"Received NEWCLIENT message for self or invalid client: {client_name}")
    
    def apply_add(self, data):
        start_index = data['startIndex']
        content = data['content']
        tk_index = self.get_tk_index(start_index)
        # Insert the content without triggering events
        self.text_editor.event_generate("<<TextModified>>")
        self.text_editor.insert(tk_index, content)

    def apply_remove(self, data):
        start_index = data['startIndex']
        end_index = data['endIndex']
        tk_start = self.get_tk_index(start_index)
        tk_end = self.get_tk_index(end_index)
        # Delete the content without triggering events
        self.text_editor.event_generate("<<TextModified>>")
        self.text_editor.delete(tk_start, tk_end)

    def load_document(self, data):
        content = data.get('content', '')
        self.text_editor.delete('1.0', 'end')
        self.text_editor.insert('1.0', content)

    def update_client_cursor(self, data):
        client_name = data.get('clientName')
        cursor_location = data['cursorLocation']
        client = self.get_client_by_name(client_name)
        if client and client.name != self.current_client.name:
            tk_index = self.get_tk_index(cursor_location)
            self.text_editor.mark_set(client.cursor_mark_name, tk_index)
            self.update_other_cursors()

    def get_tk_index(self, char_index):
        # Convert character index back to 'line.column'
        index = self.text_editor.index(f"1.0 + {char_index} chars")
        return index

    def on_mouse_click(self, event=None):
        index = self.text_editor.index(f"@{event.x},{event.y}")
        line_start = f"{index.split('.')[0]}.0"
        tags = self.text_editor.tag_names(line_start)

        for tag in tags:
            if tag.startswith("line_lock_") and tag != f"line_lock_{self.current_client.name}":
                # Cannot place cursor on a locked line
                return "break"

        self.cursor_active = True
        self.text_editor.focus_set()
        self.text_editor.mark_set('insert', index)
        self.update_current_cursor()
        self.update_other_cursors()
        self.update_line_locks()

    def on_mouse_release(self, event=None):
        self.update_current_cursor()
        self.update_other_cursors()
        self.update_line_locks()

    def on_mouse_drag(self, event=None):
        if not self.cursor_active:
            return "break"

        cursor_pos = self.text_editor.index(f"@{event.x},{event.y}")
        line_start = f"{cursor_pos.split('.')[0]}.0"
        tags = self.text_editor.tag_names(line_start)

        for tag in tags:
            if tag.startswith("line_lock_") and tag != f"line_lock_{self.current_client.name}":
                # Prevent cursor from moving to this line
                return "break"

    def on_selection(self, event=None):
        if not self.cursor_active:
            return

        try:
            selection_start = self.text_editor.index("sel.first")
            selection_end = self.text_editor.index("sel.last")
            # Iterate over each index in selection
            current_index = selection_start
            while current_index != selection_end:
                line_start = f"{current_index.split('.')[0]}.0"
                tags = self.text_editor.tag_names(line_start)
                for tag in tags:
                    if tag.startswith("line_lock_") and tag != f"line_lock_{self.current_client.name}":
                        # Deselect the text
                        self.text_editor.tag_remove("sel", "1.0", "end")
                        return
                current_index = self.text_editor.index(f"{current_index} +1c")
        except Exception:
            pass  # No selection

    def on_backspace(self, event=None):
        if not self.cursor_active:
            return "break"
        cursor_pos = self.text_editor.index('insert')
        if cursor_pos == '1.0':
            # At the beginning of the document
            return "break"
        prev_pos = self.text_editor.index(f"{cursor_pos} -1c")
        prev_line = int(prev_pos.split('.')[0])
        curr_line = int(cursor_pos.split('.')[0])
        if prev_line != curr_line:
            # Moving into the previous line
            line_start = f"{prev_line}.0"
            tags = self.text_editor.tag_names(line_start)
            for tag in tags:
                if tag.startswith("line_lock_") and tag != f"line_lock_{self.current_client.name}":
                    # Cannot backspace into a locked line
                    return "break"
        # Prepare REMOVE message
        start_index = self.get_char_index(prev_pos)
        end_index = self.get_char_index(cursor_pos)
        message = {
            'command': 'REMOVE',
            'clientName': self.client_name,
            'startIndex': start_index,
            'endIndex': end_index
        }
        print(f"Sending REMOVE message to server: {message}")  # Debugging statement
        self.send_queue.put(json.dumps(message))
        # Allow backspace
        return None

    def on_delete_key(self, event=None):
        if not self.cursor_active:
            return "break"
        cursor_pos = self.text_editor.index('insert')
        next_pos = self.text_editor.index(f"{cursor_pos} +1c")
        next_line = int(next_pos.split('.')[0])
        curr_line = int(cursor_pos.split('.')[0])
        if next_line != curr_line:
            line_start = f"{next_line}.0"
            tags = self.text_editor.tag_names(line_start)
            for tag in tags:
                if tag.startswith("line_lock_") and tag != f"line_lock_{self.current_client.name}":
                    return "break"
        # Prepare REMOVE message
        start_index = self.get_char_index(cursor_pos)
        end_index = self.get_char_index(next_pos)
        message = {
            'command': 'REMOVE',
            'clientName': self.client_name,
            'startIndex': start_index,
            'endIndex': end_index
        }
        print(f"Sending REMOVE message to server: {message}")  # Debugging statement
        self.send_queue.put(json.dumps(message))
        # Allow delete
        return None

    def on_cut(self, event=None):
        return self.prevent_edit_on_locked_lines(event)

    def on_clear(self, event=None):
        return self.prevent_edit_on_locked_lines(event)

    def on_paste(self, event=None):
        cursor_pos = self.text_editor.index('insert')
        line_start = f"{cursor_pos.split('.')[0]}.0"
        tags = self.text_editor.tag_names(line_start)

        for tag in tags:
            if tag.startswith("line_lock_") and tag != f"line_lock_{self.current_client.name}":
                # Cannot paste on a locked line
                return "break"

    def on_copy(self, event=None):
        pass  # Copying is allowed

    def prevent_edit_on_locked_lines(self, event=None):
        if not self.cursor_active:
            return "break"

        try:
            selection_start = self.text_editor.index("sel.first")
            selection_end = self.text_editor.index("sel.last")
            # Iterate over each index in selection
            current_index = selection_start
            while current_index != selection_end:
                line_start = f"{current_index.split('.')[0]}.0"
                tags = self.text_editor.tag_names(line_start)
                for tag in tags:
                    if tag.startswith("line_lock_") and tag != f"line_lock_{self.current_client.name}":
                        return "break"
                current_index = self.text_editor.index(f"{current_index} +1c")
        except Exception:
            pass  # No selection

    def on_arrow_key(self, event):
        direction = event.keysym

        current_index = self.text_editor.index('insert')
        try:
            if direction == 'Up':
                new_index = self.text_editor.index(f"{current_index} -1 lines")
            elif direction == 'Down':
                new_index = self.text_editor.index(f"{current_index} +1 lines")
            elif direction == 'Left':
                new_index = self.text_editor.index(f"{current_index} -1 chars")
            elif direction == 'Right':
                new_index = self.text_editor.index(f"{current_index} +1 chars")
            elif direction == 'Home':
                line_num = current_index.split('.')[0]
                new_index = f"{line_num}.0"
            elif direction == 'End':
                line_num = current_index.split('.')[0]
                new_index = f"{line_num}.end"
            elif direction == 'Prior':
                new_index = self.text_editor.index(f"{current_index} -1 pages")
            elif direction == 'Next':
                new_index = self.text_editor.index(f"{current_index} +1 pages")
            else:
                return

            line_start = f"{new_index.split('.')[0]}.0"
            tags = self.text_editor.tag_names(line_start)

            for tag in tags:
                if tag.startswith("line_lock_") and tag != f"line_lock_{self.current_client.name}":
                    return "break"

            # Move the cursor
            self.text_editor.mark_set('insert', new_index)
            self.update_current_cursor()
            self.update_other_cursors()
            self.update_line_locks()

            return "break"  # Prevent default behavior
        except Exception:
            return "break"

    def update_current_cursor(self):
        if not self.cursor_active:
            return
        self.text_editor.mark_set(self.current_client.cursor_mark_name, 'insert')

    def update_other_cursors(self):
        """Display other clients' cursors in the text editor."""
        # Remove existing cursor tags
        for client in self.clients:
            if client.name != self.current_client.name:
                self.text_editor.tag_remove(f'cursor_{client.name}', '1.0', 'end')

        # Add cursor tags for other clients
        for client in self.clients:
            if client.name != self.current_client.name:
                # Check if the cursor mark exists
                if client.cursor_mark_name in self.text_editor.mark_names():
                    cursor_pos = self.text_editor.index(client.cursor_mark_name)
                    # Underline the character at the cursor position
                    start = cursor_pos
                    end = f"{start}+1c"
                    self.text_editor.tag_add(f'cursor_{client.name}', start, end)
                    self.text_editor.tag_config(
                        f'cursor_{client.name}',
                        underline=True,
                        foreground=client.color,
                        selectbackground='',
                        background=''
                    )

    def update_line_numbers(self, event=None):
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")

        line_count = self.text_editor.index("end-1c").split(".")[0]
        line_numbers_content = "\n".join(str(i) for i in range(1, int(line_count) + 1))
        self.line_numbers.insert("1.0", line_numbers_content)

        self.line_numbers.configure(state="disabled")

    def update_line_locks(self):
        if not self.cursor_active:
            return

        cursor_pos = self.text_editor.index('insert')
        current_line = cursor_pos.split('.')[0]

        ranges = self.text_editor.tag_ranges(f"line_lock_{self.current_client.name}")
        for i in range(0, len(ranges), 2):
            start_line = int(self.text_editor.index(ranges[i]).split('.')[0])
            if start_line != int(current_line):
                self.text_editor.tag_remove(f"line_lock_{self.current_client.name}", ranges[i], ranges[i+1])
                self.current_client.locked_lines.discard(start_line)
        self.update_line_locks_visual()

    def update_line_locks_visual(self):
        """Update the visual indication of line locks."""
        # Remove existing visual lock tags
        for client in self.clients:
            self.text_editor.tag_remove(f"line_lock_visual_{client.name}", "1.0", "end")

        # Configure the visual lock tags
        for client in self.clients:
            if client.name == self.current_client.name:
                continue  # Skip the current client to avoid highlighting own lines
            ranges = self.text_editor.tag_ranges(f"line_lock_{client.name}")
            for i in range(0, len(ranges), 2):
                start = ranges[i]
                end = ranges[i+1]
                self.text_editor.tag_add(f"line_lock_visual_{client.name}", start, end)
            # Use client's color for background and adjust text color for readability
            self.text_editor.tag_config(
                f"line_lock_visual_{client.name}",
                background=client.color,
                foreground=self.get_contrasting_text_color(client.color)
        )


    def get_contrasting_text_color(self, bg_color):
        # Simple function to determine a contrasting text color (black or white)
        bg_color = bg_color.lstrip('#')
        r, g, b = int(bg_color[0:2], 16), int(bg_color[2:4], 16), int(bg_color[4:6], 16)
        luminance = (0.299*r + 0.587*g + 0.114*b)/255
        return '#000000' if luminance > 0.5 else '#FFFFFF'

    def update_line_locks_visual(self):
        """Update the visual indication of line locks."""
        # Remove existing visual lock tags
        for client in self.clients:
            self.text_editor.tag_remove(f"line_lock_visual_{client.name}", "1.0", "end")

        # Configure the visual lock tags
        for client in self.clients:
            ranges = self.text_editor.tag_ranges(f"line_lock_{client.name}")
            for i in range(0, len(ranges), 2):
                start = ranges[i]
                end = ranges[i+1]
                self.text_editor.tag_add(f"line_lock_visual_{client.name}", start, end)
            # Use client's color for background and set text color to ensure readability
            self.text_editor.tag_config(
                f"line_lock_visual_{client.name}",
                background=client.color,
                foreground=self.get_contrasting_text_color(client.color)
        )

    def set_current_client(self, client_name):
        """Switch the active client (debug mode only)."""
        if self.debug_mode:
            if self.cursor_active:
                self.update_current_cursor()
            self.cursor_active = False
            self.update_line_locks()
            # Switch client
            self.current_client = self.get_client_by_name(client_name)
            self.client_name = client_name
            self.text_editor.mark_unset('insert')
            self.cursor_active = True
            self.text_editor.focus_set()
            self.text_editor.mark_set('insert', self.invisible_textboxes[self.current_client.name].index(self.current_client.cursor_mark_name))
            self.update_current_cursor()
            self.update_other_cursors()
            self.update_line_locks()
            print(f"Switched to {self.current_client.name}")

    def get_current_client_cursor_index(self):
        if self.cursor_active:
            return self.text_editor.index('insert')
        else:
            return self.invisible_textboxes[self.current_client.name].index(self.current_client.cursor_mark_name)
