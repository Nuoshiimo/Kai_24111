import queue
import threading
import tkinter as tk
from tkinter import ttk

import requests

API_URL = "https://open.er-api.com/v6/latest/USD"


class CurrencyConverter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Конвертер валют")
        self.geometry("520x360")
        self.minsize(480, 340)

        # Состояние приложения
        self.rates = {}          # {"EUR": 0.92, "USD": 1.0, ...}
        self.base = "USD"
        self.loading = False
        self.events = queue.Queue()   # единственная связь поток -> GUI

        # Переменные виджетов
        self.amount_var = tk.StringVar(value="100")
        self.from_var = tk.StringVar(value="USD")
        self.to_var = tk.StringVar(value="EUR")

        self._build_ui()

        # Реакция на действия пользователя
        self.amount_var.trace_add("write", lambda *_: self.recalculate())
        self.from_combo.bind("<<ComboboxSelected>>", lambda _: self.recalculate())
        self.to_combo.bind("<<ComboboxSelected>>", lambda _: self.recalculate())

        self.after(100, self._poll_events)
        self.load_rates()        # первый запрос при старте

    # ---------------- Интерфейс ----------------
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        frame = ttk.Frame(self, padding=20)
        frame.grid(row=0, column=0, sticky="nsew")
        for col in range(3):
            frame.columnconfigure(col, weight=1)

        ttk.Label(frame, text="Сумма").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.amount_var, font=("Segoe UI", 12)) \
            .grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)

        ttk.Label(frame, text="Из").grid(row=1, column=0, sticky="w", pady=4)
        self.from_combo = ttk.Combobox(frame, textvariable=self.from_var,
                                      state="readonly", font=("Segoe UI", 11))
        self.from_combo.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="В").grid(row=2, column=0, sticky="w", pady=4)
        self.to_combo = ttk.Combobox(frame, textvariable=self.to_var,
                                    state="readonly", font=("Segoe UI", 11))
        self.to_combo.grid(row=2, column=1, sticky="ew", pady=4)

        self.swap_button = ttk.Button(frame, text="⇄ Поменять", command=self.swap)
        self.swap_button.grid(row=1, column=2, sticky="ew", padx=(8, 0))

        self.refresh_button = ttk.Button(frame, text="⟳ Обновить курсы",
                                        command=self.load_rates)
        self.refresh_button.grid(row=2, column=2, sticky="ew", padx=(8, 0))

        self.result_label = ttk.Label(frame, text="—", foreground="#1a7f37",
                                      font=("Segoe UI", 18, "bold"))
        self.result_label.grid(row=3, column=0, columnspan=3, pady=20)

        self.status_label = ttk.Label(frame, text="Загрузка курсов…",
                                      foreground="#666666", wraplength=460)
        self.status_label.grid(row=4, column=0, columnspan=3, sticky="w")

        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(10, 0))

    # ---------------- Логика пересчёта ----------------
    def recalculate(self, *_):
        if not self.rates:
            self.result_label.config(text="—")
            return

        try:
            amount = float(self.amount_var.get().replace(",", "."))
        except ValueError:
            self.result_label.config(text="Введите число")
            return

        src, dst = self.from_var.get(), self.to_var.get()
        if src not in self.rates or dst not in self.rates:
            self.result_label.config(text="Выберите валюты")
            return

        # Все курсы даны относительно USD:
        # сумма -> USD -> целевая валюта
        in_usd = amount / self.rates[src]
        result = in_usd * self.rates[dst]

        self.result_label.config(
            text=f"{amount:,.2f} {src}  →  {result:,.2f} {dst}".replace(",", " ")
        )

    def swap(self):
        self.from_var.set(self.to_var.get())
        self.to_var.set(self.from_var.get())
        self.recalculate()

    # ---------------- Сеть: рабочий поток ----------------
    def load_rates(self):
        if self.loading:
            return
        self.loading = True
        self.refresh_button.config(state="disabled")
        self.status_label.config(text="Загружаю курсы…")
        self.progress.start(12)

        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        """Работает в фоновом потоке. НИКАКИХ обращений к виджетам здесь!"""
        try:
            response = requests.get(API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("result") != "success" or not data.get("rates"):
                raise ValueError("API вернул некорректные данные")

            self.events.put(("ok", data))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    # ---------------- Приём результатов в GUI-потоке ----------------
    def _poll_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "ok":
                    self._apply_rates(payload)
                else:
                    self.status_label.config(
                        text=f"Ошибка загрузки: {payload}. Попробуйте ещё раз."
                    )
                    self._finish_loading()
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _apply_rates(self, data):
        self.rates = data["rates"]
        self.base = data.get("base_code", "USD")

        codes = sorted(set(self.rates) | {"USD"})
        self.from_combo["values"] = codes
        self.to_combo["values"] = codes

        # Сохраняем выбор, если он всё ещё доступен
        if self.from_var.get() not in codes:
            self.from_var.set("USD")
        if self.to_var.get() not in codes:
            self.to_var.set("EUR" if "EUR" in codes else "USD")

        self.status_label.config(text=f"Курсы от {data.get('date', '?')} · база {self.base}")
        self._finish_loading()
        self.recalculate()

    def _finish_loading(self):
        self.loading = False
        self.progress.stop()
        self.refresh_button.config(state="normal")


if __name__ == "__main__":
    CurrencyConverter().mainloop()