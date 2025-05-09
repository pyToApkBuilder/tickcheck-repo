import flet as ft
from tradingview_ta import TA_Handler, Interval
import pytz
import time
from datetime import datetime

def get_time():
    india_tz = pytz.timezone('Asia/Kolkata')
    return datetime.now(india_tz).strftime("%Y-%m-%d (%H:%M)")

def ptc_diff(num1, num2):
    try:
        return ((num1 - num2) / num2) * 100
    except:
        return 0

def getdata(sym, exc="NSE", screen="INDIA"):
    try:
        handler = TA_Handler(
            symbol=sym.strip(),
            screener=screen.strip(),
            exchange=exc.strip(),
            interval=Interval.INTERVAL_1_DAY,
        )
        data = handler.get_indicators(['description', "close", "RSI","RSI[1]"])
        return data, exc
    except Exception:
        return None, None

def main(page: ft.Page):
    page.title = "TickCheck"

    def save_data(data):
        page.client_storage.set("stocklist", data)

    def load_data():
        value = page.client_storage.get("stocklist")
        return value if value else []


    def exit(e):
        data = e.control.data
        stocksList = load_data()
        stocksList = [item for item in stocksList if item != data]
        save_data(stocksList)
        screenupdate()
        page.open(ft.SnackBar(ft.Text(f"{data[0][0]} Exited! ",color=ft.Colors.RED)))

    def screenupdate():
        stockslist = load_data()
        results_column.controls.clear()
        if not stockslist:
            results_column.controls.append(ft.Text("No stocks matched your filter."))
            page.update()
            return
        for symlist in stockslist:
            data, exc = getdata(*symlist[0]) if len(symlist[0]) > 1 else getdata(symlist[0][0])
            if data is None:
                continue
            direction = symlist[2]
            entry = symlist[1]
            price = data["close"]
            name = data["description"]
            rsi = data["RSI"]
            rsi1 = data["RSI[1]"]
            change = ptc_diff(price, entry) if direction == "LONG" else ptc_diff(entry, price)
            results_column.controls.insert(0, ft.Container(
                margin=5,
                padding = 10,
                alignment=ft.alignment.center,
                content=ft.Row([
                    ft.Column([
                        ft.Text(value=symlist[3], size=12),
                        ft.Text(value=f"{name}", size=20),
                        ft.Text(f'Entry: {entry} | Price: {price}'),
                        ft.Text(f"RSI: {rsi:.2f} | RSI[1]: {rsi1:.2f}"),
                        ft.Text(value=f"{direction} change: {change:.2f} %",
                                color=ft.Colors.RED if change < 0 else ft.Colors.GREEN)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.PopupMenuButton(items=[
                        ft.PopupMenuItem(
                            text="Google Finance",
                            icon=ft.Icons.BAR_CHART,
                            on_click=lambda _, s=symlist[0][0]: page.launch_url(
                                f"https://www.google.com/finance/quote/{s}:{exc}")
                        ),
                        ft.PopupMenuItem(
                            text="Exit",
                            icon=ft.Icons.EXIT_TO_APP,
                            data=symlist,
                            on_click=exit
                        )
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ))
        page.update()

    def submit(e):
        if sym_input.value == "":
            return
        symlist = sym_input.value.strip().upper().split("/")
        data, exc = getdata(*symlist) if len(symlist) > 1 else getdata(symlist[0])
        if data is not None:
            info.color = ft.Colors.GREEN
            info.value = f"{data['description']} ({exc}) | Price: {data['close']} | RSI: {data['RSI']:.1f} | RSI[1]: {data['RSI[1]']:.1f}"
        else:
            info.color = ft.Colors.RED
            info.value = "No data avalable!"
            sym_input.value = ""
        page.update()


    def entry(e):
        direction = e.control.data
        symlist = sym_input.value.strip().upper().split("/")
        data, exc = getdata(*symlist) if len(symlist) > 1 else getdata(symlist[0])
        if data is not None:
            stocklist = load_data()
            if symlist not in [item[0] for item in stocklist]:
                stocklist.append([symlist, data["close"], direction, get_time()])
                save_data(stocklist)
                page.open(ft.SnackBar(ft.Text(f"{symlist[0]} Added!",color=ft.Colors.GREEN)))
                screenupdate()
            else:
                page.open(ft.SnackBar(ft.Text(f"{symlist[0]} already exists!")))
                page.update()
        else:
            page.open(ft.SnackBar(ft.Text("Invalid Input!",color=ft.Colors.RED)))
            page.update()
        sym_input.value = ""
        info.value = ""
        sym_input.autofocus = False
        page.update()

    sym_input = ft.TextField(
        label="Stock symbol (e.g. symbol/exchange/screener)...",
        expand=True,
        autofocus=False,
        border_width=0,
        focused_border_width=0,
        on_submit=submit
    )
    info = ft.Text("")
    results_column = ft.ListView(expand=True, spacing=10, auto_scroll=False, padding=5)



    clear_all_button = ft.PopupMenuItem(
        text="Exit All",
        icon=ft.Icons.CLEAR,
        on_click=lambda _: [page.client_storage.clear(), screenupdate()]
    )
    refresh_button = ft.PopupMenuItem(
        text="Refresh",
        icon=ft.Icons.REFRESH,
        on_click=lambda _: screenupdate()
    )

    page.add(ft.Container(
        expand=True,
        padding=ft.padding.only(top=30),
        content=ft.Column([
            ft.Row([sym_input]),
            info,
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.PopupMenuButton(items=[refresh_button,clear_all_button,]),
                ft.ElevatedButton(
                    icon=ft.Icons.ADD,
                    text="LONG",
                    expand=True,
                    on_click=entry,
                    data="LONG",
                    bgcolor=ft.Colors.GREEN_400,
                    color=ft.Colors.WHITE,
                    icon_color=ft.Colors.BLACK
                ),
                ft.ElevatedButton(
                    icon=ft.Icons.REMOVE,
                    text="SHORT",
                    expand=True,
                    on_click=entry,
                    data="SHORT",
                    bgcolor=ft.Colors.RED_400,
                    color=ft.Colors.WHITE,
                    icon_color=ft.Colors.BLACK
                ),
            ]),
            results_column,
        ])
    ))

    def autoupdate():
        while True:
            screenupdate()
            time.sleep(60)


    page.run_task(autoupdate())
ft.app(target=main)
