from tkinter import *
from tkinter import ttk, filedialog
from tkinter import messagebox
from functools import partial
from tkinterdnd2 import DND_FILES, TkinterDnD

from pyotp import TOTP
import threading
import time

import requests
import os
import json
import sys

import path_to_tree
import crypto

# part to setup working directory on the executable path
if getattr(sys, "frozen", False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.getcwd()

os.chdir(application_path)

LARGE_FONT = ("Verdana", 12)
SERVER_URL = "https://filelocker.valenwe.fr/BACKEND/server.php"
# SERVER_URL = "http://localhost/mastercamp/BACKEND/server.php"
global id_user
id_user = -1

# php session
global session
session = requests.Session()

# user information
global user_info
user_info = {}

# all widgets to destroy
global widgets_list
widgets_list = []

# different permissions possibilities
permissions = ["Read only", "Read and write", "Administrator"]

# wipe out all widgets that remains between frames (stored in the widgets list)


def destroy_widget(widgets):
    for widget in widgets:
        widget.destroy()
    return []


def permission_to_str(id_perm):
    return permissions[int(id_perm) - 1]


def str_to_permission(permission):
    return permissions.index(permission) + 1


def is_owner(current_username, group):
    for user in group["users"]:
        if user["name"] == current_username:
            return group["owner"]["id"] == user["id"]


def is_admin(current_username, id_group):
    group = user_info["groups"][id_group]
    if is_owner(current_username, group):
        return True
    else:
        for user in group["users"]:
            if user["name"] == current_username:
                return int(user["id_permission"]) == 3


def can_write(current_username, id_group):
    group = user_info["groups"][id_group]
    if is_owner(current_username, group):
        return True
    else:
        for user in group["users"]:
            if user["name"] == current_username:
                return int(user["id_permission"]) >= 2


def error_message(error):
    try:
        messagebox.showerror(
            "Error " + error.split(" ~~~ ")[0], error.split(" ~~~ ")[1])
    except:
        messagebox.showerror(
            "Error", error)

def byte_to_str(byte_value):
    byte_value = int(byte_value)
    prefix = "B"
    if len(str(byte_value)) >= 10:
        prefix = "GB"
        byte_value /= 10 ** 9
    elif len(str(byte_value)) >= 7:
        prefix = "MB"
        byte_value /= 10 ** 6
    elif len(str(byte_value)) >= 4:
        prefix = "KB"
        byte_value /= 10 ** 3

    return str(round(byte_value, 2)) + " " + prefix

# handle switch between windows


class App(Tk):
    def __init__(self, *args, **kwargs):
        # necessary to allow drag and drop
        TkinterDnD.Tk.__init__(self, *args, **kwargs)
        self.geometry("1350x600")
        self.title("FileLocker")

        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (HomePage, LoginPage, CreateGroup, GroupPage, GroupList, UserPage, AddFriend, FriendsPage, UnlockKey, GroupUsers):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LoginPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

        try:
            menubar = frame.menubar(self)
            self.configure(menu=menubar)
        except:
            pass

    def get_frame(self, cont):
        return self.frames[cont]


class LoginPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent, bg="#71d2f0")
        Label(self, text="Login", font=LARGE_FONT).pack(pady=10, padx=10)

        logoImage = PhotoImage(file="assets/imgs/logo_empty.png")

        labelphoto = Label(self, image=logoImage, borderwidth=0)
        labelphoto.image = logoImage
        labelphoto.pack(padx=10, pady=10)

        Label(self, text="Filelocker", font=(
            LARGE_FONT, 22), bg="#71d2f0").pack(padx=10)

        # username label and text entry box
        username_label = Label(self, text="Username", bg="#71d2f0", font=18)
        username_label.pack(padx=10, pady=(5, 0))

        username = StringVar()

        username_entry = Entry(
            self, textvariable=username, width=30, bg="#cdf4ff")
        username_entry.pack(padx=10, pady=(3, 0))

        # password label and password entry box
        password_label = Label(self, text="Password", bg="#71d2f0", font=18)
        password_label.pack(padx=10, pady=(10, 0))

        password = StringVar()

        password_entry = Entry(self, textvariable=password,
                               show='*', width=30, bg="#cdf4ff")
        password_entry.pack(padx=10, pady=(3, 0))

        # totp code
        a2f_label = Label(self, text="A2F Code", bg="#71d2f0", font=18)
        a2f_label.pack(padx=10, pady=(10, 0))

        a2f = StringVar()

        a2f_entry = Entry(self, textvariable=a2f, width=30, bg="#cdf4ff")
        a2f_entry.pack(padx=10, pady=(3, 10))

        # login button
        self.validateLogin = partial(
            self.validateLogin, username, password, a2f)
        photoLogin = PhotoImage(file="assets/imgs/icons8-connexion-30.png")
        submit_button = Button(self, text="Login", command=self.validateLogin, image=photoLogin, compound=LEFT,
                               relief="flat", bg="#71d2f0", highlightcolor="#71d2f0")
        submit_button.image = photoLogin
        submit_button.pack(side=TOP)

    def validateLogin(self, username_inp, password_inp, a2f_inp, e=None):
        username = username_inp.get()
        password = password_inp.get()
        a2f = a2f_inp.get()

        username_inp.set("")
        password_inp.set("")
        a2f_inp.set("")

        # print(username, password, a2f)

        if len(username) > 0 and len(password) > 0 and len(a2f) > 0:
            try:
                ask_key = 1
                key_path = os.getcwd() + "/keys/" + username + ".pem"
                if not os.path.exists(os.path.dirname(key_path)):
                    os.makedirs(os.path.dirname(key_path))

                # if we already retrieved the private key, we check if it's ciphered
                if os.path.exists(key_path):
                    if crypto.key_is_ciphered(key_path):
                        ask_key = 0
                    else:
                        os.remove(key_path)

                global session
                data = {"log_user": 1, "log_username": username,
                        "log_password": password, "log_otp_code": a2f,
                        "ask_key": ask_key}
                resp = session.post(
                    SERVER_URL, data)

                # print(resp.text)
                content = resp.text

                if (not ask_key and len(content.split()) == 1) or ask_key and len(content.split()) == 3:
                    # we save the ciphered private key
                    if (ask_key):
                        raw_data = content.split(" ~~~ ")
                        content = raw_data[0]
                        key_content = raw_data[1]

                        with open(key_path, "w") as f:
                            f.write(key_content)

                    global id_user
                    id_user = int(content.split()[0])

                    username_inp.set("")
                    password_inp.set("")

                    if (not ask_key):
                        app.show_frame(HomePage)
                        app.get_frame(HomePage).fetchInformation()
                    else:
                        app.show_frame(UnlockKey)
                        app.get_frame(UnlockKey).username = username
                else:
                    error_message(resp.text)

            except:
                # print(traceback.format_exc())
                error_message("Server unreachable")


class UnlockKey(Frame):
    def __init__(self, parent, controller):
        self.controller = controller
        Frame.__init__(self, parent, bg="#71d2f0")
        label = Label(self, text="Unlock account", font=LARGE_FONT)
        label.pack(pady=10, padx=10)

        self.username = None

        Label(self, text="In order to use for the first time this account, you have to enter the passphrase of your account").pack()

        Label(self, text="Passphrase").pack()
        passphrase = StringVar()
        Entry(self, textvariable=passphrase, bg="#cdf4ff").pack()

        self.unlock_key = partial(self.unlock_key, passphrase)
        Button(self, text="Unlock", command=self.unlock_key).pack()

    def unlock_key(self, passphrase):
        passphrase_inp = passphrase.get()
        passphrase.set("")

        if len(passphrase_inp) == 0:
            return

        passphrase_inp = "".join(passphrase_inp.split(" "))

        try:
            key_path = os.getcwd() + "/keys/" + self.username + ".pem"

            with open(key_path, "r") as f:
                cipher_content = f.read()

            content = crypto.decrypt_AES_ECB(passphrase_inp, cipher_content)

            if crypto.key_is_ciphered(content, False):
                # remove weird characters at the end
                #print(content.split("END RSA PUBLIC KEY-----"))
                #content = content.split("END RSA PUBLIC KEY-----")[0] + "END RSA PUBLIC KEY-----"
                with open(key_path, "w", newline='') as f:
                    f.write(content)

                app.show_frame(HomePage)
                app.get_frame(HomePage).fetchInformation()
            else:
                error_message("Wrong passphrase!")
        except:
            # print(traceback.format_exc())
            error_message("Wrong passphrase!")


class HomePage(Frame):
    def __init__(self, parent, controller):
        self.controller = controller
        Frame.__init__(self, parent, bg="#71d2f0")
        label = Label(self, text="Filelocker", font=(
            LARGE_FONT, 22), bg="#71d2f0")
        label.pack(pady=30, padx=30)

        self.name = Label(self, text="Welcome, ", font=(
            LARGE_FONT, 20), bg="#71d2f0")
        self.name.pack(pady=30, padx=30)

        # access to file
        filePhoto = PhotoImage(file="assets/imgs/icons8-fichier-30.png")
        buttonFile = Button(self, text="Files", command=self.enter_group_list, image=filePhoto,
                            compound=LEFT, width=115, height=25)
        buttonFile.image = filePhoto
        buttonFile.pack(padx=10, pady=(0, 20))

        # create group button
        groupPhoto = PhotoImage(
            file="./assets/imgs/icons8-groupe-premier-plan-sélectionné-32.png")
        buttonGroup = Button(self, text="Create group", image=groupPhoto, command=self.create_group,
                             compound=LEFT, width=115, height=25)
        buttonGroup.image = groupPhoto
        buttonGroup.pack(padx=10, pady=(0, 20))

        # enter friend list button
        friendPhoto = PhotoImage(
            file="assets/imgs/icons8-ajouter-un-groupe-d'utilisateurs-homme-homme-24.png")
        buttonFriend = Button(self, text="Friends", command=self.enter_friends, image=friendPhoto,
                              compound=LEFT, width=115, height=25)
        buttonFriend.image = friendPhoto
        buttonFriend.pack(padx=10, pady=(0, 20))

        # refresh button
        refreshPhoto = PhotoImage(file="assets/imgs/icons8-rafraîchir-30.png")
        buttonRefresh = Button(self, text="Refresh", command=self.refresh, image=refreshPhoto,
                               compound=LEFT, width=115, height=25)
        buttonRefresh.image = refreshPhoto
        buttonRefresh.pack(padx=10, pady=(0, 20))

        # log out button
        logOutPhoto = PhotoImage(file="assets/imgs/icons8-log-out-32.png")
        buttonLogOut = Button(self, text="Disconnect", image=logOutPhoto, command=self.logout,
                              compound=LEFT, width=115, height=25)
        buttonLogOut.image = logOutPhoto
        buttonLogOut.pack(padx=10, pady=(0, 20))

        # exit button
        exitPhoto = PhotoImage(file="assets/imgs/icons8-macos-fermer-30.png")
        buttonExit = Button(self, text="Exit", command=self.exit, image=exitPhoto,
                            compound=LEFT, width=115, height=25)
        buttonExit.image = exitPhoto
        buttonExit.pack(padx=10, pady=(0, 20))

    def fetchInformation(self):
        global widgets_list
        widgets_list = destroy_widget(widgets_list)

        data = {"fetch_information": 1}
        global session
        resp = session.post(SERVER_URL, data)
        # print(resp.text)

        global user_info
        user_info = resp.json()

        # print(user_info)
        self.name.config(text="Welcome, " + user_info["username"])

    def logout(self):
        data = {"log_out": 1}
        global session
        resp = session.post(SERVER_URL, data)
        # print(resp.text)
        app.show_frame(LoginPage)

        global widgets_list
        widgets_list = destroy_widget(widgets_list)

    def exit(self):
        data = {"log_out": 1}
        global session
        resp = session.post(SERVER_URL, data)
        app.quit()

    def create_group(self):
        app.show_frame(CreateGroup)

    def enter_group_list(self):
        app.show_frame(GroupList)
        app.get_frame(GroupList).refresh_informations()

    def enter_friends(self):
        app.show_frame(FriendsPage)
        app.get_frame(FriendsPage).refresh_informations()

    def refresh(self):
        self.fetchInformation()


class AddFriend(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent, bg="#71d2f0")
        label = Label(self, text="Filelocker", font=(
            LARGE_FONT, 22), bg="#71d2f0")
        label.pack(pady=(30, 15), padx=30)

        Label(self, text="Add friend", font=LARGE_FONT,
              bg="#71d2f0").pack(pady=(0, 5), padx=10)

        self.personal_code_label = Label(
            self, text="Your code: ", font=LARGE_FONT, bg="#71d2f0")
        self.personal_code_label.pack(pady=(5, 5), padx=10)

        self.log_refresh = Label(self, text="Refresh in 0", bg="#71d2f0")
        self.log_refresh.pack()

        self.personal_totp = None
        self._thread = False

        otp_code = StringVar()
        friend_username = StringVar()

        Label(self, text="Friend username", bg="#71d2f0").pack()
        Entry(self, textvariable=friend_username, bg="#cdf4ff").pack()

        Label(self, text="Friend code", bg="#71d2f0").pack()
        Entry(self, textvariable=otp_code, bg="#cdf4ff").pack()

        self.friend_request = partial(
            self.friend_request, friend_username, otp_code)
        Button(self, text="Validate", command=self.friend_request, bg="#cdf4ff",
               relief="flat", highlightcolor="#71d2f0").pack(pady=(5, 5))

        # back button
        self.back = partial(self.back, friend_username, otp_code)
        backPhoto = PhotoImage(file="assets/imgs/icons8-arriere-32.png")
        buttonBack = Button(self, text="Back", command=self.back, image=backPhoto,
                            compound=LEFT, width=75, height=25,
                            relief="flat", bg="#71d2f0", highlightcolor="#71d2f0")
        buttonBack.image = backPhoto
        buttonBack.pack(pady=(30, 0))

    def refresh_informations(self):
        self._thread = True
        self.personal_totp = TOTP(user_info["friendrequest_code"])
        self.personal_code_label.config(
            text="Your code: " + self.personal_totp.now())

        refresher = threading.Thread(target=self.refresh_totp, daemon=True)
        refresher.start()

    def refresh_totp(self):
        sec = 15
        while self._thread:
            if sec <= 0:
                self.personal_code_label.config(
                    text="Your code: " + self.personal_totp.now())
                sec = 15
            self.log_refresh.config(text="Refresh in " + str(sec) + "s")
            time.sleep(1)
            sec -= 1

    def back(self, friend_username, otp_code, e=None):
        friend_username.set("")
        otp_code.set("")
        self._thread = False
        app.show_frame(FriendsPage)
        app.get_frame(HomePage).fetchInformation()
        app.get_frame(FriendsPage).refresh_informations()

    def friend_request(self, friend_username_inp, otp_code_inp):
        friend_username = friend_username_inp.get()
        otp_code = otp_code_inp.get()

        friend_username_inp.set("")
        otp_code_inp.set("")

        if len(friend_username) > 0 and len(otp_code) > 0:
            data = {"add_friend": 1, "friend_name": friend_username,
                    "friend_code": otp_code}
            resp = session.post(SERVER_URL, data)

            if len(resp.text) > 0:
                # print(resp.text)
                error_message(resp.text)
            else:
                self.back()


class FriendsPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent, bg="#71d2f0")
        label = Label(self, text="Filelocker", font=(
            LARGE_FONT, 22), bg="#71d2f0")
        label.pack(pady=(30, 15), padx=30)

        Label(self, text="Friend list", font=LARGE_FONT, bg="#71d2f0").pack()

        # back button
        backPhoto = PhotoImage(file="assets/imgs/icons8-arriere-32.png")
        buttonBack = Button(self, text="Back", command=self.back, image=backPhoto,
                            compound=LEFT, width=75, height=25,
                            relief="flat", bg="#71d2f0", highlightcolor="#71d2f0")
        buttonBack.image = backPhoto
        buttonBack.pack()

        # add friend button
        addFriendPhoto = PhotoImage(
            file="assets/imgs/icons8-ajouter-un-groupe-d'utilisateurs-homme-homme-24.png")
        buttonAdd = Button(self, text="Add friend", command=self.enter_add_friend, image=addFriendPhoto,
                           compound=LEFT, width=100, height=25,
                           relief="flat", bg="#71d2f0", highlightcolor="#71d2f0")
        buttonAdd.image = addFriendPhoto
        buttonAdd.pack(pady=(0, 5), padx=10)

        scrollY = Scrollbar(self, orient='vertical')
        scrollY.pack(fill='y', side='right')

        self.friendList = Listbox(
            self, yscrollcommand=scrollY.set, bg="#cdf4ff")
        self.friendList.pack(fill="both", expand=1, side='top')
        scrollY.configure(command=self.friendList.yview)

        self.friendList.bind("<Double-1>", self.enter_friend)
        self.friendList.bind("<Return>", self.enter_friend)
        self.friendList.bind("<ButtonRelease-3>", self.rightClicked)

        self.rightClickFriend = Menu(self, tearoff=0)
        self.rightClickFriend.add_command(
            label="Delete", command=self.delete_friend)

    def back(self):
        app.show_frame(HomePage)

    def enter_add_friend(self):
        app.show_frame(AddFriend)
        app.get_frame(AddFriend).refresh_informations()

    def refresh_informations(self):
        self.friendList.delete(0, END)
        for friend in user_info["friends"]:
            self.friendList.insert(END, friend["name"])

    def enter_friend(self, e=None):
        cur = self.friendList.curselection()
        try:
            friend_name = self.friendList.get(cur)
            for friend in user_info["friends"]:
                if friend["name"] == friend_name:
                    app.show_frame(UserPage)
                    app.get_frame(UserPage).set_back_target(FriendsPage)
                    app.get_frame(UserPage).refresh_informations(friend)
        except IndexError:
            pass
        except NameError:
            pass

    def delete_friend(self, e=None):
        cur = self.friendList.curselection()
        ans = messagebox.askyesno("Delete!", "Do you really want to delete?")
        if ans:
            data = {"remove_friend": 1,
                    "friend_name": self.friendList.get(cur)}
            resp = session.post(SERVER_URL, data)
            # print(resp.text)

        app.get_frame(HomePage).fetchInformation()
        self.refresh_informations()

    def rightClicked(self, e):
        try:
            rowid = self.friendList.nearest(e.y)
            self.friendList.selection_set(rowid)

            global x_root, y_root
            x_root = e.x_root
            y_root = e.y_root

            cur = self.friendList.curselection()
            if len(self.friendList.get(cur)) > 0:
                self.rightClickFriend.tk_popup(x=e.x_root, y=e.y_root)

        finally:
            self.rightClickFriend.grab_release()


class CreateGroup(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent, bg="#71d2f0")
        label = Label(self, text="Filelocker", font=(
            LARGE_FONT, 22), bg="#71d2f0")
        label.pack(pady=30, padx=30)

        Label(self, text="Create group", font=LARGE_FONT,
              bg="#71d2f0").pack(pady=10, padx=10)

        # name input text
        name = StringVar()

        # username label and text entry box
        Label(self, text="Name", bg="#71d2f0").pack()
        Entry(self, textvariable=name).pack(pady=(0, 10), padx=10)

        # login button
        createPhoto = PhotoImage(file="assets/imgs/icons8-plus-32.png")
        self.creation_request = partial(
            self.creation_request, name, controller)
        buttonCreate = Button(self, text="Create", command=self.creation_request, image=createPhoto,
                              compound=LEFT, width=75, height=25,
                              relief="flat", bg="#71d2f0", highlightcolor="#71d2f0")
        buttonCreate.image = createPhoto
        buttonCreate.pack(pady=(0, 75), padx=10)

        # back button
        backPhoto = PhotoImage(file="assets/imgs/icons8-arriere-32.png")
        self.back = partial(
            self.back, name)
        buttonBack = Button(self, text="Back", command=self.back, image=backPhoto,
                            compound=LEFT, width=75, height=25,
                            relief="flat", bg="#71d2f0", highlightcolor="#71d2f0")
        buttonBack.image = backPhoto
        buttonBack.pack(pady=(0, 10), padx=10)

    def creation_request(self, name_inp, controller):
        name = name_inp.get()
        name_inp.set("")
        if len(name) > 0:
            data = {"create_group": 1, "group_name": name}
            global session
            resp = session.post(SERVER_URL, data)

            if len(resp.text) > 0:
                # print(resp.text)
                error_message(resp.text)

            controller.show_frame(HomePage)
            app.get_frame(HomePage).fetchInformation()

    def back(self, name):
        name.set("")
        app.show_frame(HomePage)


class EntryPopUp(Entry):
    def __init__(self, parent, iid, text, id_group, opened_folder, target, **kw):

        super().__init__(parent, **kw)
        self.tv = parent
        self['bd'] = 2
        self.iid = iid
        self.insert('end', text[0])

        self['exportselection'] = False
        self.focus_force()
        self.bind("<Return>", self.on_return)
        # self.bind("<Control-a>", self.select_all)
        self.bind("<Escape>", self.on_destroy)

        self.id_group = id_group
        self.opened_folder = opened_folder
        self.old_filename = text[0]
        self.target = target

    def on_return(self, event):
        widget = event.widget
        if self.target == "file":
            data = {"rename_file": 1, "id_group": self.id_group,
                    "old_file_name": self.opened_folder + self.old_filename,
                    "new_file_name": self.opened_folder + widget.get()}

            # print(data)
            resp = session.post(SERVER_URL, data)
            if len(resp.text) > 0:
                # print(resp.text)
                error_message(resp.text)

        elif self.target == "folder":
            data = {"create_folder": 1, "id_group": self.id_group,
                    "folder_path": self.opened_folder + widget.get()}

            resp = session.post(SERVER_URL, data)
            if len(resp.text) > 0:
                # print(resp.text)
                error_message(resp.text)

        elif self.target == "rename_folder":
            data = {"rename_folder": 1, "id_group": self.id_group,
                    "old_folder_path": self.opened_folder + self.old_filename,
                    "new_folder_path": self.opened_folder + widget.get()}

            resp = session.post(SERVER_URL, data)
            if len(resp.text) > 0:
                # print(resp.text)
                error_message(resp.text)

        app.get_frame(HomePage).fetchInformation()
        app.get_frame(GroupPage).refresh_informations(self.id_group)

        self.destroy()

    def on_destroy(self, event):
        if self.target == "folder":
            app.get_frame(GroupPage).cancel_create_folder()

        self.destroy()


class OptionMenuPopup(OptionMenu):
    def __init__(self, parent, iid, text, id_group, **kw):
        self.variable = StringVar()
        self.variable.set(text[1])
        self.variable.trace('w', self.on_return)

        super().__init__(parent, self.variable, *permissions, **kw)
        self.tv = parent
        self['bd'] = 2
        self.iid = iid

        self.focus_force()
        self.bind("<Return>", self.on_return)
        # self.bind("<Control-a>", self.select_all)
        self.bind("<Escape>", self.on_destroy)

        self.id_group = id_group
        self.username = text[0]

    def on_return(self, event=None, *args):
        try:
            new_perm = event.widget.get()
        except:
            new_perm = self.variable.get()

        current_group = user_info["groups"][app.get_frame(GroupPage).id_group]
        for user in current_group["users"]:
            if user["name"] == self.username:
                data = {"change_permission": 1, "user_id_to_change":
                        user["id"], "new_perm": str_to_permission(new_perm),
                        "id_group": app.get_frame(GroupPage).id_group}
                resp = session.post(SERVER_URL, data)
                # print(data)
                if len(resp.text) > 0:
                    # print(resp.text)
                    error_message(resp.text)

                break

        app.get_frame(HomePage).fetchInformation()
        app.get_frame(GroupUsers).refresh_informations(
            app.get_frame(GroupPage).id_group)

        self.destroy()

    def on_destroy(self, e=None):
        self.destroy()


class GroupList(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent, bg="#71d2f0")
        label = Label(self, text="Filelocker", font=(
            LARGE_FONT, 22), bg="#71d2f0")
        label.pack(pady=(30, 15), padx=30)

        Label(self, text="Groups", font=LARGE_FONT,
              bg="#71d2f0").pack(pady=10, padx=10)

        # back button
        backPhoto = PhotoImage(file="assets/imgs/icons8-arriere-32.png")
        buttonBack = Button(self, text="Back", command=self.back, image=backPhoto,
                            compound=LEFT, width=75, height=25,
                            relief="flat", bg="#71d2f0", highlightcolor="#71d2f0")
        buttonBack.image = backPhoto
        buttonBack.pack(pady=(0, 0))

    def back(self):
        destroy_widget(widgets_list)
        app.show_frame(HomePage)
        app.get_frame(HomePage).fetchInformation()

    def refresh_informations(self):
        for id_group in user_info["groups"]:
            # print(group)
            group = user_info["groups"][id_group]
            button = Button(self, text=group["name"], command=partial(
                self.enter_group, group["id"]))
            button.pack(side="top")

            widgets_list.append(button)

        if len(user_info["groups"]) == 0:
            label = Label(
                self, text="You do not have any group yet", font=LARGE_FONT)
            label.pack(pady=10, padx=10)
            widgets_list.append(label)

    def enter_group(self, id):
        global widgets_list
        widgets_list = destroy_widget(widgets_list)

        app.show_frame(GroupPage)
        app.get_frame(GroupPage).refresh_informations(id)


# https://github.com/imran2244556677/File-Explorer-with-Tkinter


class GroupPage(Frame):
    def __init__(self, parent, controller):
        # register the current folder
        self.opened_folder = ""

        # register current group id
        self.id_group = None

        # register the file tree
        self.file_tree = None

        Frame.__init__(self, parent, bg="#71d2f0")
        self.groupname = Label(self, text="Group", font=LARGE_FONT)
        self.groupname.pack(pady=10, padx=10)

        # back button
        backPhoto = PhotoImage(file="assets/imgs/icons8-arriere-32.png")
        buttonBack = Button(self, text="Back", command=self.back, image=backPhoto,
                            compound=LEFT, width=75, height=25,
                            relief="flat", bg="#71d2f0", highlightcolor="#71d2f0")
        buttonBack.image = backPhoto
        buttonBack.pack(pady=(30, 0))

        # refresh button
        refreshPhoto = PhotoImage(file="assets/imgs/icons8-rafraîchir-30.png")
        buttonRefresh = Button(self, text="Refresh", command=self.refresh, image=refreshPhoto,
                               compound=LEFT, width=115, height=25)
        buttonRefresh.image = refreshPhoto
        buttonRefresh.pack(padx=10, pady=(0, 20))

        # add user button
        groupPhoto = PhotoImage(
            file="./assets/imgs/icons8-groupe-premier-plan-sélectionné-32.png")
        buttonGroup = Button(self, text="User list", image=groupPhoto, command=self.enter_group_user,
                             compound=LEFT, width=115, height=25)
        buttonGroup.image = groupPhoto
        buttonGroup.pack(padx=10, pady=(0, 20))

        # remove group button
        logOutPhoto = PhotoImage(file="assets/imgs/icons8-macos-fermer-30.png")
        buttonLogOut = Button(self, text="Remove group", image=logOutPhoto, command=self.remove_group,
                              compound=LEFT, width=115, height=25)
        buttonLogOut.image = logOutPhoto
        buttonLogOut.pack(padx=10, pady=(0, 20))

        panedWindow = PanedWindow(self, bg="#71d2f0")
        panedWindow.pack(fill='both', expand=1)

        scrollY = Scrollbar(self, orient='vertical')
        scrollY.pack(fill='y', side='right')

        upBtn = Button(self, text="↑", font='{} 17',
                       bd=0, command=self.back_folder, bg="#cdf4ff")
        upBtn.pack(anchor='nw')

        # register the list of files/folder in the current directory
        self.fileList = ttk.Treeview(self, yscrollcommand=scrollY.set, columns=[
            "name", "date modified", "type", "size"], selectmode="browse")

        self.fileList.heading("name", text="Name")
        self.fileList.heading("date modified", text="Date Modified")
        self.fileList.heading("type", text="Type")
        self.fileList.heading("size", text="Size")

        self.fileList['show'] = 'headings'

        self.fileList.column("name", width=200)
        self.fileList.column("date modified", width=50)
        self.fileList.column("type", width=20)
        self.fileList.column("size", width=150)

        self.fileList.pack(fill="both", expand=1, side='top')
        scrollY.configure(command=self.fileList.yview)

        self.fileList.drop_target_register(DND_FILES)
        self.fileList.dnd_bind('<<Drop>>', self.dnd_send_file)

        panedWindow.add(self)

        self.fileList.bind("<Double-1>", self.enter_folder)
        self.fileList.bind("<Return>", self.enter_folder)
        self.fileList.bind("<ButtonRelease-3>", self.rightClicked)

        self.rightClickFile = Menu(self, tearoff=0)
        self.rightClickFile.add_command(
            label="Download", command=self.download)
        self.rightClickFile.add_command(label="Rename", command=self.rename)
        self.rightClickFile.add_command(label="Delete", command=self.delete)

        self.rightClickVoid = Menu(self, tearoff=0)
        self.rightClickVoid.add_command(
            label="New folder", command=self.create_folder)

        self.rightClickFolder = Menu(self, tearoff=0)
        self.rightClickFolder.add_command(label="Rename", command=self.rename)
        self.rightClickFolder.add_command(label="Delete", command=self.delete)

    def back(self):
        app.show_frame(GroupList)
        app.get_frame(HomePage).fetchInformation()
        app.get_frame(GroupList).refresh_informations()

    def refresh(self):
        app.get_frame(HomePage).fetchInformation()
        self.refresh_informations(self.id_group)

    def rightClicked(self, e):
        try:
            rowid = self.fileList.identify_row(e.y)
            self.fileList.selection_set(rowid)

            global x_root, y_root
            x_root = e.x_root
            y_root = e.y_root

            cur = self.fileList.selection()
            if len(self.fileList.item(cur)['values']) > 0:
                if "Directory" in self.fileList.item(cur)["values"][2]:
                    self.rightClickFolder.tk_popup(x=e.x_root, y=e.y_root)
                else:
                    self.rightClickFile.tk_popup(x=e.x_root, y=e.y_root)
            else:
                if not can_write(user_info["username"], self.id_group):
                    return
                self.rightClickVoid.tk_popup(x=e.x_root, y=e.y_root)

        finally:
            self.rightClickFile.grab_release()
            self.rightClickFolder.grab_release()
            self.rightClickVoid.grab_release()

    def rename(self):
        if not can_write(user_info["username"], self.id_group):
            error_message("You do not have the authorization!")
            return

        rowid = self.fileList.selection()
        element = self.fileList.item(rowid, 'values')
        if "Directory" in element[2]:
            self.rename_folder()
        else:
            self.rename_file()

    def rename_file(self):
        rowid = self.fileList.selection()
        column_id = "#1"

        x, y, width, height = self.fileList.bbox(rowid, column_id)

        text = self.fileList.item(rowid, 'values')
        entryPopUp = EntryPopUp(self.fileList, rowid,
                                text, self.id_group, self.opened_folder, "file")
        entryPopUp.place(x=0, y=y, width=width, height=height)

    def download(self):
        if not os.path.exists(os.getcwd() + "/temp"):
            os.makedirs(os.getcwd() + "/temp")

        rowid = self.fileList.selection()
        filename = self.fileList.item(rowid, 'values')[0]

        data = {"retrieve_file": 1, "id_group": self.id_group,
                "filepath": self.opened_folder + filename}
        resp = session.post(SERVER_URL, data)

        try:
            # print(resp.content)
            raw_data = resp.content.decode("utf-8").split(" ~~~ ")
            file_json = json.loads(raw_data[0])
            file_content = raw_data[1]

            # print(file_json)
            # print(file_content)

            with open(os.getcwd() + "/keys/" + user_info["username"] + ".pem", "r") as key_file:
                key = key_file.read()

            aes_key = crypto.decrypt_RSA(key, file_json["ciphered_aes"])
            aes_nonce = crypto.decrypt_RSA(key, file_json["ciphered_nonce"])

            # print(aes_key, aes_nonce)

            decipher_file_content = crypto.decrypt_AES(
                aes_key, aes_nonce, file_content)

            f = filedialog.asksaveasfile(
                initialdir="/", title="Select folder", initialfile=filename, filetypes=[("All files", "*.*")])
            if f is None:
                return
            else:
                with open(f.name, "wb") as new_file:
                    new_file.write(decipher_file_content)
                f.close()
        except:
            error_message(resp.text)

    def refresh_informations(self, id):
        global user_info
        group = user_info["groups"][id]

        path_list = []
        for file in group["files"]:
            path_list.append(file["path"])
            # print(file)

        # for correct tree for group files
        self.file_tree = path_to_tree.generate_tree(path_list)
        self.id_group = id

        self.groupname.configure(text=group["name"])

        app.get_frame(GroupPage).refresh_folder()

    def refresh_folder(self):
        folder_content = path_to_tree.get_folder_content(
            self.file_tree, self.opened_folder)
        self.fileList.delete(*self.fileList.get_children())

        for file in folder_content[path_to_tree.FILE_MARKER]:
            for file_json in user_info["groups"][self.id_group]["files"]:
                # print(file_json["path"], self.opened_folder + file)
                if file_json["path"] == self.opened_folder + file:
                    self.fileList.insert('', END, values=[
                                         file, file_json["modification_date"], "File", byte_to_str(file_json["size"])])

        for folder in folder_content[path_to_tree.FOLDER_MARKER]:
            self.fileList.insert(
                '', END, values=[folder, "", "File Directory", ""])

    def dnd_send_file(self, event):
        thread = threading.Thread(target=self.add_file, args=(event,))
        thread.start()

    def add_file(self, event):
        if not os.path.exists(os.getcwd() + "/temp"):
            os.makedirs(os.getcwd() + "/temp")

        if not can_write(user_info["username"], self.id_group):
            error_message("You do not have the authorization!")
            return

        self.fileList.insert('', END, values=[
            "Sending...", "", "File", ""])
        self.update()

        # remove the { } from the event.data if existing
        if event.data[0] == '{':
            file_to_upload = event.data[1:-1]
        else:
            file_to_upload = event.data

        with open(file_to_upload, "rb") as f:
            global session
            content_to_cipher = f.read()

        for user in user_info["groups"][self.id_group]["users"]:
            aes_key, aes_nonce, encrypted_file = crypto.generate_and_encrypt_AES(
                content_to_cipher)

            aes_key = crypto.encrypt_RSA(user["public_key"], aes_key)
            aes_nonce = crypto.encrypt_RSA(user["public_key"], aes_nonce)

            # print(encrypted_file)
            temp_filename = user["id"] + "_" + \
                os.path.basename(file_to_upload)
            temp_file = open(os.getcwd() + "/temp/" + temp_filename, "w")
            temp_file.write(encrypted_file)
            temp_file.close()

            with open(os.getcwd() + "/temp/" + temp_filename, "rb") as f:
                data = {"add_file": 1, "id_group": self.id_group,
                        "wanted_path": self.opened_folder, "filename": os.path.basename(file_to_upload),
                        "ciphered_for": user["id"], "ciphered_aes": aes_key, "ciphered_nonce": aes_nonce}

                resp = session.post(SERVER_URL, data, files={
                                    "uploaded_file": f})

                if len(resp.text) > 0:
                    # print(resp.text)
                    error_message(resp.text)
                    f.close()
                    break

        for root, dirs, files in os.walk(os.getcwd() + "/temp/"):
            for file in files:
                os.remove(os.path.join(root, file))

        app.get_frame(HomePage).fetchInformation()
        self.refresh_informations(self.id_group)

    def create_folder(self):
        rowid = self.fileList.insert(
            '', END, values=["New Folder", "", "File Directory", ""])
        column_id = "#1"

        x, y, width, height = self.fileList.bbox(rowid, column_id)

        text = self.fileList.item(rowid, 'values')
        entryPopUp = EntryPopUp(self.fileList, rowid,
                                text, self.id_group, self.opened_folder, "folder")
        entryPopUp.place(x=0, y=y, width=width, height=height)

    def cancel_create_folder(self):
        item = self.fileList.get_children()[-1]
        self.fileList.delete(item)

    def rename_folder(self):
        rowid = self.fileList.selection()
        column_id = "#1"

        x, y, width, height = self.fileList.bbox(rowid, column_id)

        text = self.fileList.item(rowid, 'values')
        entryPopUp = EntryPopUp(self.fileList, rowid,
                                text, self.id_group, self.opened_folder, "rename_folder")
        entryPopUp.place(x=0, y=y, width=width, height=height)

    def delete(self):
        if not can_write(user_info["username"], self.id_group):
            error_message("You do not have the authorization!")
            return

        rowid = self.fileList.selection()
        element = self.fileList.item(rowid, 'values')
        if "Directory" in element[2]:
            self.delete_folder()
        else:
            self.delete_file()

    def delete_file(self):
        cur = self.fileList.selection()
        ans = messagebox.askyesno("Delete!", "Do you really want to delete?")
        if ans:
            data = {"remove_file": 1, "id_group": self.id_group,
                    "path": self.opened_folder + self.fileList.item(cur)['values'][0]}
            resp = session.post(SERVER_URL, data)

            if len(resp.text) > 0:
                # print(resp.text)
                error_message(resp.text)

        app.get_frame(HomePage).fetchInformation()
        self.refresh_informations(self.id_group)

    def delete_folder(self):
        cur = self.fileList.selection()
        ans = messagebox.askyesno("Delete!", "Do you really want to delete?")
        if ans:
            data = {"remove_folder": 1, "id_group": self.id_group,
                    "folder_path": self.opened_folder + self.fileList.item(cur)['values'][0]}
            resp = session.post(SERVER_URL, data)

            if len(resp.text) > 0:
                # print(resp.text)
                error_message(resp.text)

        app.get_frame(HomePage).fetchInformation()
        self.refresh_informations(self.id_group)

    def enter_user(self, user):
        app.show_frame(UserPage)
        app.get_frame(UserPage).refresh_informations(user)
        app.get_frame(UserPage).set_back_target(GroupPage)

    def enter_folder(self, e=None):
        cur = self.fileList.selection()
        try:
            if "Directory" in self.fileList.item(cur)['values'][2]:
                folder = self.fileList.item(cur)['values'][0]

                self.opened_folder += folder + "/"
                self.refresh_folder()
            elif "File" in self.fileList.item(cur)['values'][2]:
                self.download()
        except IndexError:
            pass
        except NameError:
            pass

    def back_folder(self):
        if len(self.opened_folder) > 0:
            new_path = ""
            for folder in self.opened_folder.split("/")[:-2]:
                if len(folder) > 0:
                    new_path += folder + "/"

            if len(new_path) == 1:
                new_path = ""

            self.opened_folder = new_path
            self.refresh_folder()

    def enter_group_user(self):
        destroy_widget(widgets_list)
        app.show_frame(GroupUsers)
        app.get_frame(GroupUsers).refresh_informations()

    def remove_group(self):
        ans = messagebox.askyesno("Delete!", "Do you really want to delete?")
        if ans:
            data = {"remove_group": 1, "id_group": self.id_group}
            resp = session.post(SERVER_URL, data)

            if len(resp.text) > 0:
                # print(resp.text)
                error_message(resp.text)
            else:
                app.get_frame(HomePage).fetchInformation()
                app.show_frame(HomePage)


class GroupUsers(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent, bg="#71d2f0")

        search = StringVar()

        Label(self, text="Group Users", font=LARGE_FONT).pack(pady=10, padx=10)

        # back button
        self.back = partial(self.back, search)
        backPhoto = PhotoImage(file="assets/imgs/icons8-arriere-32.png")
        buttonBack = Button(self, text="Back", command=self.back, image=backPhoto,
                            compound=LEFT, width=75, height=25,
                            relief="flat", bg="#71d2f0", highlightcolor="#71d2f0")
        buttonBack.image = backPhoto
        buttonBack.pack(pady=(30, 0))

        # self.panedWindow = PanedWindow(self)
        # self.panedWindow.pack(fill='both', expand=1)

        self.search_label = Label(self, text="Add friends to the group")
        self.search_label.pack(side="top", pady=(25, 5))

        self.search_entry = Entry(self, textvariable=search, bg="#cdf4ff")
        self.search_entry.pack(side="top")

        self.refresh_informations = partial(self.refresh_informations, search)
        self.search_entry.bind("<KeyRelease>", self.refresh_informations)

        # list of current users
        self.user_list = ttk.Treeview(self, columns=[
            "name", "permission"], selectmode="browse")

        self.user_list.heading("name", text="Name")
        self.user_list.heading(
            "permission", text="User's permissions")

        self.user_list['show'] = 'headings'
        self.user_list.pack(side="left", fill="y", padx=25, pady=25)

        self.user_list.bind("<Double-1>", self.enter_user)
        self.user_list.bind("<Return>", self.enter_user)

        # part to search friends to add

        self.searchResults = Listbox(self, width=30)
        self.searchResults.pack(side="right", fill="y", padx=25, pady=25)

        self.searchResults.bind("<Double-1>", self.add_user)
        self.searchResults.bind("<Return>", self.add_user)
        self.user_list.bind("<ButtonRelease-3>", self.rightClicked)

        # self.panedWindow.add(self.user_list)
        # self.panedWindow.add(self.searchResults)

        self.rightClickUser = Menu(self, tearoff=0)
        self.rightClickUser.add_command(
            label="Delete", command=self.delete_user)
        self.rightClickUser.add_command(
            label="Change permission", command=self.enter_change_perm)

    def back(self, search):
        search.set("")
        app.show_frame(GroupPage)
        app.get_frame(GroupPage).refresh_informations(
            app.get_frame(GroupPage).id_group)

    def refresh_informations(self, search, e=None):
        search_inp = search.get()

        """if not is_admin(user_info["username"], app.get_frame(GroupPage).id_group):
            self.search_label.destroy()
            self.search_entry.destroy()
            self.searchResults.destroy()"""

        self.searchResults.delete(0, END)
        for friend in user_info["friends"]:
            if len(search_inp) == 0 or search_inp.lower() in friend["name"].lower():
                self.searchResults.insert(END, friend["name"])

        self.user_list.delete(*self.user_list.get_children())
        current_group = user_info["groups"][app.get_frame(GroupPage).id_group]
        for user in current_group["users"]:

            if not is_owner(user["name"], current_group):
                perm = permission_to_str(user["id_permission"])
            else:
                perm = "Owner"

            self.user_list.insert('', END, values=[user["name"], perm])

    def rightClicked(self, e):
        id_group = app.get_frame(GroupPage).id_group
        if not is_admin(user_info["username"], id_group):
            return

        try:
            rowid = self.user_list.identify_row(e.y)
            self.user_list.selection_set(rowid)

            global x_root, y_root
            x_root = e.x_root
            y_root = e.y_root

            cur = self.user_list.selection()
            if len(self.user_list.item(cur)['values']) > 0:
                clicked_username = self.user_list.item(cur)['values'][0]
                if clicked_username != user_info["username"] and is_admin(user_info["username"], id_group) and not is_owner(clicked_username, user_info["groups"][id_group]):
                    self.rightClickUser.tk_popup(x=e.x_root, y=e.y_root)

        finally:
            self.rightClickUser.grab_release()

    def add_user(self, e=None):
        if not is_admin(user_info["username"], app.get_frame(GroupPage).id_group):
            error_message("You do not have the authorization to add users")
            return

        cur = self.searchResults.curselection()

        username = self.searchResults.get(cur)
        current_group = user_info["groups"][app.get_frame(GroupPage).id_group]

        for user in current_group["users"]:
            if user["name"] == username:
                return

        for user in user_info["friends"]:
            if user["name"] == username:
                new_user_id = user["id"]

        data = {"add_group_user": 1, "id_group": app.get_frame(GroupPage).id_group,
                "new_user_id": new_user_id}

        # print(data)
        resp = session.post(SERVER_URL, data)
        if len(resp.text) > 0:
            # print(resp.text)
            error_message(resp.text)

        app.get_frame(HomePage).fetchInformation()
        self.refresh_informations()

    def enter_user(self, e=None):
        cur = self.user_list.selection()
        try:
            username = self.user_list.item(cur)['values'][0]
            for user in user_info["groups"][app.get_frame(GroupPage).id_group]["users"]:
                if user["name"] == username:
                    app.show_frame(UserPage)
                    app.get_frame(UserPage).set_back_target(GroupUsers)
                    app.get_frame(UserPage).refresh_informations(user)
        except IndexError:
            pass
        except NameError:
            pass

    def delete_user(self):
        cur = self.user_list.selection()
        username = self.user_list.item(cur)['values'][0]
        ans = messagebox.askyesno("Delete!", "Do you really want to delete?")
        if ans:
            for user in user_info["groups"][app.get_frame(GroupPage).id_group]["users"]:
                if user["name"] == username:
                    new_user_id = user["id"]

            data = {"remove_group_user": 1, "id_group": app.get_frame(GroupPage).id_group,
                    "new_user_id": new_user_id}
            resp = session.post(SERVER_URL, data)

            if len(resp.text) > 0:
                # print(resp.text)
                error_message(resp.text)

        app.get_frame(HomePage).fetchInformation()
        self.refresh_informations()

    def enter_change_perm(self):
        rowid = self.user_list.selection()
        column_id = "#2"

        x, y, width, height = self.user_list.bbox(rowid, column_id)

        text = self.user_list.item(rowid, 'values')
        entryPopUp = OptionMenuPopup(self.user_list, rowid,
                                     text, app.get_frame(GroupPage).id_group)
        entryPopUp.place(x=x, y=y, width=width, height=height)


class UserPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent, bg="#71d2f0")
        Label(self, text="User", font=LARGE_FONT).pack(pady=10, padx=10)

        # back button
        Button(self, text="Back", command=self.back).pack()

        self.back_target = HomePage

    def set_back_target(self, target):
        self.back_target = target

    def back(self):
        app.get_frame(HomePage).fetchInformation()
        app.show_frame(self.back_target)

    def refresh_informations(self, user):
        global widgets_list
        widgets_list = destroy_widget(widgets_list)

        name = Label(app, text="Name: " + user["name"])
        name.pack(side="top")

        email = Label(app, text="Email: " + user["email"])
        email.pack(side="top")

        widgets_list.append(name)
        widgets_list.append(email)


# window
app = App()
app.mainloop()
