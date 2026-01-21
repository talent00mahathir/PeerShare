import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import sys
import socket
import os
import json
import shutil

# Get absolute path to python executable
PYTHON_CMD = sys.executable

class LauncherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PeerShare Network Manager (Silent)")
        self.root.geometry("500x650")
        
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 10), padding=5)
        
        tk.Label(root, text="PeerShare Network Launcher", font=("Arial", 16, "bold"), pady=10).pack()

        # --- 1. CONFIGURATION ---
        frame = tk.LabelFrame(root, text="1. Network Config", padx=10, pady=10)
        frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame, text="Total Peers:").grid(row=0, column=0, sticky="w", pady=5)
        
        self.spin_count = ttk.Spinbox(frame, from_=2, to=10, width=5, command=self.update_uploader_list)
        self.spin_count.set(3)
        self.spin_count.grid(row=0, column=1, sticky="w", pady=5)
        
        tk.Label(frame, text="IP Address:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_ip = tk.Entry(frame, width=20)
        self.entry_ip.insert(0, self.get_local_ip())
        self.entry_ip.grid(row=1, column=1, sticky="w", pady=5)

        # --- 2. FILE SELECTION ---
        frame_file = tk.LabelFrame(root, text="2. Select File to Share", padx=10, pady=10)
        frame_file.pack(fill="x", padx=10, pady=5)

        self.source_file_path = None
        btn_browse = ttk.Button(frame_file, text="Browse File...", command=self.browse_file)
        btn_browse.grid(row=0, column=0, padx=5)
        
        self.lbl_filename = tk.Label(frame_file, text="No file selected (will use dummy)", fg="gray")
        self.lbl_filename.grid(row=0, column=1, sticky="w", padx=5)

        # --- 3. SEEDERS ---
        frame_up = tk.LabelFrame(root, text="3. Who starts with the file? (Seeders)", padx=10, pady=10)
        frame_up.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.check_buttons_frame = tk.Frame(frame_up)
        self.check_buttons_frame.pack(fill="both", expand=True)
        
        self.check_vars = []
        self.update_uploader_list() # Initial load

        # --- LAUNCH BUTTON ---
        self.btn_launch = ttk.Button(root, text="🚀 Launch Network Environment", command=self.launch_network)
        self.btn_launch.pack(fill="x", padx=20, pady=20)

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
        except:
            local_ip = '127.0.0.1'
        finally:
            s.close()
        return local_ip

    def browse_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.source_file_path = filename
            self.lbl_filename.config(text=os.path.basename(filename), fg="black")

    def update_uploader_list(self):
        # Clear existing
        for widget in self.check_buttons_frame.winfo_children():
            widget.destroy()
        self.check_vars = []
        
        try: 
            count = int(self.spin_count.get())
        except: 
            count = 3

        for i in range(1, count + 1):
            var = tk.IntVar()
            if i == 1: var.set(1) # Default Peer 1
            chk = tk.Checkbutton(self.check_buttons_frame, text=f"Peer {i}", variable=var)
            chk.pack(anchor="w")
            self.check_vars.append(var)

    def launch_network(self):
        try:
            count = int(self.spin_count.get())
            target_ip = self.entry_ip.get().strip()
            
            if self.source_file_path:
                filename = os.path.basename(self.source_file_path)
            else:
                filename = "dummy_video.mp4"

            # 1. Setup Peer Data
            peers = []
            base_port = 5001
            for i in range(1, count + 1):
                peers.append({
                    'name': f'Peer{i}',
                    'port': base_port + i - 1,
                    'folder': f'peer_{i}_data'
                })

            # 2. Create Folders
            for p in peers:
                if not os.path.exists(p['folder']):
                    os.makedirs(p['folder'])

            # 3. Handle File Copying
            selected_indices = [i for i, var in enumerate(self.check_vars) if var.get() == 1]
            if not selected_indices:
                messagebox.showwarning("Warning", "No seeders selected! Network will be empty.")
            
            for idx in selected_indices:
                p = peers[idx]
                dest_path = os.path.join(p['folder'], filename)
                
                if self.source_file_path:
                    try:
                        shutil.copy(self.source_file_path, dest_path)
                    except Exception as e:
                        messagebox.showerror("Error", f"Copy failed: {e}")
                        return
                else:
                    if not os.path.exists(dest_path):
                        with open(dest_path, 'wb') as f:
                            f.write(os.urandom(1024 * 1024)) # 1MB dummy

            # 4. Save Network Config (Full Mesh)
            config_data = [{'name': p['name'], 'ip': target_ip, 'port': p['port']} for p in peers]
            with open("network_config.json", "w") as f:
                json.dump(config_data, f, indent=4)

            # 5. Launch Processes (HIDDEN TERMINAL MODE)
            for p in peers:
                # Quote arguments to handle spaces in paths
                cmd = f'"{PYTHON_CMD}" gui.py "{p["name"]}" "{p["port"]}" "{p["folder"]}" "{target_ip}" "{filename}"'
                
                if os.name == 'nt':
                    # 0x08000000 is the specific Windows flag for "CREATE_NO_WINDOW"
                    # This hides the black terminal completely.
                    subprocess.Popen(cmd, creationflags=0x08000000)
                else:
                    # Linux/Mac
                    subprocess.Popen([sys.executable, 'gui.py', p["name"], str(p["port"]), p["folder"], target_ip, filename])
            
            messagebox.showinfo("Success", f"Launched {count} peers.\nFile: {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Launch Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LauncherGUI(root)
    root.mainloop()