import sqlite3
import os
import paramiko
import datetime
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.scrollview import MDScrollView
from kivy.metrics import dp
from kivy.uix.popup import Popup

class SQLTrackerApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"  # Dark mode for better UI
        self.conn = sqlite3.connect("database.db")  # Persistent database
        self.cursor = self.conn.cursor()
        self.create_tracking_table()

        self.goal = 10  # Default daily query goal
        self.today_date = datetime.date.today()

        layout = MDBoxLayout(orientation="vertical", padding=10, spacing=10)

        # SQL Input Field
        self.query_input = MDTextField(hint_text="Enter SQL Query Here", multiline=True, size_hint_y=None, height=100)
        layout.add_widget(self.query_input)

        # Buttons Layout
        button_layout = MDBoxLayout(size_hint_y=None, height=50, spacing=10)

        self.run_button = MDRaisedButton(text="Run Query", on_press=self.execute_query)
        self.create_table_button = MDRaisedButton(text="Create Sample Table", on_press=self.create_sample_table)
        self.show_tables_button = MDRaisedButton(text="Show Tables", on_press=self.show_tables)
        self.set_goal_button = MDRaisedButton(text="Set Goal", on_press=self.set_goal)
        self.progress_button = MDRaisedButton(text="View Progress", on_press=self.show_progress)

        button_layout.add_widget(self.run_button)
        button_layout.add_widget(self.create_table_button)
        button_layout.add_widget(self.show_tables_button)
        button_layout.add_widget(self.set_goal_button)
        button_layout.add_widget(self.progress_button)
        layout.add_widget(button_layout)

        # Progress Bar for Daily Goal
        self.progress_label = MDLabel(text="Daily Progress: 0%", halign="center", size_hint_y=None, height=30)
        self.progress_bar = MDProgressBar(value=0, max=100, size_hint_x=1)
        layout.add_widget(self.progress_label)
        layout.add_widget(self.progress_bar)

        # Table for Query Results
        self.scroll_view = MDScrollView()
        self.data_table = MDDataTable(
            size_hint=(1, 0.6),
            use_pagination=True,
            column_data=[("Column", dp(30))],  # Placeholder columns
            row_data=[("No data",)]
        )
        self.scroll_view.add_widget(self.data_table)
        layout.add_widget(self.scroll_view)

        return layout

    def create_tracking_table(self):
        """Creates a table to track SQL query executions."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                execution_date DATE
            );
        """)
        self.conn.commit()

    def execute_query(self, instance):
        query = self.query_input.text.strip()
        if not query:
            self.result_label.text = "⚠️ Please enter an SQL query."
            return

        try:
            self.cursor.execute(query)
            if query.lower().startswith("select"):
                results = self.cursor.fetchall()
                columns = [desc[0] for desc in self.cursor.description]
                self.data_table.column_data = [(col, dp(30)) for col in columns]
                self.data_table.row_data = results or [("No results",)]
                self.result_label.text = "✅ Query executed successfully."
            else:
                self.conn.commit()
                self.result_label.text = "✅ Query executed successfully."

            # Log query execution for tracking
            self.log_query(query)
            self.update_progress_bar()

        except Exception as e:
            self.result_label.text = f"❌ Error: {e}"

    def log_query(self, query):
        """Logs executed queries into the tracking table."""
        today = str(self.today_date)
        self.cursor.execute("INSERT INTO query_log (query, execution_date) VALUES (?, ?)", (query, today))
        self.conn.commit()

    def update_progress_bar(self):
        """Updates the progress bar based on queries executed today."""
        today = str(self.today_date)
        self.cursor.execute("SELECT COUNT(*) FROM query_log WHERE execution_date = ?", (today,))
        count = self.cursor.fetchone()[0]
        progress = (count / self.goal) * 100
        self.progress_bar.value = progress
        self.progress_label.text = f"Daily Progress: {int(progress)}%"

    def set_goal(self, instance):
        """Allows the user to set a daily query goal."""
        def set_goal_value(obj):
            self.goal = int(goal_input.text)
            goal_popup.dismiss()

        goal_layout = MDBoxLayout(orientation="vertical", padding=10, spacing=10)
        goal_input = MDTextField(hint_text="Enter your daily goal (e.g., 10)", size_hint_y=None, height=50)
        goal_button = MDRaisedButton(text="Set Goal", on_press=set_goal_value)

        goal_layout.add_widget(goal_input)
        goal_layout.add_widget(goal_button)

        goal_popup = Popup(title="Set Daily Goal", content=goal_layout, size_hint=(0.7, 0.4))
        goal_popup.open()

    def show_progress(self, instance):
        """Shows progress of total SQL queries executed."""
        self.cursor.execute("SELECT execution_date, COUNT(*) FROM query_log GROUP BY execution_date;")
        progress_data = self.cursor.fetchall()
        progress_text = "\n".join([f"{date}: {count} queries" for date, count in progress_data]) or "No data yet."

        self.show_popup("📊 Progress Report", progress_text)

    def show_tables(self, instance):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()
        self.show_popup("📂 Database Tables", ", ".join([table[0] for table in tables]) if tables else "No tables found.")

    def create_sample_table(self, instance):
        query = """CREATE TABLE IF NOT EXISTS students (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT,
                      age INTEGER,
                      grade TEXT
                   );"""
        self.cursor.execute(query)
        self.conn.commit()
        self.result_label.text = "✅ Sample table 'students' created."
        self.log_query("Created 'students' table")

    def show_popup(self, title, message):
        popup_layout = MDBoxLayout(orientation="vertical", padding=10, spacing=10)
        popup_label = MDLabel(text=message, halign="center")
        close_button = MDRaisedButton(text="Close", on_press=lambda x: popup.dismiss())

        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)

        popup = Popup(title=title, content=popup_layout, size_hint=(0.7, 0.4))
        popup.open()

    def send_log_to_server(self):
        """(Optional) Sends query logs to a remote server using Paramiko."""
        host, username, password = "your.server.com", "your_username", "your_password"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, password=password)
        
        sftp = ssh.open_sftp()
        sftp.put("database.db", "/remote/path/database.db")
        sftp.close()
        ssh.close()

if __name__ == "__main__":
    SQLTrackerApp().run()
