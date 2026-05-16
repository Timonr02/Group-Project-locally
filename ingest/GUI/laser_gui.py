import sys
import tkinter as tk
from tkinter import ttk
import os
import webbrowser

import PIL.Image, PIL.ImageTk

from Client.opcua_client import Laser
from Generate_Gcode.Generate_Gcode import Generate_Gcode
from Preview_Gcode.preview_gcode import GCodePreview

PATH = os.path.dirname(os.path.abspath(__file__)) + "/"

from asyncua.sync import Client, ua

URL = "opc.tcp://192.168.158.34:4840"

class Ur5:
    def __init__(self) -> None:
        self.ur = Client(URL, 50)
        self._is_connected = False
        self.namespace = "idk"

        try:
            self.ur.connect()
            self._is_connected = True
        except:
            pass

    def exit(self):
        try:
            if self._is_connected:
                self.ur.disconnect()
            self.ur.tloop.stop()
        except:
            pass

    def pick_from(self, modul_num: int = 0):
        try:
            node = self.ur.get_node("ns=2;s=pick_from_mod_1")
            return node.write_value(modul_num, ua.VariantType.Int32)
        except:
            return

    def place_to(self, modul_num: int = 0):
        try:
            node = self.ur.get_node("ns=2;s=place_to_mod_1")
            return node.write_value(modul_num, ua.VariantType.Int32)
        except:
            return

    def pick_one_card(self, modul_num: int = 0):
        try:
            node = self.ur.get_node("ns=2;s=pick_from_mod_5")
            return node.write_value(modul_num, ua.VariantType.Int32)
        except:
            return


class LaserGUI(ttk.Frame):

    def __init__(self, _):
        ttk.Frame.__init__(self)
        self.prev = GCodePreview()
        self.fontsize = 20
        self.tk.call("source", PATH + "azure.tcl")
        self.tk.call("set_theme", "dark")
        for index in [0, 1, 2]:
            self.columnconfigure(index=index, weight=1)
            self.rowconfigure(index=index, weight=1)

        self.laser = Laser()
        self.generater = Generate_Gcode()
        self.ur = Ur5()
        self.update_delay = 100
        self.connected = False
        self.old_list = []
        self.offset= [4, 86]

        self.postions = ["Front", "Back"]
        self.start_pos_var = tk.StringVar(value="Back")

        self.var_progress = tk.DoubleVar(value=0.0)

        self.tabs()
        self.frames()
        self.logo_widgets()
        self.control_widgets()
        self.status_widgets()
        self.move_widgets()
        self.list_widgets()
        self.generte_widgets()
        self.update_postion()
        # self.laser.reference()

        self.after(self.update_delay, self.update)

    def exit(self):
        self.laser.exit()
        self.ur.exit()

    def tabs(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.grid(
            row=0, column=1, padx=(10, 20), pady=(10, 20), sticky="nwewns", rowspan=3
        )

        self.tab_1 = ttk.Frame(self)
        self.tabs.add(self.tab_1, text="Control")
        self.tab_2 = ttk.Frame(self)
        self.tabs.add(self.tab_2, text="Generate Gcode")
        self.tab_4 = ttk.Frame(self)
        self.tabs.add(self.tab_4, text="NFC")

    def frames(self):
        self.logo_frame = tk.Frame(self)
        self.logo_frame.grid(row=0, column=0, padx=(20,10), pady=10, sticky="ew")

        self.status_frame = ttk.LabelFrame(self, text="Status", padding=(20, 10))
        self.status_frame.grid(row=1, column=0, padx=(20,10), pady=10, sticky="nwewns")

        self.info_frame = ttk.LabelFrame(self, text="About", padding=(20, 10))
        self.info_frame.grid(row=2, column=0, padx=(20,10), pady=(10,20), sticky="nwewns")

        self.control_frame = ttk.LabelFrame(
            self.tab_1, text="Control", padding=(20, 20), width=100
        )
        self.control_frame.grid(
            row=0,
            column=0,
            padx=(20, 10),
            pady=(20, 10),
            sticky="nwewns",
            rowspan=2,
        )

        self.move_frame = ttk.LabelFrame(self.control_frame, text="Move", padding=(0, 0))
        self.move_frame.grid(
            row=11, column=0, padx=(0, 0), pady=10, sticky="nwew", columnspan=2
        )

        self.run_gcode_frame = ttk.Frame(
            self.tab_1, padding=(20, 0)
        )
        self.run_gcode_frame.grid(
            row=0,
            column=1,
            padx=(0, 10),
            pady=(23, 10),
            sticky="nwewns",
            rowspan=1,
        )

        self.tree_frame = ttk.Frame(
            self.tab_1, padding=(20, 00)
        )
        self.tree_frame.grid(
            row=1,
            column=1,
            padx=(0, 10),
            pady=(5, 10),
            sticky="nwewns",
            rowspan=1,
        )

        self.generate_frame = ttk.LabelFrame(
            self.tab_2, text="Generate Gcode", padding=(20, 20)
        )

        self.generate_frame.grid(
            row=0, column=0, padx=(20, 10), pady=(20, 10), sticky="nwewns"
        )

        self.preview_frame = ttk.LabelFrame(
            self.tab_2, text="Preview", padding=(20, 20)
        )
        self.preview_frame.grid(
            row=0, column=1, padx=(20, 10), pady=(20, 10), sticky="nwewns"
        )

    def logo_widgets(self, img=PATH + "img/hsel_logo_dark.png"):
        about_msg = (
            "User Interface to control the Laser\nEngraver \n\t\t",
        )
        self.logo = tk.PhotoImage(file=img)
        self.logo_label = ttk.Label(self.logo_frame, image=self.logo)
        self.logo_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew", rowspan=3)

        self.laser_label = ttk.Label(
            self.info_frame,
            text="Laser Engraver",
            font=("-size", self.fontsize),
        )
        self.laser_label.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")

        self.about_label = ttk.Label(
            self.info_frame,
            text=about_msg[0],
            font=("-size", self.fontsize),
            width=30
        )
        self.about_label.grid(
            row=1, column=0, padx=5, pady=10, sticky="nsew", columnspan=2
        )
        self.doc_button = ttk.Button(
            self.info_frame,
            text="Documentation",
            command=lambda: webbrowser.open(
                PATH.replace("GUI/", "docs/_build/html/index.html")
            ),
        )
        self.doc_button.grid(row=2, column=0, padx=5, pady=0, sticky="nw")

    def status_widgets(self):
        self.connect_label = ttk.Label(
            self.status_frame,
            text="OPCUA-Server is not connected",
            font=("-size", self.fontsize),
            width=30,
            foreground="red"
        )
        self.connect_label.grid(
            row=1, column=0, padx=5, pady=10, sticky="ew", columnspan=2
        )

        self.laser_connect_label = ttk.Label(
            self.status_frame,
            text="Laser Engraver is not connected",
            font=("-size", self.fontsize),
            width=30,
            foreground="red"
        )
        self.laser_connect_label.grid(
            row=2, column=0, padx=5, pady=10, sticky="ew", columnspan=2
        )

        self.mcu_connect_label = ttk.Label(
            self.status_frame,
            text="MCU is not connected",
            font=("-size", self.fontsize),
            width=30,
            foreground="red"
        )
        self.mcu_connect_label.grid(
            row=3, column=0, padx=5, pady=10, sticky="ew", columnspan=2
        )

        self.is_running_label = ttk.Label(
            self.status_frame, text="Status:", font=("-size", self.fontsize)
        )
        self.is_running_label.grid(
            row=4, column=0, padx=5, pady=10, sticky="ew", columnspan=2
        )

        self.progress_label = ttk.Label(
            self.status_frame,
            text="Progress: ",
            font=("-size", self.fontsize),
            width=17,
        )
        self.progress_label.grid(
            row=6, column=0, padx=5, pady=10, sticky="ew", columnspan=1
        )
        self.progress_val_label = ttk.Label(
            self.status_frame,
            text=str(int(self.var_progress.get())) + "%",
            font=("-size", self.fontsize),
            width=1,
        )
        self.progress_val_label.grid(
            row=6, column=1, padx=(110, 0), pady=10, sticky="ew", columnspan=1
        )

        self.progress = ttk.Progressbar(
            self.status_frame, value=0, variable=self.var_progress, mode="determinate"
        )
        self.progress.grid(
            row=7, column=0, padx=(5, 5), pady=10, sticky="ew", columnspan=2
        )


    def control_widgets(self):
        self.theme = ["dark", "light"]
        self.theme_var = tk.StringVar()
        # self.enalbe_var = tk.BooleanVar(value=True)
        self.reference_var = tk.BooleanVar(value=False)
        self.pointer_var = tk.BooleanVar(value=False)
        self.fan_var = tk.BooleanVar(value=False)
        self.actuator_hight_var = tk.IntVar(value=135)
        self.actuator_push_var = tk.IntVar(value=135)

        self.connect_button = ttk.Button(
            self.control_frame, 
            text="Connect", 
            command=lambda: (
                self.laser.connect(),
                self.update_postion(),
            ),
        )
        self.connect_button.grid(
            row=0, column=0, padx=5, pady=10, sticky="ew", columnspan=2
        )

        self.pointer = ttk.Checkbutton(
            self.control_frame,
            text="Pointer",
            style="Toggle.TButton",
            variable=self.pointer_var,
            command=lambda: self.laser.pointer(self.pointer_var.get()),
        )
        self.pointer.grid(row=4, column=0, padx=5, pady=10, sticky="nsew", columnspan=2)

        self.pointer = ttk.Checkbutton(
            self.control_frame,
            text="Exhaust Fan",
            style="Toggle.TButton",
            variable=self.fan_var,
            command=lambda: self.laser.fan_control(self.fan_var.get()),
        )
        self.pointer.grid(row=6, column=0, padx=5, pady=10, sticky="nsew", columnspan=2)


        self.start_pos_label = ttk.Label(
            self.move_frame, text="Origin:", font=("-size", self.fontsize)
        )
        self.start_pos_label.grid(row=7, column=0, padx=5, pady=10)

        self.start_pos = ttk.OptionMenu(
            self.move_frame,
            self.start_pos_var,
            self.postions[1],
            *self.postions,
            command=lambda _: self.update_postion(),
            direction="below",
        )
        self.start_pos.grid(row=7, column=1, padx=25, pady=5, sticky="ew", columnspan=2)

        self.actuator_label = ttk.Label(
            self.control_frame,
            text="Servo Motors:",
            font=("-size", self.fontsize),
            width=1,
        )
        self.actuator_label.grid(row=8, column=0, padx=(5,0), pady=10, sticky="nsew", columnspan=2)

        self.actuator_hight_label = ttk.Label(
            self.control_frame,
            text="Hight",
            font=("-size", self.fontsize),
            width=1,
        )
        self.actuator_hight_label.grid(row=9, column=0, padx=(5,0), pady=10, sticky="nsew", columnspan=1)

        self.actuator_hight = ttk.Scale(
            self.control_frame,
            from_=0,
            to=270,
            length=250,
            variable=self.actuator_hight_var,
            command=lambda _: (
                self.actuator_hight_var.set(self.actuator_hight.get()),
                self.laser.move_actuator_hight(int(self.actuator_hight_var.get())),
            ),
        )
        self.actuator_hight.grid(row=9, column=1, padx=(0,5), pady=10, sticky="nsew", columnspan=1)

        self.actuator_push_label = ttk.Label(
            self.control_frame,
            text="Push ",
            font=("-size", self.fontsize),
            width=1,
        )
        self.actuator_push_label.grid(row=10, column=0, padx=(5,0), pady=10, sticky="nsew", columnspan=1)

        self.actuator_push = ttk.Scale(
            self.control_frame,
            from_=0,
            to=270,
            length=250,
            variable=self.actuator_push_var,
            command=lambda _: (
                self.actuator_push_var.set(self.actuator_push.get()),
                self.laser.move_actuator_push(270-int(self.actuator_push_var.get())),
            ),
        )
        self.actuator_push.grid(row=10, column=1, padx=(0,5), pady=10, sticky="nsew", columnspan=1)

        self.theme = ttk.OptionMenu(
            self.status_frame,
            self.theme_var,
            self.theme[0],
            *self.theme,
            command=lambda _: self.update_theme(),
            direction="above",
        )
        self.theme.grid(row=16, column=0, padx=5, pady=10, sticky="nsew", columnspan=1)
        self.close = ttk.Button(
            self.status_frame,
            text="close",
            command=lambda: self.quit(),
        )
        self.close.grid(row=16, column=1, padx=5, pady=10, sticky="nsew", columnspan=1)

    def move_widgets(self):
        self.steps = [1, 10, 20, 40, 60, 80, 100]
        self.step_var = tk.DoubleVar(value=10)
        button_width = 5

        ##########
        # ↖↙⬅
        self.lu = ttk.Button(
            self.move_frame,
            text="↖",
            width=button_width,
            command=lambda: self.laser.move_relativ(
                xval=-1 * self.step_var.get(), yval=self.step_var.get()
            ),
        )
        self.lu.grid(row=0, column=0, padx=25, pady=25)

        self.l = ttk.Button(
            self.move_frame,
            text="⬅",
            width=button_width,
            command=lambda: self.laser.move_relativ(xval=-1 * self.step_var.get()),
        )
        self.l.grid(row=1, column=0, padx=25, pady=5)

        self.ld = ttk.Button(
            self.move_frame,
            text="↙",
            width=button_width,
            command=lambda: self.laser.move_relativ(
                xval=-1 * self.step_var.get(), yval=-1 * self.step_var.get()
            ),
        )
        self.ld.grid(row=2, column=0, padx=25, pady=25)

        ##########
        # ↗↘➡
        self.ru = ttk.Button(
            self.move_frame,
            text="↗",
            width=button_width,
            command=lambda: self.laser.move_relativ(
                xval=1 * self.step_var.get(), yval=1 * self.step_var.get()
            ),
        )
        self.ru.grid(row=0, column=2, padx=25, pady=25)

        self.r = ttk.Button(
            self.move_frame,
            text="➡",
            width=button_width,
            command=lambda: self.laser.move_relativ(xval=1 * self.step_var.get()),
        )
        self.r.grid(row=1, column=2, padx=25, pady=5)

        self.rd = ttk.Button(
            self.move_frame,
            text="↘",
            width=button_width,
            command=lambda: self.laser.move_relativ(
                xval=1 * self.step_var.get(), yval=-1 * self.step_var.get()
            ),
        )
        self.rd.grid(row=2, column=2, padx=25, pady=25)
        ##########
        # ⬆⬇
        self.u = ttk.Button(
            self.move_frame,
            text="⬆",
            width=button_width,
            command=lambda: self.laser.move_relativ(yval=1 * self.step_var.get()),
        )
        self.u.grid(row=0, column=1, padx=0, pady=25)

        self.h = ttk.Button(
            self.move_frame,
            text=" ",
            width=button_width,
            command=lambda: (
                self.reference_var.set(True),
                self.laser.reference(),
            ),
        )
        self.h.grid(row=1, column=1, padx=0, pady=5)

        self.d = ttk.Button(
            self.move_frame,
            text="⬇",
            width=button_width,
            command=lambda: self.laser.move_relativ(yval=-1 * self.step_var.get()),
        )
        self.d.grid(row=2, column=1, padx=0, pady=25)

        self.step_label = ttk.Label(
            self.move_frame, text="Steps:", font=("-size", self.fontsize)
        )
        self.step_label.grid(row=3, column=0, padx=5, pady=10)

        self.step = ttk.OptionMenu(
            self.move_frame,
            self.step_var,
            self.steps[6],
            *self.steps,
            direction="below",
        )
        self.step.grid(row=3, column=1, padx=25, pady=10, sticky="ew", columnspan=2)

    def list_widgets(self):
        self.file_prev_var = tk.BooleanVar(value=False)
        self.file_img_var = PIL.ImageTk.PhotoImage(self.prev.generate_preview(""))

        self.file_prev_img = tk.Canvas(self.run_gcode_frame, width=680, height=450)
        self.file_prev_img.grid(
            row=0,
            column=0,
            padx=5,
            pady=0,
            sticky="nsew",
            columnspan=3
        )

        self.file_prev_img.create_image(0, 0, image=self.file_img_var, anchor=tk.NW)

        self.load_button = ttk.Button(
            self.run_gcode_frame,
            text="Run File",
            command=lambda: self.load_pragram(),
        )
        self.load_button.grid(
            row=1,
            column=0,
            padx=5,
            pady=(0,5),
            sticky="nsew",
        )

        self.stop = ttk.Button(
            self.run_gcode_frame,
            text="Stop",
            command=lambda: (self.laser.stop()),
        )
        self.stop.grid(
            row=1,
            column=1,
            padx=5,
            pady=(0,5),
            sticky="nsew",
        )

        self.preview_button = ttk.Checkbutton(
            self.run_gcode_frame,
            text="Preview",
            style = "Toggle.TButton",
            variable= self.file_prev_var,
            command=lambda : self.prev_file(),
        )

        self.preview_button.grid(
            row=1,
            column=2,
            padx=5,
            pady=(0,5),
            sticky="nsew",
        )

        ttk.Style().configure('TreeStyle.Treeview', rowheight=34)

        self.scrollbar = ttk.Scrollbar(self.tree_frame)
        self.scrollbar.pack(side="right", fill="y")

        self.treeview = ttk.Treeview(
            self.tree_frame,
            selectmode="browse",
            yscrollcommand=self.scrollbar.set,
            height=7,
            padding=(20, 0),
            style="TreeStyle.Treeview",
        )
        self.treeview.pack(expand=True, fill="both")

        self.treeview.bind("<ButtonRelease-1>", self.update_selected_program())
        self.treeview.heading("#0", text="Available Programs", anchor="center")
        self.treeview.tag_configure("mylist", font=("Segoe Ui", self.fontsize))

        self.scrollbar.config(command=self.treeview.yview)

    def generte_widgets(self):
        self.gen_variant_list = ["hs", "blank", "hs-simple","zdin", "icps2025"]
        self.gen_variant_var = tk.StringVar()
        self.gen_material_list = ["wood", "PVC_White", "PVC_Blue", "PVC_Black"]
        self.gen_material_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.division_var = tk.StringVar()
        self.job_title_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.fax_var = tk.StringVar()
        self.mail_var = tk.StringVar()
        self.generate_var = tk.BooleanVar(value=False)
        self.prev_img_var = PIL.ImageTk.PhotoImage(self.prev.generate_preview(""))

        self.gen_variant = ttk.OptionMenu(
            self.generate_frame,
            self.gen_variant_var,
            self.gen_variant_list[0],
            *self.gen_variant_list,
            direction="below",
        )
        self.gen_variant.grid(
            row=0, column=0, padx=5, pady=10, sticky="nsew", columnspan=2
        )

        self.gen_material = ttk.OptionMenu(
            self.generate_frame,
            self.gen_material_var,
            self.gen_material_list[0],
            *self.gen_material_list,
            direction="below",
        )
        self.gen_material.grid(
            row=1, column=0, padx=5, pady=10, sticky="nsew", columnspan=2
        )

        self.title_label = ttk.Label(self.generate_frame, text="Title")
        self.title_label.grid(
            row=2, column=0, padx=5, pady=0, sticky="nw", columnspan=1
        )
        self.title_entry = ttk.Entry(self.generate_frame, textvariable=self.title_var)
        self.title_entry.grid(
            row=3, column=0, padx=5, pady=0, sticky="nw", columnspan=1
        )

        self.name_label = ttk.Label(self.generate_frame, text="Name")
        self.name_label.grid(row=4, column=0, padx=5, pady=0, sticky="nw", columnspan=1)
        self.name_entry = ttk.Entry(self.generate_frame, textvariable=self.name_var)
        self.name_entry.grid(row=5, column=0, padx=5, pady=0, sticky="nw", columnspan=1)

        self.division_label = ttk.Label(self.generate_frame, text="Division")
        self.division_label.grid(
            row=6, column=0, padx=5, pady=0, sticky="nw", columnspan=1
        )
        self.division_entry = ttk.Entry(
            self.generate_frame, textvariable=self.division_var
        )
        self.division_entry.grid(
            row=7, column=0, padx=5, pady=0, sticky="nw", columnspan=1
        )

        self.job_title_label = ttk.Label(self.generate_frame, text="Job Title")
        self.job_title_label.grid(
            row=8, column=0, padx=5, pady=0, sticky="nw", columnspan=1
        )
        self.job_title_entry = ttk.Entry(
            self.generate_frame, textvariable=self.job_title_var
        )
        self.job_title_entry.grid(
            row=9, column=0, padx=5, pady=0, sticky="nw", columnspan=1
        )

        self.phone_label = ttk.Label(self.generate_frame, text="Phone")
        self.phone_label.grid(
            row=10, column=0, padx=5, pady=0, sticky="nw", columnspan=1
        )
        self.phone_entry = ttk.Entry(self.generate_frame, textvariable=self.phone_var)
        self.phone_entry.grid(
            row=11, column=0, padx=5, pady=0, sticky="nw", columnspan=1
        )

        self.fax_label = ttk.Label(self.generate_frame, text="Fax")
        self.fax_label.grid(row=12, column=0, padx=5, pady=0, sticky="nw", columnspan=1)
        self.fax_entry = ttk.Entry(self.generate_frame, textvariable=self.fax_var)
        self.fax_entry.grid(row=13, column=0, padx=5, pady=0, sticky="nw", columnspan=1)

        self.mail_label = ttk.Label(self.generate_frame, text="E-Mail")
        self.mail_label.grid(
            row=14, column=0, padx=5, pady=0, sticky="nw", columnspan=1
        )
        self.mail_entry = ttk.Entry(self.generate_frame, textvariable=self.mail_var)
        self.mail_entry.grid(
            row=15, column=0, padx=5, pady=0, sticky="nw", columnspan=1
        )
        self.prev_img = tk.Canvas(self.preview_frame, width=680, height=450)
        self.prev_img.grid(row=0, column=0, padx=10, pady=10, rowspan=1, columnspan=2)
        self.prev_img.create_image(0, 0, image=self.prev_img_var, anchor=tk.NW)

        self.generate_button = ttk.Checkbutton(
            self.preview_frame,
            text="Generate",
            style = "Toggle.TButton",
            variable= self.generate_var,
            command=lambda: self.update_previwe_img(),
        )
        self.generate_button.grid(row=2, column=0, padx=5, pady=10, sticky="nsew", columnspan=2)

        self.card_in = ttk.Button(
            self.preview_frame,
            text="Card in",
            command=lambda: self.laser.push_card_in(),
        )
        self.card_in.grid(row=3, column=0, padx=5, pady=10, sticky="nsew")

        self.card_out = ttk.Button(
            self.preview_frame,
            text="Card Out",
            command=lambda: self.laser.push_card_out(),
        )
        self.card_out.grid(row=3, column=1, padx=5, pady=10, sticky="nsew")

        self.generate_run = ttk.Button(
            self.preview_frame,
            text="Run",
            command=lambda: self.laser.run_generated_gcode(),
        )
        self.generate_run.grid(row=4, column=0, padx=5, pady=10, sticky="nsew")

        self.generate_stop = ttk.Button(
            self.preview_frame,
            text="Stop",
            command=lambda: self.laser.stop(),
        )
        self.generate_stop.grid(row=4, column=1, padx=5, pady=10, sticky="nsew")

        start_pos_label = ttk.Label(
            self.preview_frame, text="Origin:", font=("-size", self.fontsize),width=1,
        )
        start_pos_label.grid(row=1, column=0, padx=5, pady=10, sticky="nsew", columnspan=1)

        start_pos = ttk.OptionMenu(
            self.preview_frame,
            self.start_pos_var,
            self.postions[1],
            *self.postions,
            command=lambda _: self.update_postion(),
            direction="below",
        )
        start_pos.grid(row=1, column=1, padx=5, pady=10, sticky="nsew", columnspan=1)

        self.robot_place = ttk.Button(
            self.preview_frame,
            text="Request Cards",
            command=lambda: self.ur.place_to(5)
        )
        self.robot_place.grid(row=5, column=0, padx=5, pady=10, sticky="nsew", columnspan=1)

        self.robot_place = ttk.Button(
            self.preview_frame,
            text="Pick Card",
            command=lambda: self.ur.pick_one_card(5)
        )
        self.robot_place.grid(row=5, column=1, padx=5, pady=10, sticky="nsew", columnspan=1)



    def connect(self):
        if not self.laser.is_connected():
            self.laser = Laser()

    def prev_file(self):
        if not self.selected_program:
            self.file_prev_var.set(False),
            return

        print(self.selected_program[0])
        self.file_prev_var.set(True)
        code = self.prev.generate_preview(self.laser.get_gcode(self.selected_program[0]))
        self.file_img_var = PIL.ImageTk.PhotoImage(code)
        self.file_prev_img.create_image(
            0, 0, 
            image=self.file_img_var,
            anchor=tk.NW),
        self.file_prev_var.set(False),

    def load_pragram(self):
        if self.selected_program:
            self.laser.send_command("$H\nG90 G0 X"+ str(self.offset[0]) + "Y" + str(self.offset[1]) +"S0F10000")
            while self.laser.is_running():
                pass
            self.laser.run_file(self.selected_program[0])

    def update_selected_program(self):
        self.selected_program = self.treeview.item(self.treeview.focus())["values"]
        if self.selected_program:
            self.treeview.heading("#0", anchor="center",
                text= self.selected_program[0]
            )

    def update_list(self):
        list = self.laser.list_files()
        if not list:
            return

        if list == self.old_list:
            return
        self.old_list = list
        list = sorted(list)
        self.treeview.delete(*self.treeview.get_children())
        for item in list:
            self.treeview.insert(
                parent="", index="end", text=item, values=item, tags=("mylist")
            )

    def update_theme(self):
        theme = self.theme_var.get()
        self.tk.call("set_theme", theme)
        if theme == "dark":
            self.logo_widgets(PATH + "img/hsel_logo_dark.png")
        else:
            self.logo_widgets(PATH + "img/hsel_logo_light.png")

    def update_postion(self):
        postion = self.start_pos_var.get()
        self.tk.call("set_theme", postion)
        if postion == "Front":
            self.offset = [4, 86]
        else:
            self.offset = [66, 308]
        self.laser.set_card_offset(self.offset[0], self.offset[1])
        self.prev.set_offset(self.offset[0], self.offset[1])
        self.generater.set_offset(self.offset[0], self.offset[1])

    def update_previwe_img(self):
        self.generate_var.set(True)
        self.laser.generate_gcode(
            self.gen_variant_var.get(),
            self.title_var.get(),
            self.name_var.get(),
            self.division_var.get(),
            self.job_title_var.get(),
            self.phone_var.get(),
            self.fax_var.get(),
            self.mail_var.get(),
        )
        temp = self.gen_variant_var.get()
        if temp == "icps2025Blank":
            temp = "icps2025"
        self.generater.generate_gcode( {
            "variant": temp,
            "title": self.title_var.get(),
            "name": self.name_var.get(),
            "division": self.division_var.get(),
            "job_title": self.job_title_var.get(),
            "phone": self.phone_var.get(),
            "fax": self.fax_var.get(),
            "mail": self.mail_var.get(),
            }
        )
        gcode = self.generater.get_gcode()
        self.prev_img_var = PIL.ImageTk.PhotoImage(self.prev.generate_preview(gcode))
        self.prev_img.create_image(0, 0, image=self.prev_img_var, anchor=tk.NW)
        self.generate_var.set(False)

    def update(self):
        self.photo = PIL.ImageTk.PhotoImage(file=PATH + "img/hsel_icon.png")
        self.update_selected_program()

        if self.laser.is_connected():
            self.connect_label.config(text="OPCUA-Server is connected         ", foreground="green")
            if self.laser.is_laser_connected():
                self.connected = True
                self.laser_connect_label.config(text="Laser is connected", foreground="green")
            else:
                self.laser_connect_label.config(text="Laser is not connected", foreground="red")

            if self.laser.is_mcu_connected():
                self.mcu_connect_label.config(text="MCU is connected", foreground="green")
            else:
                self.mcu_connect_label.config(text="MCU is not connected", foreground="red")

            if self.laser.is_running():
                self.is_running_label.config(text="Status: Laser is Moving")
                self.var_progress.set(self.laser.get_progress())
                self.progress_val_label.config(text=str(int(self.var_progress.get())) + "%")
            else:
                self.is_running_label.config(text="Status: Laser is Not Moving")
                self.var_progress.set(0.0)
                self.progress_val_label.config(text="0%")
            self.update_list()
        else:
            self.connected = False
            self.connect_label.config(text="OPCUA-Server is not connected      ", foreground="red")
            self.laser_connect_label.config(text="Laser is not connected", foreground="red")
            self.mcu_connect_label.config(text="MCU is not connected", foreground="red")

        self.after(self.update_delay, self.update)

def main():
    root = tk.Tk()
    root.title("HS Emden/Leer: Laser Engraver ")
    root.attributes("-zoomed", True)
    root.attributes("-fullscreen", True)
    root.iconphoto(False, tk.PhotoImage(file=PATH + "img/hsel_icon.png"))
    app = LaserGUI(root)
    app.pack(fill="both", expand=True)

    root.update()
    app.mainloop()
    sys.exit(app.exit())
