import tkinter as tk
from tkinter import scrolledtext, messagebox
import sys
import threading
from peer import Peer 

class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
    def write(self, string):
        self.text_widget.after(0, self._append_text, string)
    def _append_text(self, string):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')
    def flush(self): pass

class PeerGUI:
    def __init__(self, root, name, port, folder, ip, default_file):
        self.root = root
        self.root.title(f"PeerShare: {name}")
        self.root.geometry("750x550")
        
        self.peer_backend = Peer(name, port, folder, ip)
        self.peer_backend.start()

        top_frame = tk.Frame(root, bg="#2c3e50", pady=10)
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text=f"👤 {name}", font=("Arial", 12, "bold"), fg="white", bg="#2c3e50").pack(side=tk.LEFT, padx=15)
        
        control_frame = tk.LabelFrame(root, text="Dynamic Swarm Control", padx=10, pady=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(control_frame, text="File:").grid(row=0, column=0)
        self.entry_file = tk.Entry(control_frame, width=20); self.entry_file.grid(row=0, column=1)
        self.entry_file.insert(0, default_file)

        tk.Label(control_frame, text="Peers:").grid(row=0, column=2, padx=5)
        self.entry_peers = tk.Entry(control_frame, width=30); self.entry_peers.grid(row=0, column=3)
        self.entry_peers.insert(0, "ALL")

        btn_swarm = tk.Button(control_frame, text="⬇ Start", command=self.start_swarm_thread, bg="#27ae60", fg="white", font=("Arial", 10, "bold"))
        btn_swarm.grid(row=0, column=4, padx=15)

        self.log_area = scrolledtext.ScrolledText(root, state='disabled', bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        sys.stdout = ConsoleRedirector(self.log_area)

    def start_swarm_thread(self):
        filename = self.entry_file.get().strip()
        p_text = self.entry_peers.get().strip()
        self.peer_backend.load_network_config()
        
        if p_text == "ALL":
            seeders = [p for p in self.peer_backend.network.peers.keys() if p != self.peer_backend.name]
        else:
            seeders = p_text.split()
            
        threading.Thread(target=self.peer_backend.swarm_download, args=(filename, seeders), daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    PeerGUI(root, sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else "file.mp4")
    root.mainloop()