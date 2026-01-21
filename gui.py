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

        top_frame = tk.Frame(root, bg="#333", pady=10)
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text=f"👤 {name}", font=("Arial", 12, "bold"), fg="white", bg="#333").pack(side=tk.LEFT, padx=15)
        tk.Label(top_frame, text=f"🌐 {ip}:{port}", fg="#aaa", bg="#333").pack(side=tk.LEFT)

        control_frame = tk.LabelFrame(root, text="Download Manager", padx=10, pady=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(control_frame, text="File Name:").grid(row=0, column=0, sticky="w")
        self.entry_file = tk.Entry(control_frame, width=25)
        self.entry_file.grid(row=0, column=1, padx=5)
        self.entry_file.insert(0, default_file)

        tk.Label(control_frame, text="Swarm Source (Peers):").grid(row=0, column=2, padx=5)
        self.entry_peers = tk.Entry(control_frame, width=40)
        self.entry_peers.grid(row=0, column=3, padx=5)
        
        all_peers = list(self.peer_backend.network.peers.keys())
        peers_str = " ".join([p for p in all_peers if p != name])
        self.entry_peers.insert(0, peers_str)

        btn_swarm = tk.Button(control_frame, text="⬇ Start Swarm Download", command=self.start_swarm_thread, bg="#007bff", fg="white", font=("Arial", 10, "bold"))
        btn_swarm.grid(row=0, column=4, padx=15)

        log_frame = tk.Frame(root, pady=5, padx=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(log_frame, text="Live Activity Log:", anchor="w").pack(fill=tk.X)
        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', height=15, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True)

        sys.stdout = ConsoleRedirector(self.log_area)
        print(f"[GUI] Ready. Network size: {len(all_peers)} peers.")

    def start_swarm_thread(self):
        filename = self.entry_file.get().strip()
        peers_text = self.entry_peers.get().strip()
        if not filename or not peers_text:
            messagebox.showerror("Error", "Missing filename or peers.")
            return
        
        self.peer_backend.load_network_config()
        if peers_text == "ALL":
             peers_text = " ".join([p for p in self.peer_backend.network.peers.keys() if p != self.peer_backend.name])

        seeders = peers_text.split()
        t = threading.Thread(target=self._run_swarm, args=(filename, seeders))
        t.daemon = True
        t.start()

    def _run_swarm(self, filename, seeders):
        self.peer_backend.swarm_download(filename, seeders)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        sys.exit(1)
    name = sys.argv[1]
    port = sys.argv[2]
    folder = sys.argv[3]
    ip = sys.argv[4]
    filename = sys.argv[5] if len(sys.argv) > 5 else "video.mp4"

    root = tk.Tk()
    app = PeerGUI(root, name, port, folder, ip, filename)
    root.mainloop()