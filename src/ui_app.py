import customtkinter as ctk
import threading
import os
import sys
from tkinter import messagebox
from core.capture import CaptureEngine
from core.exporter import ReportExporter

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class DocuFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DocuFlow")
        self.geometry("400x500")
        self.resizable(False, False)

        # Logic variables
        self.capture_engine = None
        self.capture_thread = None
        self.export_thread = None
        self.is_recording = False
        self.is_exporting = False

        # GUI Elements
        self._create_widgets()

    def _create_widgets(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=20, padx=20, fill="x")

        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="DocuFlow", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack()

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame, 
            text="Generador de Documentación", 
            font=ctk.CTkFont(size=14)
        )
        self.subtitle_label.pack()

        # Inputs
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(pady=10, padx=20, fill="x")

        self.doc_title_label = ctk.CTkLabel(self.input_frame, text="Título del Tutorial *")
        self.doc_title_label.pack(anchor="w")
        self.doc_title_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Ej: Cómo crear una factura")
        self.doc_title_entry.pack(fill="x", pady=(0, 10))

        self.author_label = ctk.CTkLabel(self.input_frame, text="Autor (Opcional)")
        self.author_label.pack(anchor="w")
        self.author_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Tu Nombre")
        self.author_entry.pack(fill="x", pady=(0, 10))

        # Status
        self.status_label = ctk.CTkLabel(
            self, 
            text="Listo para grabar", 
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=(20, 10))
        
        # Progress Bar (initially hidden)
        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", mode="indeterminate")
        # Don't pack it yet, strictly show on export

        # Buttons
        self.start_button = ctk.CTkButton(
            self, 
            text="INICIAR GRABACIÓN", 
            font=ctk.CTkFont(size=15, weight="bold"),
            height=40,
            command=self.start_recording
        )
        self.start_button.pack(padx=20, fill="x")

        self.open_folder_button = ctk.CTkButton(
            self,
            text="Abrir Carpeta de PDF",
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "#DCE4EE"),
            state="disabled",
            command=self.open_output_folder
        )
        self.open_folder_button.pack(pady=20)

    def start_recording(self):
        doc_title = self.doc_title_entry.get().strip()
        if not doc_title:
            messagebox.showwarning("Faltan datos", "Por favor ingresa un título para el tutorial.")
            return

        # Prepare UI
        self.is_recording = True
        self.status_label.configure(text="Grabando... Presiona ESC para terminar", text_color="#FF9900")
        self.start_button.configure(state="disabled", text="Grabando...")
        self.open_folder_button.configure(state="disabled")
        self.doc_title_entry.configure(state="disabled")
        self.author_entry.configure(state="disabled")
        
        # Minimize window
        self.iconify()

        # Start Capture in Thread
        self.capture_engine = CaptureEngine()
        self.capture_thread = threading.Thread(target=self.capture_engine.start)
        self.capture_thread.daemon = True
        self.capture_thread.start()

        # Start monitoring
        self.monitor_recording()

    def monitor_recording(self):
        if self.capture_thread and self.capture_thread.is_alive():
            # Check back in 100ms
            self.after(100, self.monitor_recording)
        else:
            # Thread finished (Esc pressed)
            self.stop_recording()

    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False
        self.deiconify()
        
        # Start Export Process
        self.status_label.configure(text="Generando PDF... Por favor espere.", text_color="cyan")
        self.progress_bar.pack(pady=(0, 20), padx=40, fill="x")
        self.progress_bar.start()
        
        self.start_button.configure(text="Generando...")
        
        steps = self.capture_engine.get_steps()
        if steps:
            title = self.doc_title_entry.get().strip() or "Sin Título"
            author = self.author_entry.get().strip() or "Anónimo"
            
            # Run export in thread
            exporter = ReportExporter(steps)
            self.export_thread = threading.Thread(
                target=self._run_export, 
                args=(exporter, title, author)
            )
            self.export_thread.start()
            self.monitor_export()
        else:
            # Nothing captured
            self.end_export(failed=True)

    def _run_export(self, exporter, title, author):
        exporter.generate_pdf(title=title, author=author)

    def monitor_export(self):
        if self.export_thread and self.export_thread.is_alive():
            self.after(100, self.monitor_export)
        else:
            self.end_export(failed=False)

    def end_export(self, failed=False):
        # Stop loading
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        
        if failed:
             self.status_label.configure(text="Grabación vacía o cancelada.", text_color="red")
        else:
             self.status_label.configure(text="¡PDF Generado con éxito!", text_color="green")
             self.open_folder_button.configure(state="normal")
        
        # Reset UI controls
        self.start_button.configure(state="normal", text="INICIAR GRABACIÓN")
        self.doc_title_entry.configure(state="normal")
        self.author_entry.configure(state="normal")

    def open_output_folder(self):
        output_dir = os.path.abspath("output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        os.startfile(output_dir)

if __name__ == "__main__":
    app = DocuFlowApp()
    app.mainloop()
