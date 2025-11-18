# quiz_app_colored.py
# Run: python quiz_app_colored.py
# A Tkinter-based quiz app: Login, Registration, Category-based quiz, scoreboard (SQLite).
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import hashlib
import datetime
import random

DB = "quiz_app_colored.db"

# --------------------------
# Database helpers
# --------------------------
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            age INTEGER,
            gender TEXT,
            category TEXT,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            score INTEGER,
            total INTEGER,
            category TEXT,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

# --------------------------
# A small sample question bank (extendable)
# each question: {'q':..., 'options':[...], 'answer': index}
# --------------------------
QUESTION_BANK = {
    "Children": [
        {'q': "Which animal says 'moo'?", 'options': ['Dog','Cow','Cat','Sheep'], 'answer': 1},
        {'q': "How many legs does a spider have?", 'options': ['6','8','4','10'], 'answer': 1},
        {'q': "Which of these is a primary color?", 'options': ['Green','Purple','Red','Brown'], 'answer': 2},
    ],
    "Teenagers": [
        {'q': "Which tech is used to secure websites (HTTPS)?", 'options': ['FTP','SSL/TLS','SMTP','POP3'], 'answer': 1},
        {'q': "What does 2FA stand for?", 'options': ['Two-Factor Auth','Two-File Auth','Two-Fold Access','None'], 'answer': 0},
        {'q': "Which subject studies living things?", 'options': ['Physics','Chemistry','Biology','Math'], 'answer': 2},
    ],
    "Adults": [
        {'q': "Which index commonly measures inflation?", 'options': ['CPI','GDP','GNP','PPI'], 'answer': 0},
        {'q': "Which of these is renewable energy?", 'options': ['Coal','Solar','Oil','Natural Gas'], 'answer': 1},
        {'q': "What is diversification in investing mainly for?", 'options': ['Increase taxes','Reduce risk','Guarantee profit','Increase fees'], 'answer': 1},
    ]
}

def build_rounds(cat):
    bank = QUESTION_BANK.get(cat, []).copy()
    random.shuffle(bank)
    n = len(bank)
    if n == 0:
        return [[], [], []]
    k = max(1, n//3)
    r1 = bank[:k]
    r2 = bank[k:k+k]
    r3 = bank[k+k:]
    # Ensure some content in rounds
    if not r2 and n>1:
        r2 = bank[1:2]
        r1 = [bank[0]]
        r3 = bank[2:]
    return [r1, r2, r3]

# --------------------------
# Simple gradient helper (Canvas)
# --------------------------
def create_gradient(canvas_width, canvas_height, color1, color2):
    c = tk.Canvas(width=canvas_width, height=canvas_height, highlightthickness=0)
    def hex_to_rgb(h): h=h.lstrip('#'); return int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    r1,g1,b1 = hex_to_rgb(color1); r2,g2,b2 = hex_to_rgb(color2)
    for i in range(canvas_height):
        t = i / canvas_height
        r = int(r1 + (r2-r1)*t); g = int(g1 + (g2-g1)*t); b = int(b1 + (b2-b1)*t)
        c.create_line(0,i,canvas_width,i, fill=f'#{r:02x}{g:02x}{b:02x}')
    return c

# --------------------------
# Main application
# --------------------------
class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Beautiful Quiz App")
        self.geometry("960x680")
        self.minsize(860,620)

        # Colors & styles
        self.colors = {
            'bg': '#EAF4FF',
            'card': '#FFFFFF',
            'accent': '#2E6BE6',
            'accent_dark': '#234FAB',
            'muted': '#25343B',
            'success': '#2AA876',
            'danger': '#E05A5A'
        }
        self.font_main = ('Segoe UI', 11)
        self.font_title = ('Segoe UI', 18, 'bold')

        self.configure(bg=self.colors['bg'])
        self.style = ttk.Style(self)
        try:
            self.style.theme_use('clam')
        except:
            pass
        self.style.configure("TFrame", background=self.colors['bg'])
        self.style.configure("Card.TFrame", background=self.colors['card'])
        self.style.configure("TLabel", background=self.colors['bg'], foreground=self.colors['muted'], font=self.font_main)
        self.style.configure("Accent.TLabel", background=self.colors['card'], foreground=self.colors['accent_dark'], font=self.font_main)
        self.style.configure("Title.TLabel", background=self.colors['accent'], foreground='white', font=self.font_title)
        self.style.configure("TButton", font=('Segoe UI',10,'bold'), padding=6)
        self.style.map("TButton", background=[('active', self.colors['accent_dark'])])

        init_db()
        self.current_user = None
        self.frames = {}
        self.create_frames()
        self.show_frame(LoginFrame)

    def create_frames(self):
        container = ttk.Frame(self)
        container.pack(fill='both', expand=True, padx=12, pady=12)
        for F in (LoginFrame, RegisterFrame, HomeFrame, QuizFrame, ScoreboardFrame):
            frame = F(parent=container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()
        if hasattr(frame, 'on_show'):
            frame.on_show()

# --------------------------
# Login Page
# --------------------------
class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=14)
        self.controller = controller

        grad = create_gradient(920, 72, controller.colors['accent'], controller.colors['accent_dark'])
        grad_frame = ttk.Frame(self, style="Card.TFrame")
        grad_frame.pack(fill='x', pady=(0,10))
        grad.master = grad_frame
        grad.pack(fill='x')
        title = ttk.Label(grad, text="Welcome to Beautiful Quiz", style="Title.TLabel")
        grad.create_window(460,36,window=title)

        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(padx=8, pady=8, fill='x')

        ttk.Label(card, text="Username or Email:", style="Accent.TLabel").grid(row=0, column=0, sticky='w')
        self.ident = ttk.Entry(card, width=36); self.ident.grid(row=0, column=1, pady=6, padx=8)

        ttk.Label(card, text="Password:", style="Accent.TLabel").grid(row=1, column=0, sticky='w')
        self.pw = ttk.Entry(card, width=36, show='*'); self.pw.grid(row=1, column=1, pady=6, padx=8)

        btns = ttk.Frame(card, style="Card.TFrame"); btns.grid(row=2, column=0, columnspan=2, pady=10)
        login_btn = ttk.Button(btns, text="Login", command=self.try_login); login_btn.grid(row=0,column=0,padx=6)
        reg_btn = ttk.Button(btns, text="Register →", command=lambda: controller.show_frame(RegisterFrame)); reg_btn.grid(row=0,column=1,padx=6)

        forgot_btn = ttk.Button(card, text="Forgot password?", command=self.forgot_password); forgot_btn.grid(row=3,column=0,columnspan=2,pady=(6,0))
        self.message = ttk.Label(self, text="", foreground=controller.colors['danger'])
        self.message.pack(pady=6)

    def try_login(self):
        ident = self.ident.get().strip(); pw = self.pw.get().strip()
        if not ident or not pw:
            self.message.config(text="Enter username/email and password.")
            return
        conn = sqlite3.connect(DB); cur = conn.cursor()
        cur.execute("SELECT id, username, email, password_hash, age, gender, category FROM users WHERE username=? OR email=?", (ident,ident))
        row = cur.fetchone(); conn.close()
        if not row:
            self.message.config(text="User not found. Please register.")
            return
        uid, username, email, phash, age, gender, category = row
        if hash_pw(pw) != phash:
            self.message.config(text="Incorrect password.")
            return
        self.controller.current_user = {'id':uid,'username':username,'email':email,'age':age,'gender':gender,'category':category}
        self.ident.delete(0,'end'); self.pw.delete(0,'end'); self.message.config(text="")
        self.controller.show_frame(HomeFrame)

    def forgot_password(self):
        email = simpledialog.askstring("Forgot password", "Enter your registered email:")
        if not email: return
        conn = sqlite3.connect(DB); cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        if not row:
            conn.close(); messagebox.showerror("Not found", "No user with that email."); return
        uid = row[0]
        newpw = simpledialog.askstring("Reset password", "Enter new password:", show='*')
        if not newpw:
            conn.close(); return
        cur.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_pw(newpw), uid))
        conn.commit(); conn.close()
        messagebox.showinfo("Success", "Password reset. Please login with new password.")

# --------------------------
# Registration Page
# --------------------------
class RegisterFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=12)
        self.controller = controller
        grad = create_gradient(920, 60, controller.colors['accent_dark'], controller.colors['accent'])
        grad_frame = ttk.Frame(self, style="Card.TFrame")
        grad_frame.pack(fill='x', pady=(0,8))
        grad.master = grad_frame; grad.pack(fill='x')
        title = ttk.Label(grad, text="Create an Account", style="Title.TLabel"); grad.create_window(460,30,window=title)

        card = ttk.Frame(self, style="Card.TFrame", padding=14); card.pack(padx=8,pady=8,fill='x')

        ttk.Label(card, text="Username:", style="Accent.TLabel").grid(row=0,column=0, sticky='w')
        self.username = ttk.Entry(card, width=36); self.username.grid(row=0,column=1,pady=6, padx=8)

        ttk.Label(card, text="Email:", style="Accent.TLabel").grid(row=1,column=0, sticky='w')
        self.email = ttk.Entry(card, width=36); self.email.grid(row=1,column=1,pady=6, padx=8)

        ttk.Label(card, text="Password:", style="Accent.TLabel").grid(row=2,column=0, sticky='w')
        self.pw = ttk.Entry(card, width=36, show='*'); self.pw.grid(row=2,column=1,pady=6, padx=8)

        ttk.Label(card, text="Confirm Password:", style="Accent.TLabel").grid(row=3,column=0, sticky='w')
        self.pw2 = ttk.Entry(card, width=36, show='*'); self.pw2.grid(row=3,column=1,pady=6, padx=8)

        ttk.Label(card, text="Age:", style="Accent.TLabel").grid(row=4,column=0, sticky='w')
        self.age_var = tk.IntVar(value=18)
        self.age_spin = ttk.Spinbox(card, from_=8, to=100, textvariable=self.age_var, width=6); self.age_spin.grid(row=4,column=1, sticky='w', pady=6, padx=8)

        ttk.Label(card, text="Gender:", style="Accent.TLabel").grid(row=5,column=0, sticky='w')
        self.gender_var = tk.StringVar(value='Male')
        gframe = ttk.Frame(card, style="Card.TFrame"); gframe.grid(row=5,column=1, sticky='w')
        ttk.Radiobutton(gframe, text='Male', variable=self.gender_var, value='Male').pack(side='left', padx=6)
        ttk.Radiobutton(gframe, text='Female', variable=self.gender_var, value='Female').pack(side='left', padx=6)
        ttk.Radiobutton(gframe, text='Other', variable=self.gender_var, value='Other').pack(side='left', padx=6)

        ttk.Label(card, text="(Category determined by age: 8-12 Children, 13-19 Teenagers, 20-40 Adults)", wraplength=680).grid(row=6,column=0,columnspan=2,pady=(8,6))

        btns = ttk.Frame(card); btns.grid(row=7,column=0,columnspan=2,pady=8)
        ttk.Button(btns, text="Register", command=self.register_user).pack(side='left', padx=6)
        ttk.Button(btns, text="Back to Login", command=lambda: controller.show_frame(LoginFrame)).pack(side='left', padx=6)

        self.status = ttk.Label(self, text="", foreground=controller.colors['success']); self.status.pack(pady=6)
        now = datetime.datetime.now().strftime("%A, %d %B %Y — %I:%M %p")
        footer = ttk.Label(self, text=f"Registration time: {now}", font=('Segoe UI',9)); footer.pack(side='bottom', pady=8)

    def determine_category(self, age):
        age = int(age)
        if 8 <= age <= 12:
            return "Children"
        if 13 <= age <= 19:
            return "Teenagers"
        if 20 <= age <= 40:
            return "Adults"
        return "Adults"

    def register_user(self):
        u = self.username.get().strip(); e = self.email.get().strip(); p = self.pw.get().strip(); p2 = self.pw2.get().strip()
        try:
            age = int(self.age_spin.get())
        except:
            messagebox.showerror("Invalid", "Enter a valid age.")
            return
        gender = self.gender_var.get()
        if not (u and e and p):
            messagebox.showerror("Missing", "Please fill all fields.")
            return
        if p != p2:
            messagebox.showerror("Password", "Passwords do not match.")
            return
        cat = self.determine_category(age)
        conn = sqlite3.connect(DB); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, email, password_hash, age, gender, category, created_at) VALUES (?,?,?,?,?,?,?)",
                        (u,e,hash_pw(p),age,gender,cat,datetime.datetime.now().isoformat()))
            conn.commit()
            self.status.config(text=f"Registered successfully as {cat}. You can login now.")
            # clear
            self.username.delete(0,'end'); self.email.delete(0,'end'); self.pw.delete(0,'end'); self.pw2.delete(0,'end')
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate", "Username or email already exists.")
        finally:
            conn.close()

# --------------------------
# Home / Category Selection
# --------------------------
class HomeFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=12)
        self.controller = controller
        header = ttk.Label(self, text="Dashboard — Select Quiz", font=self.controller.font_title, foreground=self.controller.colors['accent_dark'])
        header.pack(pady=(6,10), anchor='w')

        self.user_label = ttk.Label(self, text="", font=self.controller.font_main)
        self.user_label.pack(pady=6, anchor='w')

        card = ttk.Frame(self, style="Card.TFrame", padding=12)
        card.pack(padx=6, pady=6, fill='x')

        ttk.Label(card, text="Category:", style="Accent.TLabel").grid(row=0, column=0, sticky='w')
        self.cat_var = tk.StringVar(value='Children')
        self.cat_combo = ttk.Combobox(card, textvariable=self.cat_var, values=['Children','Teenagers','Adults'], state='readonly', width=20)
        self.cat_combo.grid(row=0, column=1, padx=12, pady=6, sticky='w')

        ttk.Label(card, text="Round:", style="Accent.TLabel").grid(row=1, column=0, sticky='w')
        self.round_var = tk.StringVar(value='1')
        self.round_combo = ttk.Combobox(card, textvariable=self.round_var, values=['1','2','3'], state='readonly', width=6)
        self.round_combo.grid(row=1, column=1, padx=12, pady=6, sticky='w')

        ttk.Label(card, text="Time limit (mins):", style="Accent.TLabel").grid(row=2, column=0, sticky='w')
        self.time_entry = ttk.Entry(card, width=8); self.time_entry.insert(0,"0")
        self.time_entry.grid(row=2, column=1, padx=12, pady=6, sticky='w')

        btns = ttk.Frame(card); btns.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btns, text="Start Quiz", command=self.start_quiz).pack(side='left', padx=6)
        ttk.Button(btns, text="Scoreboard", command=lambda: controller.show_frame(ScoreboardFrame)).pack(side='left', padx=6)
        ttk.Button(btns, text="Logout", command=self.logout).pack(side='left', padx=6)

        self.info_label = ttk.Label(self, text="", font=('Segoe UI',9)); self.info_label.pack(pady=8, anchor='w')

    def on_show(self):
        u = self.controller.current_user
        if not u:
            self.controller.show_frame(LoginFrame)
            return
        self.user_label.config(text=f"Hello, {u['username']} (Age: {u['age']}, Category: {u['category']})")
        now = datetime.datetime.now().strftime("%A, %d %B %Y — %I:%M %p")
        self.info_label.config(text=f"Current date & time: {now}")

    def start_quiz(self):
        cat = self.cat_var.get(); rnd = int(self.round_var.get())
        try:
            tmin = float(self.time_entry.get())
        except:
            messagebox.showerror("Invalid", "Enter a valid number for time limit.")
            return
        qframe = self.controller.frames[QuizFrame]
        qframe.setup_quiz(category=cat, round_number=rnd, time_limit_minutes=tmin)
        self.controller.show_frame(QuizFrame)

    def logout(self):
        self.controller.current_user = None
        self.controller.show_frame(LoginFrame)

# --------------------------
# Quiz Page (category-based)
# --------------------------
class QuizFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=10)
        self.controller = controller
        self.questions = []
        self.answers = []
        self.current_index = 0
        self.var_choice = tk.IntVar(value=-1)
        self.timer_seconds = 0
        self.timer_running = False
        self.timer_id = None

        header = ttk.Label(self, text="Quiz", font=self.controller.font_title, foreground=self.controller.colors['accent_dark'])
        header.pack(pady=(2,8), anchor='w')

        top = ttk.Frame(self); top.pack(fill='x', pady=(0,8))
        self.progress_label = ttk.Label(top, text="Q 0 / 0"); self.progress_label.pack(side='left', padx=6)
        self.time_label = ttk.Label(top, text=""); self.time_label.pack(side='right', padx=6)

        self.qcard = ttk.Frame(self, style="Card.TFrame", padding=12); self.qcard.pack(fill='both', expand=True, padx=6, pady=6)
        self.q_text = ttk.Label(self.qcard, text="", wraplength=820, font=('Segoe UI',12)); self.q_text.pack(pady=(6,12), anchor='w')
        self.options_frame = ttk.Frame(self.qcard, style="Card.TFrame"); self.options_frame.pack(pady=6, anchor='w')

        nav = ttk.Frame(self); nav.pack(pady=8)
        self.prev_btn = ttk.Button(nav, text="◀ Previous", command=self.go_prev); self.prev_btn.grid(row=0,column=0,padx=6)
        self.next_btn = ttk.Button(nav, text="Next ▶", command=self.go_next); self.next_btn.grid(row=0,column=1,padx=6)
        self.submit_btn = ttk.Button(nav, text="Submit Quiz", command=self.submit_quiz); self.submit_btn.grid(row=0,column=2,padx=6)

        self.qjump_frame = ttk.Frame(self, padding=6); self.qjump_frame.pack(pady=6, fill='x')
        self.feedback = ttk.Label(self, text="", foreground=self.controller.colors['accent_dark']); self.feedback.pack(pady=6)

    def setup_quiz(self, category='Children', round_number=1, time_limit_minutes=0):
        rounds = build_rounds(category)
        sel = rounds[round_number-1] if len(rounds)>=round_number else []
        self.questions = sel.copy() if sel else QUESTION_BANK.get(category, []).copy()
        random.shuffle(self.questions)
        self.answers = [None] * len(self.questions)
        self.current_index = 0
        self.var_choice.set(-1)
        self.build_qjump()
        self.show_question()
        # timer
        self.timer_running = False
        self.time_label.config(text="")
        if time_limit_minutes and time_limit_minutes>0:
            self.timer_seconds = int(time_limit_minutes*60)
            self.timer_running = True
            self.countdown()

    def build_qjump(self):
        for w in self.qjump_frame.winfo_children(): w.destroy()
        ttk.Label(self.qjump_frame, text="Jump to:").pack(side='left', padx=(0,8))
        for i in range(len(self.questions)):
            b = ttk.Button(self.qjump_frame, text=str(i+1), width=3, command=lambda idx=i: self.goto_question(idx))
            b.pack(side='left', padx=3, pady=3)

    def show_question(self):
        if not self.questions:
            self.q_text.config(text="No questions for this category/round.")
            self.progress_label.config(text="Q 0 / 0")
            return
        q = self.questions[self.current_index]
        self.q_text.config(text=f"{self.current_index+1}. {q['q']}")
        for w in self.options_frame.winfo_children(): w.destroy()
        self.var_choice.set(-1 if self.answers[self.current_index] is None else self.answers[self.current_index])
        for idx, opt in enumerate(q['options']):
            r = ttk.Radiobutton(self.options_frame, text=opt, variable=self.var_choice, value=idx, command=self.save_choice)
            r.pack(anchor='w', pady=4)
        self.update_nav(); self.progress_label.config(text=f"Q {self.current_index+1} / {len(self.questions)}")
        self.refresh_qjump_buttons(); self.feedback.config(text="")

    def save_choice(self):
        v = self.var_choice.get()
        self.answers[self.current_index] = (None if v==-1 else int(v))
        self.refresh_qjump_buttons()

    def refresh_qjump_buttons(self):
        children = self.qjump_frame.winfo_children()
        # skip first label
        for idx, widget in enumerate(children[1:], start=0):
            if isinstance(widget, ttk.Button):
                txt = str(idx+1)
                if self.answers[idx] is not None: txt = f"{idx+1} *"
                widget.config(text=txt)

    def update_nav(self):
        if self.current_index == 0: self.prev_btn.state(['disabled'])
        else: self.prev_btn.state(['!disabled'])
        if self.current_index >= len(self.questions)-1: self.next_btn.state(['disabled'])
        else: self.next_btn.state(['!disabled'])

    def go_prev(self):
        self.save_choice()
        if self.current_index>0:
            self.current_index -= 1; self.show_question()

    def go_next(self):
        self.save_choice()
        if self.current_index < len(self.questions)-1:
            self.current_index += 1; self.show_question()

    def goto_question(self, idx):
        self.save_choice()
        if 0 <= idx < len(self.questions):
            self.current_index = idx; self.show_question()

    def submit_quiz(self):
        if not self.questions:
            messagebox.showinfo("No quiz","No questions available."); return
        if not messagebox.askyesno("Submit","Submit quiz now?"): return
        self.timer_running=False
        if self.timer_id: self.after_cancel(self.timer_id); self.timer_id=None
        score=0; total=len(self.questions)
        for i,q in enumerate(self.questions):
            ans = self.answers[i]
            if ans is not None and ans == q['answer']: score += 1
        # save score
        user = self.controller.current_user
        conn = sqlite3.connect(DB); cur = conn.cursor()
        cur.execute("INSERT INTO scores (user_id, score, total, category, timestamp) VALUES (?,?,?,?,?)",
                    (user['id'], score, total, user['category'], datetime.datetime.now().isoformat()))
        conn.commit(); conn.close()
        messagebox.showinfo("Result", f"You scored {score}/{total}")
        self.controller.show_frame(ScoreboardFrame)

    def countdown(self):
        if not self.timer_running:
            self.time_label.config(text="")
            return
        mins, secs = divmod(self.timer_seconds, 60)
        self.time_label.config(text=f"Time left: {mins:02d}:{secs:02d}")
        if self.timer_seconds <= 0:
            self.timer_running=False; messagebox.showinfo("Time's up","Auto-submitting quiz."); self.submit_quiz(); return
        self.timer_seconds -= 1
        self.timer_id = self.after(1000, self.countdown)

# --------------------------
# Scoreboard
# --------------------------
class ScoreboardFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=10)
        self.controller = controller
        header = ttk.Label(self, text="Scoreboard — Top Scores", font=self.controller.font_title, foreground=self.controller.colors['accent_dark'])
        header.pack(pady=(6,8), anchor='w')

        cols = ('user','score','total','cat','time')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=12)
        for c,w in [('user',220), ('score',80), ('total',80), ('cat',140), ('time',200)]:
            self.tree.heading(c, text=c.capitalize()); self.tree.column(c, width=w, anchor='center')
        self.tree.pack(padx=8, pady=12, fill='x')

        btns = ttk.Frame(self); btns.pack(pady=8)
        ttk.Button(btns, text="Back to Home", command=lambda: controller.show_frame(HomeFrame)).pack(side='left', padx=6)
        ttk.Button(btns, text="Refresh", command=self.load_scores).pack(side='left', padx=6)
        ttk.Button(btns, text="Clear My Attempts", command=self.clear_my_attempts).pack(side='left', padx=6)

    def on_show(self):
        self.load_scores()

    def load_scores(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = sqlite3.connect(DB); cur = conn.cursor()
        cur.execute("""
            SELECT u.username, s.score, s.total, s.category, s.timestamp
            FROM scores s JOIN users u ON s.user_id = u.id
            ORDER BY s.score DESC, s.timestamp DESC
            LIMIT 50
        """)
        rows = cur.fetchall(); conn.close()
        for r in rows: self.tree.insert('', 'end', values=r)

    def clear_my_attempts(self):
        u = self.controller.current_user
        if not u: messagebox.showerror("Not logged in","Login first."); return
        if not messagebox.askyesno("Confirm","Clear all your attempts?"): return
        conn = sqlite3.connect(DB); cur = conn.cursor()
        cur.execute("DELETE FROM scores WHERE user_id=?", (u['id'],)); conn.commit(); conn.close()
        messagebox.showinfo("Cleared","Your attempts cleared."); self.load_scores()

# --------------------------
# Run
# --------------------------
def main():
    init_db()
    app = QuizApp()
    app.mainloop()

if __name__ == '__main__':
    main()
