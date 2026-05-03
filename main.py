"""
GitHub User Finder - графический интерфейс
Автор: Воронков Никита
"""

import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
from github_finder import GitHubAPI, FavoritesManager

class GitHubUserFinder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GitHub User Finder - Поиск пользователей GitHub")
        self.root.geometry("1100x700")
        self.root.resizable(True, True)
        
        # Инициализация менеджеров
        self.api = GitHubAPI()
        self.favorites_manager = FavoritesManager()
        
        # Текущий режим отображения
        self.showing_favorites = False
        
        self.setup_ui()
        self.load_favorites_to_tree()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ========== ВЕРХНЯЯ ПАНЕЛЬ: ПОИСК ==========
        search_frame = ttk.LabelFrame(main_frame, text="🔍 Поиск пользователей GitHub", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Имя пользователя:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_entry = ttk.Entry(search_frame, width=40, font=("Arial", 10))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self.search_users())
        
        self.search_button = ttk.Button(search_frame, text="🔎 Поиск", command=self.search_users)
        self.search_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.fav_button = ttk.Button(search_frame, text="⭐ Избранное", command=self.show_favorites)
        self.fav_button.pack(side=tk.LEFT)
        
        # ========== ЛЕВАЯ ПАНЕЛЬ: РЕЗУЛЬТАТЫ ПОИСКА ==========
        left_frame = ttk.LabelFrame(main_frame, text="📋 Результаты поиска", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Таблица результатов
        result_columns = ("Логин", "Тип", "Действие")
        self.result_tree = ttk.Treeview(left_frame, columns=result_columns, show="headings", height=20)
        
        self.result_tree.heading("Логин", text="Логин")
        self.result_tree.heading("Тип", text="Тип")
        self.result_tree.heading("Действие", text="Действие")
        
        self.result_tree.column("Логин", width=200)
        self.result_tree.column("Тип", width=100)
        self.result_tree.column("Действие", width=100)
        
        scrollbar1 = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar1.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Двойной клик для просмотра деталей
        self.result_tree.bind("<Double-1>", self.on_result_double_click)
        
        # ========== ПРАВАЯ ПАНЕЛЬ: ИЗБРАННОЕ ==========
        right_frame = ttk.LabelFrame(main_frame, text="⭐ Избранные пользователи", padding="10")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Таблица избранных
        fav_columns = ("Логин", "Тип", "Действие")
        self.fav_tree = ttk.Treeview(right_frame, columns=fav_columns, show="headings", height=20)
        
        self.fav_tree.heading("Логин", text="Логин")
        self.fav_tree.heading("Тип", text="Тип")
        self.fav_tree.heading("Действие", text="Действие")
        
        self.fav_tree.column("Логин", width=200)
        self.fav_tree.column("Тип", width=100)
        self.fav_tree.column("Действие", width=100)
        
        scrollbar2 = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.fav_tree.yview)
        self.fav_tree.configure(yscrollcommand=scrollbar2.set)
        
        self.fav_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Двойной клик для просмотра деталей
        self.fav_tree.bind("<Double-1>", self.on_fav_double_click)
        
        # ========== НИЖНЯЯ ПАНЕЛЬ: СТАТУС ==========
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе. Введите имя пользователя для поиска.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def search_users(self):
        """Поиск пользователей на GitHub"""
        query = self.search_entry.get().strip()
        
        # Валидация: поле не должно быть пустым
        if not query:
            messagebox.showwarning("Внимание", "Введите имя пользователя для поиска")
            return
        
        # Сброс режима отображения
        self.showing_favorites = False
        self.search_button.config(text="🔎 Поиск")
        
        # Очистка таблицы результатов
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # Обновление статуса
        self.status_var.set(f"Поиск пользователей по запросу '{query}'...")
        self.search_button.config(state=tk.DISABLED)
        
        # Запуск поиска в отдельном потоке
        thread = Thread(target=self._search_thread, args=(query,))
        thread.daemon = True
        thread.start()
    
    def _search_thread(self, query: str):
        """Поиск в отдельном потоке"""
        try:
            users = self.api.search_users(query)
            
            # Обновление GUI в основном потоке
            self.root.after(0, self._update_search_results, users)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
            self.root.after(0, lambda: self.status_var.set("Ошибка при поиске"))
        finally:
            self.root.after(0, lambda: self.search_button.config(state=tk.NORMAL))
    
    def _update_search_results(self, users: List[Dict]):
        """Обновление таблицы результатов поиска"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        if not users:
            self.status_var.set("Пользователи не найдены")
            return
        
        for user in users:
            login = user.get("login", "N/A")
            user_type = user.get("type", "User")
            is_fav = self.favorites_manager.is_favorite(login)
            
            action_text = "★" if not is_fav else "★ В избранном"
            
            item = self.result_tree.insert("", tk.END, values=(login, user_type, action_text))
            
            # Сохраняем данные пользователя
            self.result_tree.set(item, "#3", action_text)
        
        self.status_var.set(f"Найдено пользователей: {len(users)}")
    
    def show_favorites(self):
        """Показать избранных пользователей"""
        self.showing_favorites = True
        self.search_button.config(text="🔍 Показать всех")
        self.load_favorites_to_tree()
        self.status_var.set(f"Избранные пользователи: {len(self.favorites_manager.get_all_favorites())}")
    
    def load_favorites_to_tree(self):
        """Загрузка избранных в таблицу"""
        for item in self.fav_tree.get_children():
            self.fav_tree.delete(item)
        
        favorites = self.favorites_manager.get_all_favorites()
        
        for fav in favorites:
            login = fav.get("login", "N/A")
            user_type = fav.get("type", "User")
            
            item = self.fav_tree.insert("", tk.END, values=(login, user_type, "★ Удалить"))
            
            # Создаём кнопку удаления
            self.fav_tree.set(item, "#3", "★ Удалить")
    
    def on_result_double_click(self, event):
        """Обработка двойного клика по результату поиска"""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        login = self.result_tree.item(item, "values")[0]
        
        # Получаем данные пользователя
        user_data = self._get_user_data_from_login(login)
        if user_data:
            self.show_user_details(user_data)
    
    def on_fav_double_click(self, event):
        """Обработка двойного клика по избранному"""
        selection = self.fav_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        login = self.fav_tree.item(item, "values")[0]
        
        # Открываем профиль в браузере
        import webbrowser
        webbrowser.open(f"https://github.com/{login}")
        self.status_var.set(f"Открыт профиль: {login}")
    
    def _get_user_data_from_login(self, login: str) -> Dict:
        """Получение данных пользователя по логину"""
        # Сначала ищем в результатах поиска
        for item in self.result_tree.get_children():
            values = self.result_tree.item(item, "values")
            if values[0] == login:
                # Нужно получить полные данные через API
                try:
                    return self.api.get_user_details(login)
                except:
                    return {"login": login, "html_url": f"https://github.com/{login}"}
        return None
    
    def add_to_favorites(self, login: str, user_data: Dict = None):
        """Добавление пользователя в избранное"""
        if self.favorites_manager.is_favorite(login):
            messagebox.showinfo("Информация", f"Пользователь {login} уже в избранном")
            return
        
        # Получаем данные пользователя, если не переданы
        if not user_data:
            try:
                user_data = self.api.get_user_details(login)
            except:
                user_data = {"login": login}
        
        if self.favorites_manager.add_favorite(user_data):
            messagebox.showinfo("Успех", f"Пользователь {login} добавлен в избранное")
            self.load_favorites_to_tree()
            self.status_var.set(f"Добавлен в избранное: {login}")
            
            # Обновляем кнопку в результатах поиска
            for item in self.result_tree.get_children():
                values = self.result_tree.item(item, "values")
                if values[0] == login:
                    self.result_tree.set(item, "#3", "★ В избранном")
                    break
        else:
            messagebox.showwarning("Предупреждение", f"Не удалось добавить {login}")
    
    def remove_from_favorites(self, login: str):
        """Удаление пользователя из избранного"""
        if self.favorites_manager.remove_favorite(login):
            messagebox.showinfo("Успех", f"Пользователь {login} удалён из избранного")
            self.load_favorites_to_tree()
            self.status_var.set(f"Удалён из избранного: {login}")
            
            # Обновляем кнопку в результатах поиска
            for item in self.result_tree.get_children():
                values = self.result_tree.item(item, "values")
                if values[0] == login:
                    self.result_tree.set(item, "#3", "★")
                    break
        else:
            messagebox.showwarning("Предупреждение", f"Пользователь {login} не найден в избранном")
    
    def show_user_details(self, user_data: Dict):
        """Показать окно с детальной информацией о пользователе"""
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Профиль: {user_data.get('login', 'Unknown')}")
        details_window.geometry("500x550")
        details_window.resizable(False, False)
        
        # Основной фрейм
        main_frame = ttk.Frame(details_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Аватар (если есть)
        avatar_url = user_data.get('avatar_url', '')
        if avatar_url:
            ttk.Label(main_frame, text="🖼️ Аватар:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            # В tkinter сложно отобразить изображение из URL без доп библиотек
            # Поэтому просто показываем ссылку
            ttk.Label(main_frame, text=f"Ссылка на аватар", foreground="blue", cursor="hand2").pack(anchor=tk.W, pady=(0, 10))
        
        # Информация о пользователе
        ttk.Label(main_frame, text="📊 Информация:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        fields = [
            ("Логин:", user_data.get('login', 'N/A')),
            ("Имя:", user_data.get('name', 'Не указано')),
            ("Компания:", user_data.get('company', 'Не указана')),
            ("Блог:", user_data.get('blog', 'Не указан')),
            ("Локация:", user_data.get('location', 'Не указана')),
            ("Email:", user_data.get('email', 'Не указан')),
            ("Био:", user_data.get('bio', 'Не указано')),
            ("Публичные репозитории:", user_data.get('public_repos', 0)),
            ("Подписчики:", user_data.get('followers', 0)),
            ("Подписки:", user_data.get('following', 0)),
            ("Тип аккаунта:", user_data.get('type', 'User')),
            ("Создан:", user_data.get('created_at', 'N/A')[:10] if user_data.get('created_at') else 'N/A')
        ]
        
        for label, value in fields:
            row = ttk.Frame(info_frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=label, width=18, anchor=tk.W, font=("Arial", 9, "bold")).pack(side=tk.LEFT)
            ttk.Label(row, text=str(value), wraplength=300, anchor=tk.W).pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Кнопки действий
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        login = user_data.get('login', '')
        is_fav = self.favorites_manager.is_favorite(login)
        
        if not is_fav:
            ttk.Button(btn_frame, text="⭐ Добавить в избранное",
                      command=lambda: self.add_to_favorites(login, user_data)).pack(side=tk.LEFT, padx=2)
        else:
            ttk.Button(btn_frame, text="★ Удалить из избранного",
                      command=lambda: self.remove_from_favorites(login)).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="🌐 Открыть в браузере",
                  command=lambda: self._open_in_browser(user_data.get('html_url', f'https://github.com/{login}'))).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="Закрыть", command=details_window.destroy).pack(side=tk.RIGHT, padx=2)
    
    def _open_in_browser(self, url: str):
        """Открыть URL в браузере"""
        import webbrowser
        if url:
            webbrowser.open(url)
            self.status_var.set(f"Открыт профиль в браузере")
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()