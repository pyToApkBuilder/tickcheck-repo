import flet as ft
from tradingview_ta import TA_Handler, Interval
import time
import os
import json

with open(os.path.join(os.path.dirname(__file__), "assets", "stocks.json"), "r") as f:
    STOCKS = json.load(f)


# Define your interval map
INTERVAL_MAP = {
    "1m": Interval.INTERVAL_1_MINUTE,
    "5m": Interval.INTERVAL_5_MINUTES,
    "15m": Interval.INTERVAL_15_MINUTES,
    "1h": Interval.INTERVAL_1_HOUR,
    "2h": Interval.INTERVAL_2_HOURS,
    "1d": Interval.INTERVAL_1_DAY,
}

def ptc_diff(num1, num2):
  try:
    return ((num1 - num2)/num2)*100
  except:
      return 0

def getname(sym):
    try:
        handler = TA_Handler(
            symbol=sym,
            screener="INDIA",
            exchange="NSE",
            interval=Interval.INTERVAL_1_DAY,
        )
        data = handler.get_indicators(['description',"close","RSI"])
        recom = handler.get_analysis().summary["RECOMMENDATION"]
        return [data,recom]
    except:
        return None


def main(page: ft.Page):
    page.title = "Stock Filter App"

    recommendation_dropdown = ft.Dropdown(
        label="Recommendation",
        options=[
            ft.dropdown.Option("STRONG_BUY"),
            ft.dropdown.Option("BUY"),
            ft.dropdown.Option("SELL"),
            ft.dropdown.Option("STRONG_SELL"),
        ],
        value="STRONG_BUY",
    )

    interval_dropdown = ft.Dropdown(
        label="Interval",
        options=[ft.dropdown.Option(k) for k in INTERVAL_MAP.keys()],
        value="1d"  # default interval
    )

    filter_state = ft.Text(color=ft.Colors.GREEN_200)
    results_column = ft.ListView(expand=True, spacing=10, auto_scroll=False, padding=20)
    store_stocks_column = ft.ListView(expand=True, spacing=10, auto_scroll=False, padding=20)

    # Save and load data from client storage
    def save_data(data):
        page.client_storage.set("stocks", data)

    def load_data():
        value = page.client_storage.get("stocks")
        return value if value else []

    # Function to delete a stock
    def delete_stock(e):
        data = e.control.data  # data = [symbol, price]
        stocksList = load_data()
        stocksList = [item for item in stocksList if item != data]
        save_data(stocksList)
        screenupdate()

    # Function to refresh saved stocks tab
    def screenupdate():
        store_stocks_column.controls.clear()
        stockList = load_data()

        if len(stockList) == 0:
            store_stocks_column.controls.append(ft.Text("No Saved STOCKS!"))
            page.update()
            return

        for item in stockList:
            interval_value = item[3]
            try:
                handler = TA_Handler(
                    symbol=item[0],
                    exchange="NSE",
                    screener="INDIA",
                    interval=interval_value,
                )
                analysis = handler.get_analysis()
                current_price = analysis.indicators.get("close", "N/A")
                rsi = analysis.indicators.get("RSI", "N/A")

                change = ptc_diff(current_price,item[1]) if item[2] in ["BUY","STRONG_BUY","LONG"] else ptc_diff(item[1],current_price)
                direction = "LONG" if item[2] in ["BUY","STRONG_BUY","LONG"] else "SHORT"
                stock_card = ft.Container(
                    content=ft.Row(
                        [
                            ft.Column([
                                ft.Text(f"{item[4]} ({item[0]})"),
                                ft.Text(f"Saved Price: {item[1]} | Current Price: {current_price}"),
                                ft.Text(f"Change: {change:.2f}%",size=12),
                                ft.Text(f"Direction: {direction} for Interval: {item[3]}",size=12),
                                ft.Text(f"RSI: {rsi:.2f}",size=12),
                            ], expand=True),
                            ft.PopupMenuButton(
                                items=[
                                    ft.PopupMenuItem(
                                        icon=ft.Icons.BAR_CHART,
                                        text="Goto Chart",
                                        on_click=lambda _: page.launch_url(f"https://www.tradingview.com/chart/?symbol=NSE%3A{item[0]}")),
                                    ft.PopupMenuItem(
                                        icon=ft.Icons.SHOW_CHART,
                                        text="Google finance",
                                        on_click=lambda _: page.launch_url(f"https://www.google.com/finance/quote/{item[0]}:NSE")),
                                    ft.PopupMenuItem(
                                        icon=ft.Icons.DELETE,
                                        text="DELETE",
                                        data=item,
                                        on_click=delete_stock
                                    )
                                ]
                            )
                        ],
                        alignment="spaceBetween"
                    ),
                    padding=ft.padding.only(0,10,0,10)
                )
                store_stocks_column.controls.append(stock_card)
                page.update()

            except Exception as e:
                print(e)

    # Function to add stock to storage
    def addstock(e):
        data = e.control.data
        stocksList = load_data()
        if data[0] not in [item[0] for item in stocksList]:
            stocksList.insert(0, data)
            filter_state.value = f"{data[0]} added."
        else:
            filter_state.value = f"{data[0]} already added."

        page.update()
        save_data(stocksList)
        screenupdate()

    def lunch_chart(e):
        symbol = e.control.data
        page.launch_url(f"https://www.google.com/finance/quote/{symbol}:NSE")

    # Function to filter stocks
    def filter_stocks(e):
        results_column.controls.clear()

        selected_recommendation = recommendation_dropdown.value
        selected_interval = interval_dropdown.value

        if not selected_recommendation or not selected_interval:
            page.snack_bar = ft.SnackBar(ft.Text("Please select both dropdown options"))
            page.snack_bar.open = True
            page.update()
            return
        filter_state.value = "Started.."
        page.update()
        interval_value = INTERVAL_MAP[selected_interval]

        for stock in STOCKS:

            try:
                handler = TA_Handler(
                    symbol=stock,
                    exchange="NSE",
                    screener="INDIA",
                    interval=interval_value,
                )
                analysis = handler.get_analysis()
                longname = getname(stock)[0]["description"]
                recommendation = analysis.summary.get("RECOMMENDATION", "")
                close_price = analysis.indicators.get("close", "N/A")
                change = analysis.indicators.get("change", "N/A")
                rsi = analysis.indicators.get("RSI", "N/A")
                filter_state.value = f"{stock} : {recommendation}"

                if recommendation == selected_recommendation:
                    results_column.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.TextButton(f"Symbol: {stock}", on_click=addstock, data=[stock, close_price, recommendation, interval_value, longname]),
                                    ft.Text(longname),
                                    ft.Text(f"Recommendation: {recommendation}"),
                                    ft.Text(f"Close Price: {close_price:.2f}({change:.2f}%)"),
                                    ft.Text(f"RSI: {rsi:.2f}"),
                                    ft.ElevatedButton(
                                        icon=ft.Icons.SHOW_CHART,
                                        text="Google finance",
                                        data=stock,
                                        on_click=lunch_chart,
                                        )
                                ]),
                                padding=10
                            )
                        )
                    )
                page.update()


            except Exception as ex:
                filter_state.value = f"No data for {stock}"
                page.update()
        filter_state.value = f"Done! {len(results_column.controls)} stocks found."
        page.update()


        if not results_column.controls:
            results_column.controls.append(ft.Text("No stocks matched your filter."))
            page.update()

    # Button to trigger stock filtering
    filter_button = ft.ElevatedButton(
        icon=ft.Icons.SAVED_SEARCH,
        text="Filter Stocks",
        on_click=filter_stocks,
    )

    search_stock_input = ft.TextField(hint_text="Enter Stock Symbol",multiline=False,width=200)
    search_info = ft.Text()
    search_direction_input = ft.Dropdown(
        label="Direction",
        options=[ft.DropdownOption("LONG"),ft.DropdownOption("SHORT")],
        value="LONG"
    )

    def Searchclick(e):
        sym = search_stock_input.value.strip().upper()
        data = getname(sym=sym)
        if not data:
            return
        search_info.value = f"{data[0]['description']} ({sym}) \nprice: {data[0]['close']} \nrsi: {data[0]['RSI']} \nRecommendation: {data[1]}" if data else "No data found"
        page.open(dlg_add_data)
        page.update()

    def add_data(e):
        sym = search_stock_input.value.strip().upper()
        data = getname(sym=sym)
        if not data:
            return
        price = data[0]["close"]
        direc = search_direction_input.value
        longname = data[0]["description"]
        stockdata = [sym,price,direc,Interval.INTERVAL_1_DAY,longname]
        stocksList = load_data()
        stocksList.insert(0,stockdata)
        search_stock_input.value = ""
        search_stock_input.autofocus = False
        page.close(dlg_add_data)
        page.update()
        save_data(stocksList)
        screenupdate()


    dlg_add_data = ft.BottomSheet(
        open=False,
        content=ft.Container(
            padding=20,
            content=ft.Column([
                search_info,
                search_direction_input,
                ft.Row([
                    ft.TextButton("Add",on_click=add_data),
                    ft.TextButton("Cancel",on_click=lambda _: page.close(dlg_add_data)),
                ],alignment=ft.MainAxisAlignment.CENTER)

        ],horizontal_alignment=ft.CrossAxisAlignment.CENTER),))


    # Tabs
    t = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="Saved Stocks",
                content=ft.Container(expand = True,
                    content=ft.Column(expand=True,controls=[
                        ft.Row([
                            search_stock_input,
                            ft.ElevatedButton(
                                icon=ft.Icons.SEARCH,
                                text="Search",
                                on_click= Searchclick
                            ),
                            ft.PopupMenuButton(items=[
                                ft.PopupMenuItem(
                                    content=ft.ElevatedButton(
                                        icon=ft.Icons.CLEAR,
                                        text="CLEAR_ALL",
                                        on_click=lambda _: [page.client_storage.clear(),screenupdate()]
                                    ),
                                )]
                            )
                        ],alignment=ft.MainAxisAlignment.END),
                        store_stocks_column,
                    ]),padding=10
                ),
            ),
            ft.Tab(
                text="Filter Stocks",
                icon=ft.Icons.FILTER,
                content=ft.Container(expand=True,content=ft.Column(expand=True, controls=[
                    ft.Column([ft.Row([recommendation_dropdown, interval_dropdown],alignment=ft.MainAxisAlignment.CENTER), filter_button],horizontal_alignment=ft.CrossAxisAlignment.CENTER,),
                    filter_state,
                    results_column
                ]),padding=10),
            ),
        ],
        expand=1,
    )

    page.add(ft.Container(expand=True, content=t,padding=ft.padding.only(0,20,0,10)))

    # Load saved stocks initially
    def autoupdate():
        while True:
            screenupdate()
            time.sleep(60)


    page.run_task(autoupdate())

ft.app(target=main)
