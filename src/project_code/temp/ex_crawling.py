import tkinter as tk
from selenium import webdriver 
from selenium.webdriver.common.by import By
import tkinter.messagebox as msg
from datetime import datetime

win = tk.Tk()
win.geometry("500x500")
win.option_add("*font","맑은고딕 15")
win.title("Test Window")

lblKeyword = tk.Label(win, text="Keyword")
lblKeyword.pack()

def on_enter_key(event):
    btnSearch.invoke()
entKeyword = tk.Entry(win, width=20)
entKeyword.pack()
entKeyword.focus()
entKeyword.bind("<Return>", on_enter_key)

def btn_search_clicked():
    keyword = entKeyword.get()
    driver = webdriver.Chrome()
    driver.get(f"https://www.coupang.com/np/search?q={keyword}")

    driver. implicitly_wait (10)

    results = driver. find_elements(By.CLASS_NAME, "descriptions-inner")
    for rank, r in enumerate(results,1) :
        if rank > 10 :
            break
        try :
            name = r.find_element (By.CLASS_NAME, "name")
            price = r.find_element (By.CLASS_NAME, "price")
            print(f" {rank}위 {name.text} {price.text}")
            lb.insert(tk.END, f" {rank}위 {name.text} {price.text}")
        except :
            print("skip")
    driver.quit()


btnSearch = tk.Button(win, text="쿠팡 검색")
btnSearch.config(command=btn_search_clicked)
btnSearch.pack()

lb = tk.Listbox(win, width=50,height=20)
lb.pack()

def btn_save_clicked():
    now = datetime.now()
    file_name = entKeyword.get() + "_" + now.strftime("%y%m%d_%H%M")
    with open(f"src/project/project5/data/{file_name}.txt","w",encoding="utf-8") as f:
        for info in lb.get(0,tk.END):
            f.write(info + "\n")
    msg.showinfo("저장","파일 저장 완료")

btnSave = tk.Button(win, text="저장")
btnSave.config(command=btn_save_clicked)
btnSave.pack()

win.mainloop()