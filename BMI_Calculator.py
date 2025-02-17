from datetime import date
from tkinter import *

root = Tk()
root.geometry("450x400")
root.title("BMI Calculator")
root.config(bg="#b278ff")

Label(root, text="BMI Calculator", font=("Arial", 20), bg="#73fa8c").grid(row=0, column=1, columnspan=2)

Label(root, text="", bg="#b278ff").grid(row=1, column=0)

type_conv = StringVar()
Radiobutton(root, text="Kgs and Centimetres", variable=type_conv, value="K&C", bg="#93adf5").grid(row=2, column=1)
Radiobutton(root, text="Pounds and Inches", variable=type_conv, value="P&I", bg="#93adf5").grid(row=3, column=1)

Label(root, text="", bg="#b278ff").grid(row=4, column=0)

weight = IntVar()
height = IntVar()

def scale():
    type = type_conv.get()
    
    for widget in root.grid_slaves():
        if int(widget.grid_info()["row"]) in [6, 7]:
            widget.destroy()

    if type == "K&C":
        Label(root, text="Weight in Kgs", bg="#93adf5", anchor="w").grid(row=6, column=0)
        Scale(root, from_=20, to=200, variable=weight, orient="horizontal", length=200, bg="#73fa8c").grid(row=6, column=1)

        Label(root, text="Height in Cms", bg="#93adf5", anchor="w").grid(row=7, column=0)
        Scale(root, from_=50, to=250, variable=height, orient="horizontal", length=200, bg="#73fa8c").grid(row=7, column=1)
    
    elif type == "P&I":
        Label(root, text="Weight in Lbs", bg="#93adf5", anchor="w").grid(row=6, column=0)
        Scale(root, from_=40, to=400, variable=weight, orient="horizontal", length=200, bg="#73fa8c").grid(row=6, column=1)
        
        Label(root, text="Height in Inches", bg="#93adf5", anchor="w").grid(row=7, column=0)
        Scale(root, from_=21, to=110, variable=height, orient="horizontal", length=200, bg="#73fa8c").grid(row=7, column=1)

Button(root, text="Show Scale", command=scale, bg="#93adf5").grid(row=5, column=1)

BMI = StringVar()

def calculate():
    w = weight.get()
    h = height.get()
    type = type_conv.get()

    if type == "K&C":
        h = h / 100  
        bmi_value = w / (h ** 2)
    
    elif type == "P&I":
        h = h * 0.0254  
        w = w * 0.453592  
        bmi_value = w / (h ** 2)

    BMI.set(f"{bmi_value:.2f}")

    for widget in root.grid_slaves():
        if int(widget.grid_info()["row"]) in [10, 11]:
            widget.destroy()

    Label(root, text="Your BMI is:", bg="#73fa8c").grid(row=10, column=0)
    Label(root, textvariable=BMI, bg="#93adf5", font=("Arial", 12, "bold")).grid(row=10, column=1)

    if bmi_value < 18.5:
        Label(root, text="Underweight", bg="red", fg="white").grid(row=11, column=1)
    elif bmi_value > 24.9:
        Label(root, text="Overweight", bg="red", fg="white").grid(row=11, column=1)
    else:
        Label(root, text="Healthy", bg="green", fg="white").grid(row=11, column=1)

Button(root, text="Calculate", command=calculate, bg="#73fa8c").grid(row=8, column=1)

Label(root, text="", bg="#b278ff").grid(row=9, column=0)

def save():
    curr_date = str(date.today())
    w = weight.get()
    h = height.get()
    bmi = BMI.get()

    type = type_conv.get()
    if type == "P&I":
        h = h * 0.0254  
        w = w * 0.453592  
    
    record = f"{curr_date} --> Height: {h:.2f}m, Weight: {w:.2f}kg, BMI: {bmi}\n"

    with open("BMI.txt", "a") as file:
        file.write(record)

def light():
    root.config(bg="white")
def dark():
    root.config(bg="black")
def red():
    root.config(bg="red")

menubar = Menu(root)
root.config(menu=menubar)

filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="Save", command=save)

submenu = Menu(filemenu, tearoff=0)
submenu.add_command(label="Light Mode", command=light)
submenu.add_command(label="Dark Mode", command=dark)
submenu.add_command(label="Red Mode", command=red)

filemenu.add_cascade(label="Change Theme", menu=submenu)
menubar.add_cascade(label="File", menu=filemenu)

root.mainloop()
