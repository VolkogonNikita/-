import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox


class DatabaseApp:
    def __init__(self, master, connection_params):
        self.master = master
        self.connection_params = connection_params
        self.master.title("База данных больницы")

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill='both')

        # Connect to the database
        self.conn = sqlite3.connect(**connection_params)
        self.cursor = self.conn.cursor()

        #self.create_tables()

        # Fetch table names
        self.table_names = self.get_table_names()

        # Create a tab for each table
        for table_name in self.table_names:
            frame = tk.Frame(self.notebook)
            self.notebook.add(frame, text=table_name)
            self.create_table_view(frame, table_name)

    def create_ables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Patient (
                                id INTEGER PRIMARY KEY, 
                                name TEXT, 
                                birth_date TEXT, 
                                gender TEXT, 
                                address TEXT, 
                                phone TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Doctor (
                                id INTEGER PRIMARY KEY,
                                name TEXT,
                                specialty TEXT,
                                phone TEXT)''')
        self.conn.commit()

    def get_table_names(self):
        # Fetch table names from the database
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = [row[0] for row in self.cursor.fetchall()]
        return table_names

    def create_table_view(self, frame, table_name):
        # Fetch column names
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in self.cursor.fetchall()]

        # Create a treeview widget
        tree = ttk.Treeview(frame, columns=columns, show='headings', selectmode='browse')
        tree.pack(expand=True, fill='both')

        # Add column headings
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor='center')

        # Populate treeview with data from the table
        self.populate_treeview(tree, table_name)

        # Add buttons for CRUD operations
        add_button = tk.Button(frame, text="Добавить", command=lambda: self.add_row(tree, table_name))
        add_button.pack(side=tk.LEFT, padx=10)

        delete_button = tk.Button(frame, text="Удалить", command=lambda: self.delete_row(tree, table_name))
        delete_button.pack(side=tk.LEFT, padx=10)

        edit_button = tk.Button(frame, text="Изменить", command=lambda: self.edit_row(tree, table_name))
        edit_button.pack(side=tk.LEFT, padx=10)

        report_button = tk.Button(frame, text="Создать отчет", command=lambda: self.generate_report(table_name))
        report_button.pack(side=tk.LEFT, padx=10)

        # Добавляем поле для поиска
        search_label = tk.Label(frame, text="Поиск:")
        search_label.pack(side=tk.LEFT, padx=5)

        search_entry = tk.Entry(frame)
        search_entry.pack(side=tk.LEFT, padx=5)

        search_button = tk.Button(frame, text="Найти",
                                  command=lambda: self.search(tree, table_name, search_entry.get()))
        search_button.pack(side=tk.LEFT, padx=5)

    def generate_report(self, table_name):
        try:
            # Получаем данные из таблицы
            self.cursor.execute(f"SELECT * FROM {table_name};")
            data = self.cursor.fetchall()

            # Получаем названия колонок
            self.cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [row[1] for row in self.cursor.fetchall()]

            # Создаем текстовый файл для отчета
            with open(f'{table_name}_report.txt', 'w', encoding='utf-8') as f:
                # Записываем заголовки
                f.write('\t'.join(columns) + '\n')
                # Записываем данные
                for row in data:
                    f.write('\t'.join(map(str, row)) + '\n')

            messagebox.showinfo("Успех", f"Отчет по таблице '{table_name}' успешно создан.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать отчет: {str(e)}")
    def populate_treeview(self, tree, table_name):
        # Fetch data from the table
        self.cursor.execute(f"SELECT * FROM {table_name};")
        data = self.cursor.fetchall()

        # Clear existing data in treeview
        tree.delete(*tree.get_children())

        # Insert data into treeview
        for row in data:
            tree.insert('', 'end', values=row)

    def add_row(self, tree, table_name):
        # Get column names
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in self.cursor.fetchall()]

        # Create a dialog for adding a new row
        add_dialog = tk.Toplevel(self.master)
        add_dialog.title("Добавить строку")

        # Entry widgets for each column
        entry_widgets = []
        for col in columns:
            label = tk.Label(add_dialog, text=col)
            label.grid(row=columns.index(col), column=0, padx=10, pady=5, sticky='e')
            entry = tk.Entry(add_dialog)
            entry.grid(row=columns.index(col), column=1, padx=10, pady=5, sticky='w')
            entry_widgets.append(entry)

        # Function to insert the new row into the table
        def insert_row():
            values = [entry.get() for entry in entry_widgets]
            placeholders = ', '.join(['?' for _ in values])
            query = f"INSERT INTO {table_name} VALUES ({placeholders});"
            self.cursor.execute(query, values)
            self.conn.commit()
            self.populate_treeview(tree, table_name)
            add_dialog.destroy()

        # Button to submit the new row
        submit_button = tk.Button(add_dialog, text="Подтвердить", command=insert_row)
        submit_button.grid(row=len(columns), columnspan=2, pady=10)

    def delete_row(self, tree, table_name):
        # Получаем выделенный элемент в treeview
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите строку для удаления.")
            return

        # Подтверждение удаления
        confirm = messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту строку?")
        if not confirm:
            return

        values = tree.item(selected_item)['values']

        # Получаем названия колонок
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in self.cursor.fetchall()]

        # Создаем условие WHERE по id
        where_clause = f"id = ?"
        query = f"DELETE FROM {table_name} WHERE {where_clause};"

        # Удаляем строку из таблицы
        self.cursor.execute(query, (values[0],))  # values[0] - это id
        self.conn.commit()

        self.populate_treeview(tree, table_name)

    def edit_row(self, tree, table_name):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите строку для изменения.")
            return

        values = tree.item(selected_item)['values']

        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in self.cursor.fetchall()]

        edit_dialog = tk.Toplevel(self.master)
        edit_dialog.title("Изменить строку")

        entry_widgets = []
        for idx, (col, value) in enumerate(zip(columns, values)):
            label = tk.Label(edit_dialog, text=col)
            label.grid(row=idx, column=0, padx=10, pady=5, sticky='e')
            entry = tk.Entry(edit_dialog)
            entry.insert(0, value)
            entry.grid(row=idx, column=1, padx=10, pady=5, sticky='w')
            entry_widgets.append(entry)

        def update_row():
            new_values = [entry.get() for entry in entry_widgets]
            set_clause = ', '.join([f"{column} = ?" for column in columns])

            # Используем id для точного обновления
            where_clause = f"id = ?"
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause};"
            self.cursor.execute(query, new_values + [values[0]])  # values[0] - это id
            self.conn.commit()
            self.populate_treeview(tree, table_name)
            edit_dialog.destroy()

        submit_button = tk.Button(edit_dialog, text="Подтвердить", command=update_row)
        submit_button.grid(row=len(columns), columnspan=2, pady=10)

    def search(self, tree, table_name, search_term):

        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in self.cursor.fetchall()]

        like_clauses = [f"{col} LIKE ?" for col in columns]
        where_clause = ' OR '.join(like_clauses)
        search_query = f"SELECT * FROM {table_name} WHERE {where_clause};"
        search_values = ['%' + search_term + '%' for _ in columns]

        self.cursor.execute(search_query, search_values)
        results = self.cursor.fetchall()

        tree.delete(*tree.get_children())

        for row in results:
            tree.insert('', 'end', values=row)


if __name__ == "__main__":
    connection_params = {"database": "hospital.db"}
    try:
        root = tk.Tk()
        app = DatabaseApp(root, connection_params)
        root.mainloop()
    except sqlite3.Error as err:
        print(f"Error: {err}")
