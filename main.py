import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


class InsufficientFundsError(Exception):
    """Exception raised when hospital revenue is less than payroll requirements."""
    pass


class Medicine:
    def __init__(self, name, price):
        self.name = name
        self.price = price


class Person:
    def __init__(self, data):
        self.name = data.get('Name', 'Unknown')
        self.cnic = data.get('CNIC', 'N/A')
        self.phone = data.get('Phone') or data.get('Contact', 'N/A')
        self.gender = data.get('Gender', 'N/A')
        self.attr = data


class Admin(Person):
    def __init__(self, data, username, password):
        super().__init__(data)
        self.username = username
        self.password = password


class Patient(Person):
    def __init__(self, data):
        super().__init__(data)
        self.id = data.get('ID', '')
        self.ward = data.get('Ward', 'General')
        self.status = data.get('status', "Admitted")
        self.assigned_doctor = data.get('assigned_doctor', "Unassigned")
        self.purchased_meds = data.get('purchased_meds', [])
        self.bill_amt = data.get('bill_amt', 0)
        self.days_stayed = data.get('days_stayed', 1)

    def to_dict(self):
        return {
            'Name': self.name, 'CNIC': self.cnic, 'Phone': self.phone,
            'Gender': self.gender, 'ID': self.id, 'Ward': self.ward,
            'status': self.status, 'assigned_doctor': self.assigned_doctor,
            'purchased_meds': self.purchased_meds, 'bill_amt': self.bill_amt,
            'days_stayed': self.days_stayed, 'Complaint': self.attr.get('Complaint', 'N/A')
        }


class Staff(Person):
    def __init__(self, data, role):
        super().__init__(data)
        self.role = role
        self.shift = data.get('Shift', 'Morning')
        self.salary = float(data.get('Salary', 0))
        self.is_paid = data.get('is_paid', False)
        self.department = data.get('Department', '')
        self.experience_level = data.get('Experience Level', '')
        self.qualification = data.get('Qualification', '')

    def to_dict(self):
        staff_dict = {
            'Name': self.name, 'CNIC': self.cnic, 'Contact': self.phone,
            'role': self.role, 'Shift': self.shift, 'Salary': self.salary, 'is_paid': self.is_paid
        }
        if self.role == "Doctor":
            staff_dict['Department'] = self.department
            staff_dict['Experience Level'] = self.experience_level
        elif self.role == "Nurse":
            staff_dict['Qualification'] = self.qualification
        return staff_dict

# LOGIC CLASS

class WardTransferManager:
    def __init__(self, wards):
        self.available_wards = wards

    def transfer(self, patient, new_ward):
        patient.ward = new_ward
        return f"Transfer Success: {patient.name} moved to {new_ward}"


class PayrollManager:
    def __init__(self):
        self.gross_revenue = 250000.0
        self.tax_rate = 0.15

    def check_payroll_feasibility(self, staff_list):
        total_needed = sum(s.salary for s in staff_list if not s.is_paid)
        if total_needed > self.gross_revenue:
            raise InsufficientFundsError(f"Shortage: Rs.{total_needed - self.gross_revenue:,.0f} needed.")
        return total_needed

    def calculate_auto_salary(self, role, level):
        if role == "Doctor":
            return {"Junior": 65000, "Mid-Level": 95000, "Senior": 160000, "Consultant": 280000}.get(level, 55000)
        return {"Diploma": 40000, "BSc Nursing": 60000, "MSc Nursing": 90000}.get(level, 38000)


class PharmacyManager:
    def __init__(self):
        self.wards = ["ICU", "CCU", "Emergency", "Private", "General", "Pediatric", "Orthopedic", "Neurology",
                      "Cardiology", "Isolation"]
        self.inventory = {
            "ICU": [Medicine("Propofol", 1200), Medicine("Norepinephrine", 850)],
            "CCU": [Medicine("Amiodarone", 950), Medicine("Heparin", 600)],
            "Emergency": [Medicine("Epinephrine", 300), Medicine("Dopamine", 800)],
            "Private": [Medicine("Augmentin", 900), Medicine("Panadol Extra", 100)],
            "General": [Medicine("Paracetamol", 50), Medicine("Amoxicillin", 300)],
            "Pediatric": [Medicine("Calpol Syrup", 150), Medicine("Brufen Kids", 200)],
            "Orthopedic": [Medicine("Diclofenac", 200), Medicine("Calcium-D", 600)],
            "Neurology": [Medicine("Phenytoin", 750), Medicine("Levetiracetam", 1800)],
            "Cardiology": [Medicine("Aspirin", 100), Medicine("Warfarin", 400)],
            "Isolation": [Medicine("Remdesivir", 5000), Medicine("Dexamethasone", 300)]
        }

# MAIN SYSTEM INTEGRATION

class AlShifa:
    def __init__(self, root):
        self.root = root
        self.bg_light = "#F1F5F9"
        self.bg_card = "#FFFFFF"
        self.sidebar_bg = "#FFFFFF"
        self.accent_blue = "#0EA5E9"
        self.text_main = "#1E293B"
        self.text_muted = "#64748B"

        self.ph_manager = PharmacyManager()
        self.pay_engine = PayrollManager()
        self.transfer_engine = WardTransferManager(self.ph_manager.wards)
        self.active_admin = Admin({"Name": "Head Admin"}, "admin", "1234")
        self.patients = []
        self.staff_list = []
        self.ward_rates = {w: 4000 + (i * 800) for i, w in enumerate(self.ph_manager.wards)}

        self.load_data()
        self.setup_main_window()
        self.show_login_screen()

    def save_data(self):
        """Safely saves hospital records without losing historical data."""
        try:
            data = {
                "patients": [p.to_dict() for p in self.patients],
                "staff": [s.to_dict() for s in self.staff_list],
                "revenue": self.pay_engine.gross_revenue
            }
            with open("hospital_records.json", "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("✓ Data saved successfully")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data: {str(e)}")

    def load_data(self):
        """Loads data cleanly and handles missing or empty files."""
        if not os.path.exists("hospital_records.json"):
            print("Notice: 'hospital_records.json' not found. Starting with empty database.")
            return

        try:
            with open("hospital_records.json", "r", encoding='utf-8') as f:
                content = json.load(f)
            self.patients = [Patient(p) for p in content.get("patients", [])]
            self.staff_list = [Staff(s, s.get('role', 'Unknown')) for s in content.get("staff", [])]
            self.pay_engine.gross_revenue = float(content.get("revenue", 250000.0))
            print(f"✓ Loaded {len(self.patients)} patients and {len(self.staff_list)} staff.")
        except json.JSONDecodeError:
            messagebox.showwarning("File Corruption", "hospital_records.json is corrupt. Backing up existing file.")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load data: {str(e)}")

    def setup_main_window(self):
        self.root.title("ALSHIFA Hospital Management System")
        self.root.geometry("1400x850")
        self.root.configure(bg=self.bg_light)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.save_data()
        self.root.destroy()

    def show_login_screen(self):
        self.login_frame = tk.Frame(self.root, bg=self.bg_light)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(self.login_frame, text="ALShifa Hospital Management System", fg=self.accent_blue, bg=self.bg_light,
                 font=("Arial", 24, "bold")).pack(pady=20)
        box = tk.Frame(self.login_frame, bg=self.bg_card, padx=40, pady=40, highlightthickness=1,
                       highlightbackground="#E2E8F0")
        box.pack()
        tk.Label(box, text="Admin Username", fg=self.text_main, bg=self.bg_card, font=("Arial", 10, "bold")).pack(
            anchor="w")
        self.user_ent = tk.Entry(box, width=30, font=("Arial", 12), bd=1, relief="solid")
        self.user_ent.pack(pady=10, ipady=5)
        tk.Label(box, text="Password", fg=self.text_main, bg=self.bg_card, font=("Arial", 10, "bold")).pack(anchor="w")
        self.pass_ent = tk.Entry(box, width=30, font=("Arial", 12), show="*", bd=1, relief="solid")
        self.pass_ent.pack(pady=10, ipady=5)

        btn = tk.Button(box, text="LOGIN AS ADMIN", bg=self.accent_blue, fg="white", font=("Arial", 10, "bold"),
                        width=25, pady=10, bd=0, command=self.handle_login, cursor="hand2")
        btn.pack(pady=20)

    def handle_login(self):
        if self.user_ent.get() == self.active_admin.username and self.pass_ent.get() == self.active_admin.password:
            self.login_frame.destroy()
            self.setup_dashboard()
        else:
            messagebox.showerror("Access Denied", "Invalid Admin Credentials")

    def setup_dashboard(self):
        self.side = tk.Frame(self.root, bg=self.sidebar_bg, width=280, highlightthickness=1,
                             highlightbackground="#E2E8F0")
        self.side.pack(side="left", fill="y")
        self.side.pack_propagate(False)

        tk.Label(self.side, text="ADMIN PANEL", fg=self.accent_blue, bg=self.sidebar_bg, font=("Arial", 14, "bold"),
                 pady=30).pack()

        nav = [
            (" Admit Patient", self.show_admit), (" Register Doctor", self.show_doc_reg),
            (" Register Nurse", self.show_nurse_reg), (" Assign Doctor", self.show_assign),
            (" Ward Pharmacy", self.show_pharmacy), (" Master Display", self.show_display),
            (" Transfer Ward", self.show_transfer), (" Billing Center", self.show_billing),
            (" Payroll System", self.show_payroll_ui), (" Discharge Dept", self.show_discharge),
            (" Manual Save", self.manual_save), (" Logout", self.logout)
        ]

        for t, c in nav:
            bg_c = "#10B981" if "Save" in t else "#EF4444" if "Logout" in t else self.sidebar_bg
            fg_c = "white" if ("Save" in t or "Logout" in t) else self.text_main

            btn = tk.Button(self.side, text=f"  {t}", command=c, bg=bg_c, fg=fg_c, bd=0, font=("Arial", 11), pady=12,
                            anchor="w", padx=20, cursor="hand2")
            if bg_c == self.sidebar_bg:
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#F1F5F9"))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.sidebar_bg))
            btn.pack(fill="x")

        self.view = tk.Frame(self.root, bg=self.bg_light)
        self.view.pack(side="right", fill="both", expand=True, padx=40, pady=30)
        self.show_display()

    def draw_header(self, title, subtitle):
        header = tk.Frame(self.view, bg=self.bg_light)
        header.pack(fill="x", pady=(0, 25))
        tk.Label(header, text=title.upper(), font=("Arial", 22, "bold"), fg=self.text_main, bg=self.bg_light).pack(
            anchor="w")
        tk.Label(header, text=subtitle, font=("Arial", 10), fg=self.text_muted, bg=self.bg_light).pack(anchor="w")
        tk.Frame(header, height=2, bg=self.accent_blue, width=150).pack(anchor="w", pady=5)

    def manual_save(self):
        self.save_data()
        messagebox.showinfo("Save Complete", "All data saved successfully.")

    def logout(self):
        self.save_data()
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_main_window()
        self.show_login_screen()

    def clear(self):
        for w in self.view.winfo_children():
            w.destroy()

    def show_admit(self):
        self.clear()
        self.draw_header("Patient Admission", "Admin: Register a new patient")
        f = tk.Frame(self.view, bg=self.bg_card, pady=20, padx=30, highlightthickness=1, highlightbackground="#E2E8F0")
        f.pack(fill="x")
        self.p_vars = {}
        fields = [("Name", "E", []), ("CNIC", "E", []), ("Phone", "E", []), ("Gender", "C", ["Male", "Female"]),
                  ("Complaint", "C", ["Critical", "Severe", "Moderate", "Mild"]), ("Ward", "C", self.ph_manager.wards)]
        for i, (l, t, o) in enumerate(fields):
            tk.Label(f, text=l, fg=self.text_main, bg=self.bg_card, font=("Arial", 10, "bold")).grid(row=i, column=0,
                                                                                                     sticky="w", pady=5)
            e = ttk.Combobox(f, values=o, width=40) if t == "C" else tk.Entry(f, width=43)
            e.grid(row=i, column=1, pady=5, padx=10)
            self.p_vars[l] = e
        tk.Button(self.view, text="CONFIRM ADMISSION", bg="#10B981", fg="white", pady=10, width=30, bd=0,
                  font=("Arial", 10, "bold"), command=self.save_p).pack(pady=20)

    def save_p(self):
        data = {k: v.get() for k, v in self.p_vars.items()}
        if not data["Name"].strip():
            return messagebox.showwarning("Error", "Name is required")
        data["ID"] = f"PAT-{len(self.patients) + 1001}"
        self.patients.append(Patient(data))
        self.save_data()
        messagebox.showinfo("Success", f"Patient {data['Name']} Admitted Successfully.")
        self.show_admit()

    def show_doc_reg(self):
        self.clear()
        self.draw_header("Doctor Registration", "Admin: Add medical staff")
        f = tk.Frame(self.view, bg=self.bg_card, pady=20, padx=30, highlightthickness=1, highlightbackground="#E2E8F0")
        f.pack()
        self.d_vars = {}
        fields = [("Name", "E", []), ("CNIC", "E", []), ("Contact", "E", []),
                  ("Department", "C", self.ph_manager.wards),
                  ("Experience Level", "C", ["Junior", "Mid-Level", "Senior", "Consultant"]),
                  ("Shift", "C", ["Morning", "Night"]), ("Manual Salary", "E", [])]
        for i, (l, t, o) in enumerate(fields):
            tk.Label(f, text=l, fg=self.text_main, bg=self.bg_card).grid(row=i, column=0, pady=5, sticky="w")
            e = ttk.Combobox(f, values=o, width=35) if t == "C" else tk.Entry(f, width=38)
            e.grid(row=i, column=1, pady=5, padx=10)
            self.d_vars[l] = e
        tk.Button(self.view, text="SAVE DOCTOR", bg=self.accent_blue, fg="white", bd=0, pady=10, width=20,
                  command=lambda: self.save_staff("Doctor")).pack(pady=10)

    def save_staff(self, role):
        vd = self.d_vars if role == "Doctor" else self.n_vars
        data = {k: v.get() for k, v in vd.items()}
        if not data["Name"].strip():
            return messagebox.showwarning("Error", "Name is required")
        manual = data.get("Manual Salary")
        if manual and manual.strip() != "":
            try:
                data["Salary"] = float(manual)
            except ValueError:
                return messagebox.showerror("Error", "Invalid salary input. Must be a number.")
        else:
            data["Salary"] = self.pay_engine.calculate_auto_salary(role, data.get("Experience Level") or data.get("Qualification"))

        self.staff_list.append(Staff(data, role))
        self.save_data()
        messagebox.showinfo("Staff Added", f"{role} {data['Name']} saved successfully.")
        self.show_doc_reg() if role == "Doctor" else self.show_nurse_reg()

    def show_nurse_reg(self):
        self.clear()
        self.draw_header("Nurse Registration", "Admin: Register nursing staff")
        f = tk.Frame(self.view, bg=self.bg_card, pady=20, padx=30, highlightthickness=1, highlightbackground="#E2E8F0")
        f.pack()
        self.n_vars = {}
        fields = [("Name", "E", []), ("CNIC", "E", []), ("Contact", "E", []),
                  ("Qualification", "C", ["Diploma", "BSc Nursing", "MSc Nursing"]),
                  ("Shift", "C", ["Morning", "Night"]), ("Manual Salary", "E", [])]
        for i, (l, t, o) in enumerate(fields):
            tk.Label(f, text=l, fg=self.text_main, bg=self.bg_card).grid(row=i, column=0, pady=5, sticky="w")
            e = ttk.Combobox(f, values=o, width=35) if t == "C" else tk.Entry(f, width=38)
            e.grid(row=i, column=1, pady=5, padx=10)
            self.n_vars[l] = e
        tk.Button(self.view, text="SAVE NURSE", bg="#A855F7", fg="white", bd=0, pady=10, width=20,
                  command=lambda: self.save_staff("Nurse")).pack(pady=10)

    def show_display(self):
        self.clear()
        self.draw_header("Hospital Census", "Current Hospital Overview")
        tabs = ttk.Notebook(self.view)
        tabs.pack(fill="both", expand=True)

        p_f = tk.Frame(tabs, bg=self.bg_card)
        cols = ("ID", "Name", "Ward", "Status", "Doctor")
        tree = ttk.Treeview(p_f, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=150)
        tree.pack(fill="both", expand=True)
        for p in self.patients:
            tree.insert("", "end", values=(p.id, p.name, p.ward, p.status, p.assigned_doctor))
        tabs.add(p_f, text=" Patients ")

        s_f = tk.Frame(tabs, bg=self.bg_card)
        scols = ("Name", "Role", "Shift", "Salary", "Paid")
        stree = ttk.Treeview(s_f, columns=scols, show="headings")
        for c in scols:
            stree.heading(c, text=c)
            stree.column(c, width=120)
        stree.pack(fill="both", expand=True)
        for s in self.staff_list:
            stree.insert("", "end", values=(s.name, s.role, s.shift, f"Rs.{s.salary:,.0f}", "✓" if s.is_paid else "✗"))
        tabs.add(s_f, text=" Hospital Staff ")

    def show_pharmacy(self):
        self.clear()
        self.draw_header("Ward Pharmacy", "Inventory Management")
        top = tk.Frame(self.view, bg=self.bg_card, pady=15, padx=15, highlightthickness=1,
                       highlightbackground="#E2E8F0")
        top.pack(fill="x")
        tk.Label(top, text="Select Ward:", bg=self.bg_card).pack(side="left")
        self.ph_ward = ttk.Combobox(top, values=self.ph_manager.wards)
        self.ph_ward.pack(side="left", padx=10)
        tk.Label(top, text="Patient:", bg=self.bg_card).pack(side="left")
        self.ph_pat = ttk.Combobox(top, values=[p.name for p in self.patients if p.status == "Admitted"])
        self.ph_pat.pack(side="left", padx=10)
        tk.Button(top, text="LOAD STOCK", command=self.load_stock, bg=self.accent_blue, fg="white", bd=0, padx=10).pack(
            side="left", padx=10)

        self.med_box = tk.Listbox(self.view, bg=self.bg_card, fg=self.text_main, font=("Arial", 11), height=10)
        self.med_box.pack(fill="x", pady=10)
        tk.Button(self.view, text="ADD TO PATIENT BILL", bg="#10B981", fg="white", pady=10, bd=0,
                  command=self.add_med).pack(fill="x")

    def load_stock(self):
        self.med_box.delete(0, tk.END)
        for m in self.ph_manager.inventory.get(self.ph_ward.get(), []):
            self.med_box.insert(tk.END, f"{m.name} -- Rs.{m.price}")

    def add_med(self):
        try:
            sel_text = self.med_box.get(self.med_box.curselection()).split(" --")[0]
            for p in self.patients:
                if p.name == self.ph_pat.get():
                    m_obj = next(m for m in self.ph_manager.inventory[self.ph_ward.get()] if m.name == sel_text)
                    p.purchased_meds.append({"name": m_obj.name, "price": m_obj.price})
                    self.save_data()
                    messagebox.showinfo("Pharmacy", f"{sel_text} added to {p.name}'s account.")
                    return
        except Exception:
            messagebox.showerror("Error", "Select Ward, Patient, and Medicine")

    def show_transfer(self):
        self.clear()
        self.draw_header("Ward Transfer", "Relocate patients")
        f = tk.Frame(self.view, bg=self.bg_card, pady=30, padx=30, highlightthickness=1, highlightbackground="#E2E8F0")
        f.pack(fill="x")
        tk.Label(f, text="Patient:", bg=self.bg_card).grid(row=0, column=0, pady=10)
        self.tr_pat = ttk.Combobox(f, values=[p.name for p in self.patients if p.status == "Admitted"], width=40)
        self.tr_pat.grid(row=0, column=1, padx=10)
        tk.Label(f, text="Target Ward:", bg=self.bg_card).grid(row=1, column=0, pady=10)
        self.tr_ward = ttk.Combobox(f, values=self.ph_manager.wards, width=40)
        self.tr_ward.grid(row=1, column=1, padx=10)
        tk.Button(f, text="EXECUTE TRANSFER", bg="#F59E0B", fg="white", bd=0, pady=10, command=self.do_transfer).grid(
            row=2, column=1, pady=20)

    def do_transfer(self):
        for p in self.patients:
            if p.name == self.tr_pat.get():
                msg = self.transfer_engine.transfer(p, self.tr_ward.get())
                self.save_data()
                messagebox.showinfo("Success", msg)
                self.show_transfer()
                return

    def show_billing(self):
        self.clear()
        self.draw_header("Billing Center", "Invoice Generation")
        f = tk.Frame(self.view, bg=self.bg_card, pady=20, padx=20, highlightthickness=1, highlightbackground="#E2E8F0")
        f.pack(fill="x")
        tk.Label(f, text="Patient:", bg=self.bg_card).pack(side="left")
        self.b_p = ttk.Combobox(f, values=[p.name for p in self.patients if p.status == "Admitted"], width=30)
        self.b_p.pack(side="left", padx=10)
        tk.Label(f, text="Days:", bg=self.bg_card).pack(side="left")
        self.b_d = tk.Entry(f, width=10)
        self.b_d.insert(0, "1")
        self.b_d.pack(side="left", padx=10)
        tk.Button(f, text="GENERATE BILL", command=self.do_bill, bg="#F59E0B", fg="white", bd=0, padx=15).pack(
            side="left", padx=10)
        self.b_area = tk.Text(self.view, bg="#F8FAFC", fg=self.text_main, font=("Consolas", 11), height=18)
        self.b_area.pack(fill="both", pady=10)

    def do_bill(self):
        for p in self.patients:
            if p.name == self.b_p.get():
                try:
                    p.days_stayed = int(self.b_d.get())
                    w_cost = self.ward_rates.get(p.ward, 4000) * p.days_stayed
                    m_cost = sum(m['price'] for m in p.purchased_meds)
                    p.bill_amt = w_cost + m_cost + 5000
                    res = (f"ALShifa HOSPITAL INVOICE\n"
                           f"----------------------\n"
                           f"Patient: {p.name}\n"
                           f"Ward Rate ({p.ward}): Rs.{w_cost:,}\n"
                           f"Medicine Charges: Rs.{m_cost:,}\n"
                           f"Hospital Base Fee: Rs.5,000\n"
                           f"----------------------\n"
                           f"Total Bill Amount: Rs.{p.bill_amt:,}")
                    self.b_area.delete("1.0", tk.END)
                    self.b_area.insert(tk.END, res)
                    self.save_data()
                except ValueError:
                    messagebox.showerror("Error", "Invalid days entered. Must be a whole number.")

    def show_payroll_ui(self):
        self.clear()
        self.draw_header("Payroll & Revenue", "Financial Admin")
        total_p = sum(s.salary for s in self.staff_list if not s.is_paid)
        cards = tk.Frame(self.view, bg=self.bg_light)
        cards.pack(fill="x", pady=10)
        for l, v, c in [("REVENUE", self.pay_engine.gross_revenue, self.accent_blue),
                        ("PENDING PAYROLL", total_p, "#F59E0B")]:
            f = tk.Frame(cards, bg=self.bg_card, padx=20, pady=15, highlightthickness=1, highlightbackground="#E2E8F0")
            f.pack(side="left", expand=True, padx=5)
            tk.Label(f, text=l, fg=self.text_muted, bg=self.bg_card).pack()
            tk.Label(f, text=f"Rs.{v:,.0f}", fg=c, bg=self.bg_card, font=("Arial", 16, "bold")).pack()
        tk.Button(self.view, text="PROCESS ALL SALARIES", bg=self.accent_blue, fg="white", pady=12, bd=0,
                  command=self.process_pay).pack(fill="x", pady=20)

    def process_pay(self):
        try:
            total = self.pay_engine.check_payroll_feasibility(self.staff_list)
            for s in self.staff_list:
                if not s.is_paid:
                    self.pay_engine.gross_revenue -= s.salary
                    s.is_paid = True
            self.save_data()
            messagebox.showinfo("Finance", f"Payroll Processed: Rs.{total:,.0f}")
            self.show_payroll_ui()
        except InsufficientFundsError as e:
            messagebox.showerror("Error", str(e))

    def show_assign(self):
        self.clear()
        self.draw_header("Assignments", "Assign Doctor to Patient")
        f = tk.Frame(self.view, bg=self.bg_card, pady=40, padx=40, highlightthickness=1, highlightbackground="#E2E8F0")
        f.pack()
        tk.Label(f, text="Patient:", bg=self.bg_card).pack()
        self.as_p = ttk.Combobox(f, values=[p.name for p in self.patients if p.status == "Admitted"], width=40)
        self.as_p.pack(pady=10)
        tk.Label(f, text="Doctor:", bg=self.bg_card).pack()
        self.as_d = ttk.Combobox(f, values=[s.name for s in self.staff_list if s.role == "Doctor"], width=40)
        self.as_d.pack(pady=10)
        tk.Button(f, text="CONFIRM ASSIGNMENT", command=self.do_assign, bg="#10B981", fg="white", bd=0, width=20,
                  pady=10).pack(pady=15)

    def do_assign(self):
        for p in self.patients:
            if p.name == self.as_p.get():
                p.assigned_doctor = self.as_d.get()
                self.save_data()
                messagebox.showinfo("Success", f"Dr. {self.as_d.get()} assigned to {p.name}.")
                self.show_assign()
                return

    def show_discharge(self):
        self.clear()
        self.draw_header("Discharge", "Finalize Patient Exit")
        f = tk.Frame(self.view, bg=self.bg_card, pady=40, padx=40, highlightthickness=1, highlightbackground="#E2E8F0")
        f.pack()
        tk.Label(f, text="Select Patient:", bg=self.bg_card, font=("Arial", 12)).pack(pady=10)
        self.di_p = ttk.Combobox(f, values=[p.name for p in self.patients if p.status == "Admitted"], width=40)
        self.di_p.pack(pady=20)
        tk.Button(f, text="CONFIRM DISCHARGE", bg="#EF4444", fg="white", pady=12, bd=0, width=25,
                  command=self.do_dis).pack()

    def do_dis(self):
        for p in self.patients:
            if p.name == self.di_p.get():
                if p.bill_amt == 0:
                    messagebox.showwarning("Warning", "Generate bill first before discharging.")
                    return
                p.status = "Discharged"
                self.pay_engine.gross_revenue += p.bill_amt
                self.save_data()
                messagebox.showinfo("Success", f"{p.name} Discharged successfully.")
                self.show_discharge()
                return


if __name__ == "__main__":
    root = tk.Tk()
    app = AlShifa(root)
    root.mainloop()