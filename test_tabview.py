import customtkinter as ctk

app = ctk.CTk()
tabview = ctk.CTkTabview(app)
tabview.pack(padx=20, pady=20)
tabview.add("Tab 1")
tabview.add("Tab 2")

def change_lang():
    for name in tabview._name_list:
        btn = tabview._segmented_button._buttons_dict[name]
        btn.configure(text=name + " translated")

ctk.CTkButton(app, text="Change", command=change_lang).pack()
app.mainloop()
