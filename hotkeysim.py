import pywinauto

app = pywinauto.application.Application().connect(process=9504)
w = app.top_window()

w.TypeKeys("{F17}")