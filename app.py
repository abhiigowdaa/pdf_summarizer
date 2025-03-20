import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
import sqlite3
import re
from utils.extractor import extract_text_from_pdf
from utils.keyword_extractor import extract_keywords
from utils.summarizer import generate_summary
from utils.email_sender import send_email_with_attachment
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ------------------ DATABASE --------------------
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT)''')
conn.commit()

class LoginRegisterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Login or Register")
        self.geometry("400x300")

        self.label = ctk.CTkLabel(self, text="PDF Summarizer Login", font=("Arial", 18, "bold"))
        self.label.pack(pady=20)

        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email")
        self.email_entry.pack(pady=5)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=5)

        self.login_button = ctk.CTkButton(self, text="Login", command=self.login)
        self.login_button.pack(pady=5)

        self.register_button = ctk.CTkButton(self, text="Register", command=self.register)
        self.register_button.pack(pady=5)

    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        if user:
            self.destroy()
            app = PDFSummarizerApp()
            app.mainloop()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def register(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        if email and password:
            try:
                cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
                conn.commit()
                messagebox.showinfo("Success", "Registration successful! You can now login.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Email already registered.")
        else:
            messagebox.showerror("Error", "Please fill out all fields.")

class PDFSummarizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PDF Summarizer Tool")
        self.geometry("650x600")

        self.title_label = ctk.CTkLabel(self, text="PDF Summarizer Tool", font=("Arial", 22, "bold"))
        self.title_label.pack(pady=10)

        self.upload_frame = ctk.CTkFrame(self, corner_radius=12)
        self.upload_frame.pack(pady=15)

        self.upload_label = ctk.CTkLabel(self.upload_frame, text="Upload PDF", font=("Arial", 16))
        self.upload_label.pack(pady=(10, 5))

        self.upload_button = ctk.CTkButton(self.upload_frame, text="Choose Files ▼", command=self.show_dropdown)
        self.upload_button.pack(pady=5)

        self.dropdown_menu = None

        self.progressbar = ctk.CTkProgressBar(self)
        self.progressbar.set(0)
        self.progressbar.pack(pady=5)

        self.keywords_label = ctk.CTkLabel(self, text="Extracted Keywords:", font=("Arial", 14))
        self.keywords_label.pack(pady=(10, 0))
        self.keywords_box = ctk.CTkTextbox(self, width=500, height=80)
        self.keywords_box.pack(pady=5)

        self.summary_label = ctk.CTkLabel(self, text="Generated Summary:", font=("Arial", 14))
        self.summary_label.pack(pady=(10, 0))
        self.summary_box = ctk.CTkTextbox(self, width=500, height=200)
        self.summary_box.pack(pady=5)

        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=10)

        self.save_button = ctk.CTkButton(self.button_frame, text="Save Summary", command=self.save_summary)
        self.save_button.grid(row=0, column=0, padx=5)

        self.email_button = ctk.CTkButton(self.button_frame, text="Email Summary PDF", command=self.email_summary)
        self.email_button.grid(row=0, column=1, padx=5)

        self.summary_text = ""

    def show_dropdown(self):
        if self.dropdown_menu:
            self.dropdown_menu.destroy()
            self.dropdown_menu = None
        else:
            self.dropdown_menu = ctk.CTkFrame(self.upload_frame, fg_color="#2b2b2b", corner_radius=10)
            self.dropdown_menu.pack(pady=(5,0))

            ctk.CTkButton(self.dropdown_menu, text="From Device", command=self.upload_pdf, width=180).pack(pady=2)
            ctk.CTkButton(self.dropdown_menu, text="From Dropbox", state="disabled", width=180).pack(pady=2)
            ctk.CTkButton(self.dropdown_menu, text="From Google Drive", state="disabled", width=180).pack(pady=2)

    def upload_pdf(self):
        if self.dropdown_menu:
            self.dropdown_menu.destroy()
            self.dropdown_menu = None

        file_path = filedialog.askopenfilename(filetypes=[["PDF Files", "*.pdf"]])
        if file_path:
            try:
                self.progressbar.set(0.3)
                self.keywords_box.delete("1.0", ctk.END)
                self.summary_box.delete("1.0", ctk.END)
                text = extract_text_from_pdf(file_path)
                keywords = extract_keywords(text)
                summary = generate_summary(text)
                self.progressbar.set(0.7)
                self.keywords_box.insert("1.0", ', '.join(keywords[:10]))
                self.summary_box.insert("1.0", summary)
                self.summary_text = summary
                self.progressbar.set(1)
            except Exception as e:
                messagebox.showerror("Error", f"Something went wrong: {e}")

    def save_summary(self):
        if self.summary_text:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[["Text files", "*.txt"]])
            if file_path:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write("Summary:\n" + self.summary_text)
                messagebox.showinfo("Success", "Summary saved successfully!")

    def email_summary(self):
        if not self.summary_text:
            messagebox.showerror("Error", "No summary to send! Please upload and summarize a PDF first.")
            return

        recipient_email = simpledialog.askstring("Recipient Email", "Enter recipient email address:")

        if recipient_email and re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", recipient_email):
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = os.path.join(output_dir, f"summary_{timestamp}.pdf")

            c = canvas.Canvas(pdf_path, pagesize=letter)
            width, height = letter
            c.setFont("Helvetica", 12)
            text_object = c.beginText(40, height - 50)
            for line in self.summary_text.split("\n"):
                text_object.textLine(line)
            c.drawText(text_object)
            c.save()

            sent = send_email_with_attachment(
                recipient_email,
                "Here is your summarized PDF attached.",
                pdf_path
            )

            log_message = f"{datetime.now()} - Email to {recipient_email} - {'Success' if sent else 'Failed'}\n"

            with open("email_log.txt", "a") as log_file:
                log_file.write(log_message)

            if sent:
                messagebox.showinfo("Email Sent", f"Summary sent to {recipient_email}!")
            else:
                messagebox.showerror("Error", "Failed to send email.")
        else:
            messagebox.showerror("Invalid Email", "Please enter a valid email address.")

if __name__ == "__main__":
    login_app = LoginRegisterApp()
    login_app.mainloop()