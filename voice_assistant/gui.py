"""
Simple Tkinter GUI for the offline assistant.

- Click the mic button to listen (uses `stt.listen()`; falls back to text input if not available).
- While listening, a pulsing animation runs.
- Options let you enable execution and the Ollama decider.
- Recognized text and results are displayed.

Run with:
    python -m voice_assistant.gui

Or double-click `run_voice_assistant_ui.bat` in the project root.
"""
import tkinter as tk
from tkinter import ttk
from threading import Thread
import queue
import time
import sys
from pathlib import Path

# Import local package modules
from . import stt, nlp_model, executor
from . import main as core_main


class AssistantUI:
    def __init__(self, root):
        self.root = root
        root.title("Offline Voice Assistant")
        # larger window to match a modern compact assistant mock
        root.geometry("520x340")
        root.resizable(False, False)
        # dark themed background (blur/acrylic is platform-dependent; keep simple alpha)
        try:
            root.configure(bg="#0f0f10")
        except Exception:
            pass

        self.config = core_main.load_config()
        self.memory = core_main.load_memory()

        self.queue = queue.Queue()
        self.listening = False
        self.anim_phase = 0
        self.anim_id = None

        # Top layout area: left = large mic canvas, right = status and options
        top = ttk.Frame(root)
        top.place(x=12, y=8, width=496, height=240)

        # Left: big mic canvas (we reuse self.canvas so animation code continues to work)
        left = tk.Frame(top, bg="#0f0f10")
        left.place(x=8, y=8, width=268, height=224)
        self.canvas = tk.Canvas(left, width=244, height=200, bg="#0f0f10", highlightthickness=0)
        self.canvas.place(x=8, y=4)
        # stylized mic drawing
        self.base_circle = self.canvas.create_oval(28, 18, 188, 178, fill="#444", outline="")
        # mic stem
        self.mic_rect = self.canvas.create_rectangle(102, 138, 122, 178, fill="#3a3a3a", outline="")
        self.mic_circle = self.canvas.create_oval(86, 38, 138, 90, fill="#fff", outline="")

        # Right: status, options stacked vertically
        right = tk.Frame(top, bg="#0f0f10")
        right.place(x=288, y=8, width=200, height=224)

        self.status_label = tk.Label(right, text="Idle", fg="#eee", bg="#0f0f10", font=("Segoe UI", 14))
        self.status_label.pack(anchor='n', pady=(6, 6))

        # option checkbuttons (larger & clearer)
        chk_font = ("Segoe UI", 12)
        self.allow_exec_var = tk.BooleanVar(value=bool(self.config.get("allow_execution", True)))
        self.use_ollama_var = tk.BooleanVar(value=bool(self.config.get("use_ollama", True)))
        self.ollama_decider_var = tk.BooleanVar(value=bool(self.config.get("use_ollama_decider", True)))

        cb_exec = tk.Checkbutton(right, text="Execute", fg="#eee", bg="#0f0f10", selectcolor="#0f0f10", activebackground="#0f0f10", font=chk_font, variable=self.allow_exec_var, bd=0)
        cb_exec.pack(anchor='w', pady=8, padx=12)
        cb_oll = tk.Checkbutton(right, text="Ollama", fg="#eee", bg="#0f0f10", selectcolor="#0f0f10", activebackground="#0f0f10", font=chk_font, variable=self.use_ollama_var, bd=0)
        cb_oll.pack(anchor='w', pady=2, padx=12)
        cb_dec = tk.Checkbutton(right, text="Decider", fg="#eee", bg="#0f0f10", selectcolor="#0f0f10", activebackground="#0f0f10", font=chk_font, variable=self.ollama_decider_var, bd=0)
        cb_dec.pack(anchor='w', pady=2, padx=12)

        # ensure all checkboxes are selected by default (user requested all features enabled)
        try:
            self.allow_exec_var.set(True)
            self.use_ollama_var.set(True)
            self.ollama_decider_var.set(True)
        except Exception:
            pass

        # reflect changes immediately when options are toggled
        try:
            self.allow_exec_var.trace_add("write", lambda *a: self._on_option_change())
            self.use_ollama_var.trace_add("write", lambda *a: self._on_option_change())
            self.ollama_decider_var.trace_add("write", lambda *a: self._on_option_change())
        except Exception:
            self.allow_exec_var.trace("w", lambda *a: self._on_option_change())
            self.use_ollama_var.trace("w", lambda *a: self._on_option_change())
            self.ollama_decider_var.trace("w", lambda *a: self._on_option_change())

        self._on_option_change()

        # compact option summary label (keeps previous behavior of showing Exec/Ollama/Decider summary)
        self.option_label = tk.Label(right, text="", fg="#999", bg="#0f0f10", font=("Segoe UI", 9))
        self.option_label.pack(anchor='s', pady=(12, 2))

        # Bottom recognized entry (single-line) for clarity
        recog_frame = tk.Frame(root, bg="#0f0f10")
        recog_frame.place(x=12, y=262, width=496, height=64)
        recog_label = tk.Label(recog_frame, text="Recognized", fg="#ccc", bg="#0f0f10", font=("Segoe UI", 10))
        recog_label.place(x=12, y=6)
        self.rec_entry = tk.Entry(recog_frame, fg="#111", bg="#fff", bd=0, font=("Segoe UI", 11))
        self.rec_entry.place(x=12, y=30, width=472, height=24)
        # allow pressing Enter to submit typed commands
        try:
            self.rec_entry.bind("<Return>", self._on_manual_enter)
        except Exception:
            pass

        # Poll queue for results and start auto-listen loop
        self.root.after(200, self._poll_queue)
        self._running = True
        self._start_auto_listen()

    def _set_status(self, text):
        self.status_label.config(text=text)

    def _append_recognized(self, text):
        try:
            # single-line recognized entry
            self.rec_entry.delete(0, 'end')
            self.rec_entry.insert(0, text)
        except Exception:
            pass

    def _append_result(self, text):
        try:
            # show short result in status label briefly
            short = str(text)
            if len(short) > 60:
                short = short[:57] + '...'
            self.status_label.config(text=short)
            # reset status to Idle after a short delay
            def _reset():
                try:
                    self.status_label.config(text="Idle")
                except Exception:
                    pass
            self.root.after(3500, _reset)
        except Exception:
            pass

    def on_mic(self):
        # kept for compatibility but not used: GUI auto-listens
        return

    def _start_auto_listen(self):
        t = Thread(target=self._auto_listen_loop, daemon=True)
        t.start()

    def _on_option_change(self):
        # update compact option summary next to status
        try:
            parts = []
            parts.append("Exec:On" if self.allow_exec_var.get() else "Exec:Off")
            parts.append("Ollama:On" if self.use_ollama_var.get() else "Ollama:Off")
            parts.append("Decider:On" if self.ollama_decider_var.get() else "Decider:Off")
            self.option_label.config(text=" | ".join(parts))
        except Exception:
            pass

    def _auto_listen_loop(self):
        # Continuous listening loop similar to CLI run_interactive
        while getattr(self, "_running", False):
            try:
                cfg = self.config.copy()
                cfg["allow_execution"] = self.allow_exec_var.get()
                cfg["use_ollama"] = self.use_ollama_var.get()
                cfg["use_ollama_decider"] = self.ollama_decider_var.get()
                cfg["always_listen"] = True

                # notify UI that we're starting STT and pass a status callback
                recognized = None
                def _stt_status_cb(s):
                    # s can be 'loading', 'listening', or 'simulated'
                    try:
                        self.queue.put(("stt_status", s, None))
                    except Exception:
                        pass
                # In GUI mode we avoid using the stdin fallback of stt.listen()
                # because readline() returns immediately with empty input and
                # gives the impression of "not listening". Check availability
                # and prompt the user to type when real STT isn't present.
                try:
                    if not stt.available():
                        # inform UI that STT is simulated/unavailable and focus entry
                        try:
                            self.queue.put(("stt_status", "simulated", None))
                            self.queue.put(("focus_entry", None, None))
                        except Exception:
                            pass
                        time.sleep(0.7)
                        continue
                    recognized = stt.listen(status_cb=_stt_status_cb)
                except Exception:
                    recognized = None

                if not recognized:
                    # idle briefly
                    time.sleep(0.4)
                    self.queue.put(("status", "idle", None))
                    continue

                # process recognized text in background so the listen loop can continue
                Thread(target=self._process_and_queue, args=(recognized, cfg), daemon=True).start()
                # small backoff to avoid tight loop
                time.sleep(0.05)
            except Exception:
                time.sleep(0.5)

    def _listen_worker(self, cfg):
        # call the existing stt.listen() — it may return None or an empty string
        try:
            recognized = stt.listen()
        except Exception:
            recognized = None

        # If STT not available or empty, prompt for text input in the UI thread
        if not recognized:
            # ask user to type text
            self.queue.put(("prompt_text", None, cfg))
            return

        # process text using main.process_text
        res = core_main.process_text(recognized, cfg, self.memory)
        self.queue.put(("result", recognized, res))

    def _process_and_queue(self, recognized, cfg):
        """Background worker: run main.process_text and push the result to the UI queue."""
        try:
            res = core_main.process_text(recognized, cfg, self.memory)
            try:
                self.queue.put(("result", recognized, res))
            except Exception:
                pass
        except Exception as e:
            try:
                self.queue.put(("result", recognized, {"ok": False, "error": str(e)}))
            except Exception:
                pass

    def _poll_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                kind, text, payload = item
                if kind == "status":
                    if text == "listening":
                        self._set_status("Listening...")
                        self.listening = True
                        self._start_anim()
                    else:
                        self._set_status("Idle")
                        self.listening = False
                        self._stop_anim()
                    self.queue.task_done()
                    continue

                if kind == "prompt_text":
                    # open a mini input dialog in the UI thread
                    self._stop_anim()
                    self.listening = False
                    self._set_status("Type input below and press Enter")
                    self._show_text_input(payload)
                elif kind == "focus_entry":
                    # focus the bottom recognized entry so user can type
                    try:
                        self.rec_entry.focus_set()
                        self._set_status("No mic — type command below")
                    except Exception:
                        pass
                elif kind == "stt_status":
                    # Map STT status to friendly UI messages and animation
                    st = text
                    if st == "loading":
                        self._set_status("Loading model...")
                        self.listening = False
                        self._stop_anim()
                    elif st == "listening":
                        self._set_status("Listening...")
                        self.listening = True
                        self._start_anim()
                    elif st == "simulated":
                        self._set_status("Simulated input - type or speak")
                        self.listening = False
                        self._stop_anim()
                    self.queue.task_done()
                    continue
                elif kind == "result":
                    recognized, res = text, payload
                    self._stop_anim()
                    self.listening = False
                    self._set_status("Idle")
                    self._append_recognized(recognized)
                    self._append_result(str(res))
                self.queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.root.after(200, self._poll_queue)

    def _show_text_input(self, cfg):
        win = tk.Toplevel(self.root)
        win.title("Type command")
        win.geometry("360x120")
        ttk.Label(win, text="No microphone available. Type the command and press Enter:").pack(pady=(8, 4))
        entry = ttk.Entry(win, width=60)
        entry.pack(padx=8)
        entry.focus_set()

        def on_enter(evt=None):
            text = entry.get().strip()
            win.destroy()
            if not text:
                self._set_status("Idle")
                return
            self._set_status("Processing...")
            # process in background
            thread = Thread(target=self._process_text_worker, args=(text, cfg), daemon=True)
            thread.start()

        entry.bind("<Return>", on_enter)
        ttk.Button(win, text="Cancel", command=lambda: (win.destroy(), self._set_status("Idle"))).pack(pady=(6, 4))

    def _process_text_worker(self, text, cfg):
        res = core_main.process_text(text, cfg, self.memory)
        self.queue.put(("result", text, res))

    def _on_manual_enter(self, evt=None):
        # read from the recognized single-line entry (user can type here)
        try:
            text = self.rec_entry.get().strip()
        except Exception:
            text = ""
        if not text:
            return
        cfg = self.config.copy()
        cfg["allow_execution"] = self.allow_exec_var.get()
        cfg["use_ollama"] = self.use_ollama_var.get()
        cfg["use_ollama_decider"] = self.ollama_decider_var.get()
        cfg["always_listen"] = True
        try:
            self.rec_entry.delete(0, 'end')
        except Exception:
            pass
        self._set_status("Processing...")
        Thread(target=self._process_text_worker, args=(text, cfg), daemon=True).start()

    def _start_anim(self):
        # improved pulsing rings animation
        self.anim_phase = 0
        self.rings = [0, 8, 16]
        self.ring_items = []
        self._animate()

    def _animate(self):
        if not self.listening:
            return
        w = 140
        h = 140
        cx = w // 2
        cy = h // 2
        # remove previous rings
        for it in getattr(self, 'ring_items', []):
            try:
                self.canvas.delete(it)
            except Exception:
                pass
        self.ring_items = []
        for i in range(len(self.rings)):
            self.rings[i] += 2
            r = 30 + self.rings[i]
            clr = f"#{200:02x}{60:02x}{60:02x}"
            it = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=clr, width=max(1, 6 - i * 2))
            self.ring_items.append(it)
        # subtle inner circle color change
        phase = (self.anim_phase % 30) / 30.0
        inner_r = int(68 + (180 - 68) * phase)
        inner_g = int(68 * (1 - phase))
        inner_b = int(68 * (1 - phase))
        color = f"#{inner_r:02x}{inner_g:02x}{inner_b:02x}"
        self.canvas.itemconfigure(self.base_circle, fill=color)
        self.anim_phase += 1
        self.anim_id = self.root.after(90, self._animate)

    def _stop_anim(self):
        if self.anim_id:
            try:
                self.root.after_cancel(self.anim_id)
            except Exception:
                pass
            self.anim_id = None
        # restore base color
        self.canvas.itemconfigure(self.base_circle, fill="#444")
        for it in getattr(self, 'ring_items', []):
            try:
                self.canvas.delete(it)
            except Exception:
                pass
        self.ring_items = []


def main():
    root = tk.Tk()
    app = AssistantUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
