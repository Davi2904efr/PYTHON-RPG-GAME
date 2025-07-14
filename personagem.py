import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageSequence
import json
import os
import random


GIF_FILE = os.path.join(os.path.dirname(__file__), 'dnd-dice.gif')
DB_FILE = 'database.json'


class UserManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.users = self.load_users()

    def load_users(self):
        if not os.path.exists(self.db_file):
            return {}
        with open(self.db_file, 'r') as f:
            return json.load(f)

    def save_users(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.users, f, indent=4)

    def register_user(self, username, email, password):
        if email in self.users:
            return False, "Email já cadastrado."
        self.users[email] = {
            'username': username,
            'password': password,
            'progress': {
                'nivel': 1,
                'xp': 0,
                'inimigo_hp': 100
            }
        }
        self.save_users()
        return True, "Conta criada com sucesso."

    def authenticate_user(self, email, password):
        user = self.users.get(email)
        if user and user['password'] == password:
            return True, user
        return False, None

    def update_progress(self, email, progress):
        if email in self.users:
            self.users[email]['progress'] = progress
            self.save_users()


class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RPG - Sistema de Login")
        self.root.geometry("450x500")
        self.user_manager = UserManager(DB_FILE)
        self.current_user_email = None
        self.build_login_screen()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def build_login_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Email").pack()
        email_entry = tk.Entry(self.root)
        email_entry.pack()

        tk.Label(self.root, text="Senha").pack()
        password_entry = tk.Entry(self.root, show="*")
        password_entry.pack()

        tk.Button(self.root, text="Entrar", command=lambda: self.login(email_entry.get(), password_entry.get())).pack(pady=10)
        tk.Button(self.root, text="Criar Conta", command=self.build_register_screen).pack()

    def build_register_screen(self):
        self.clear_screen()

        tk.Label(self.root, text="Nome").pack()
        username_entry = tk.Entry(self.root)
        username_entry.pack()

        tk.Label(self.root, text="Email").pack()
        email_entry = tk.Entry(self.root)
        email_entry.pack()

        tk.Label(self.root, text="Senha").pack()
        password_entry = tk.Entry(self.root, show="*")
        password_entry.pack()

        def register():
            success, msg = self.user_manager.register_user(
                username_entry.get(),
                email_entry.get(),
                password_entry.get()
            )
            messagebox.showinfo("Cadastro", msg)
            if success:
                self.build_login_screen()

        tk.Button(self.root, text="Registrar", command=register).pack(pady=10)
        tk.Button(self.root, text="Voltar", command=self.build_login_screen).pack()

    def login(self, email, password):
        success, user = self.user_manager.authenticate_user(email, password)
        if success:
            self.current_user_email = email
            self.build_game_screen(user)
        else:
            messagebox.showerror("Erro", "Email ou senha incorretos.")

    def build_game_screen(self, user):
        self.clear_screen()
        progress = user['progress']
        nivel = progress['nivel']
        xp = progress['xp']
        xp_necessario = 100 + (nivel - 1) * 50
        inimigo_hp = progress.get('inimigo_hp', 100 + nivel * 30)

        tk.Label(self.root, text=f"Bem-vindo, {user['username']}").pack()
        nivel_label = tk.Label(self.root, text=f"Nível: {nivel}")
        nivel_label.pack()
        xp_label = tk.Label(self.root, text=f"XP: {xp}/{xp_necessario}")
        xp_label.pack()
        inimigo_label = tk.Label(self.root, text=f"Inimigo (Nível {nivel}) HP: {inimigo_hp}")
        inimigo_label.pack()
        resultado_label = tk.Label(self.root, text="")
        resultado_label.pack(pady=10)

        gif_label = tk.Label(self.root)
        gif_label.pack()
        gif_frames = []

        def atacar():
            nonlocal gif_frames
            try:
                anim = Image.open(GIF_FILE)
                gif_frames = [ImageTk.PhotoImage(frame.copy().convert('RGBA')) for frame in ImageSequence.Iterator(anim)]

                def animate(index=0):
                    if index < len(gif_frames):
                        gif_label.configure(image=gif_frames[index])
                        gif_label.image = gif_frames[index]
                        self.root.after(60, lambda: animate(index + 1))
                    else:
                        gif_label.configure(image="")
                        executar_ataque()

                animate()
            except FileNotFoundError:
                messagebox.showerror("Erro", f"O arquivo {GIF_FILE} não foi encontrado.")
            except Exception as e:
                messagebox.showerror("Erro ao carregar GIF", str(e))

        def executar_ataque():
            nonlocal xp, nivel, inimigo_hp, xp_necessario

            dado = random.randint(1, 20)
            dano = 0

            dano_fraco = 5 + nivel * 1
            dano_medio = 10 + nivel * 2
            dano_forte = 15 + nivel * 3
            dano_critico = 25 + nivel * 5

            if dado <= 10:
                resultado = f"Você rolou {dado}: Fracasso! Nenhum dano causado."
            else:
                if dado == 20:
                    dano = dano_critico
                    resultado = f"CRÍTICO! Você rolou {dado} e causou {dano} de dano!"
                elif dado >= 15:
                    dano = dano_medio
                    resultado = f"Sucesso! Você rolou {dado} e causou {dano} de dano!"
                elif dado >= 11:
                    dano = dano_fraco
                    resultado = f"Sucesso leve! Você rolou {dado} e causou {dano} de dano!"

                inimigo_hp -= dano
                xp += 10

                if xp >= xp_necessario:
                    nivel += 1
                    xp -= xp_necessario
                    xp_necessario = 100 + (nivel - 1) * 50
                    inimigo_hp = 100 + nivel * 30
                    messagebox.showinfo("UP!", f"Você subiu para o nível {nivel}!")

                if inimigo_hp <= 0:
                    recompensa_xp = 20 + 5 * nivel
                    messagebox.showinfo("Vitória!", f"Inimigo derrotado! Você ganhou {recompensa_xp} XP.")
                    xp += recompensa_xp
                    inimigo_hp = 100 + nivel * 30

            resultado_label.config(text=resultado)
            xp_label.config(text=f"XP: {xp}/{xp_necessario}")
            nivel_label.config(text=f"Nível: {nivel}")
            inimigo_label.config(text=f"Inimigo (Nível {nivel}) HP: {inimigo_hp}")

            self.user_manager.update_progress(self.current_user_email, {
                'nivel': nivel,
                'xp': xp,
                'inimigo_hp': inimigo_hp
            })

        tk.Button(self.root, text="Atacar (d20)", command=atacar).pack(pady=10)
        tk.Button(self.root, text="Sair", command=self.build_login_screen).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()
