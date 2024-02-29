import tkinter as tk
from tkinter import ttk, messagebox
import database
import re


class System:
    def __init__(self):
        self.database = database.CONNECTION()
        self.frame_items = None
        self.items_to_process = None
        self.entrys = []
        self.start_login_window()

    # Windows
    def start_login_window(self):
        """
        Create the login window.
        """
        self.login_root = tk.Tk()
        self.login_root.title('Login')
        # mainframe for login window
        frame_login = ttk.Frame(self.login_root, padding=20)

        # labels for user and password
        label_user = ttk.Label(frame_login, text='Usuario: ', padding=5)
        label_password = ttk.Label(frame_login, text='Senha: ', padding=5)

        # Entrys data for user and password
        self.entry_user_variable = tk.StringVar()
        entry_user = ttk.Entry(frame_login, textvariable=self.entry_user_variable)

        self.entry_password_variable = tk.StringVar()
        entry_password = ttk.Entry(frame_login, textvariable=self.entry_password_variable, show='*')

        # Button for login
        button_login = ttk.Button(frame_login, text='Login', command=self.command_button_login)

        # Griding everything
        frame_login.grid()
        label_user.grid(row=0, column=0)
        entry_user.grid(row=0, column=1)

        label_password.grid(row=1, column=0)
        entry_password.grid(row=1, column=1)

        button_login.grid(row=2, column=0, columnspan=2, sticky='ew')

        # Setting the focus to the user entry
        entry_user.focus_set()

        # Defining the key binding
        frame_login.bind('<Return>', self.command_button_login)
        entry_user.bind('<Return>', self.command_button_login)
        entry_password.bind('<Return>', self.command_button_login)
        button_login.bind('<Return>', self.command_button_login)

        self.login_root.mainloop()

    def start_main_program(self):
        """
        Start the main program
        """
        # get the users datas
        self.user_data = self.database.get_user_informations(self.token)

        # close the logn page
        self.login_root.destroy()

        # creating the main window
        self.main_window_root = tk.Tk()

        # Set the main window to fullscreen
        self.main_window_root.state('zoomed')

        # Set the main's page title with the userdata
        self.main_window_root.title(f"Bem vindo {self.user_data['name']} {self.user_data['lastname']}")

        # Mainframe
        self.mainframe = ttk.Frame(self.main_window_root, border=1, relief='solid')

        # Frame of the Options
        frame_companys = ttk.Frame(self.mainframe)

        # Labels for company and entry
        label_company = ttk.Label(frame_companys, text='Empresa')
        label_entry = ttk.Label(frame_companys, text='Pedido')

        # Radios Button, Company 1 and 2
        self.variable_company = tk.IntVar(value=1)
        self.radiobutton_company1 = ttk.Radiobutton(frame_companys, text='Plastiveda', value=1, variable=self.variable_company)
        self.radiobutton_company2 = ttk.Radiobutton(frame_companys, text='Flexiveda', value=2, variable=self.variable_company)

        # Entry for the order
        self.variable_entry_order = tk.StringVar()
        self.entry_order = ttk.Entry(frame_companys, textvariable=self.variable_entry_order)

        # Validate the entry order to only allow numbers
        validate_cmd = self.main_window_root.register(self.on_validate_order)
        self.entry_order.config(validate='key', validatecommand=(validate_cmd, '%P'))

        # Button to search the order
        self.button_total = ttk.Button(frame_companys, text='Total', command=self.command_button_total)
        self.button_partial = ttk.Button(frame_companys, text='Parcial', command=self.command_button_partitial)
        self.button_reset = ttk.Button(frame_companys, text='Resetar', command=self.command_button_reset)

        # Grid configuration
        self.main_window_root.columnconfigure(0, weight=1)
        self.main_window_root.rowconfigure(0, weight=1)

        self.mainframe.columnconfigure(0, weight=1)

        self.mainframe.rowconfigure(1, weight=1)
        self.mainframe.grid(row=0, column=0, sticky='nsew')

        frame_companys.grid(row=0, column=0, sticky='n', pady=(70, 0))

        label_company.grid(row=0, column=0, columnspan=2)
        self.radiobutton_company1.grid(row=1, column=0, sticky='ew', padx=10)
        self.radiobutton_company2.grid(row=1, column=1, sticky='ew', padx=10)

        label_entry.grid(row=2, column=0, columnspan=2, pady=10)
        self.entry_order.grid(row=3, column=0, columnspan=2, pady=(0, 30))

        self.button_total.grid(row=4, column=0)
        self.button_partial.grid(row=4, column=1)
        self.button_reset.grid(row=5, column=0, columnspan=2)

        self.entry_order.focus_set()

        self.entry_order.bind('<Key-t>', self.command_button_total)
        self.entry_order.bind('<Key-g>', self.command_button_partitial)
        self.entry_order.bind('<Shift-R>', self.command_button_reset)
        self.entry_order.bind('<Control-space>', self.command_process_items)

    # Comands
    def command_button_login(self, *args):
        """
        Command that runs when the user click on the login button

        Try to login in the database
        """
        # Get the user and password from the user entrys
        username = self.entry_user_variable.get()
        password = self.entry_password_variable.get()

        try:
            # Try to login and save the token on the class attribute
            self.token = self.database.login(username, password) 
            self.start_main_program() # Start the program if the login is successful

        except Exception as e:
            messagebox.showerror(title='Erro', message=e) # Case the user or password is incorrect
        
    def command_button_total(self, *args):
        """
        Command that runs when user press the Total Button

        Add the entire order the items to process
        """
        # Get user entrys
        order = int(self.variable_entry_order.get())
        company = self.variable_company.get()
        
        try:
            # Search the order on the database
            self.searched_order = self.database.search_order(self.token, order, company)

            # Save the searched order to the items to process
            self.items_to_process = self.database.concatenate_dataframe(self.token, self.searched_order, self.items_to_process)

            # If the items to process dataframe is not empty, disable the other radio button to not allow the user change the company
            if not self.items_to_process.empty:
                if company == 1:
                    self.radiobutton_company2.config(state='disabled')
                else:
                    self.radiobutton_company1.config(state='disabled')

            # Delete the order entry
            self.variable_entry_order.set('')

            # Set the focus to the user entry
            self.entry_order.focus_set()

            # Refresh the frame
            self.command_refresh_items_frames(self.token)

        except Exception as e:
            messagebox.showerror(title='Token Expirado', message=e)
            self.main_window_root.destroy()
            self.start_login_window()

    def command_button_partitial(self, *args):
        """
        Command that runs when the user press the partitial button

        Create a new window to user select the item and quantity
        """
        # Get the user entrys
        order = self.variable_entry_order.get()
        if order:
            order = int(order)
            self.disable_buttons() 
            company = self.variable_company.get()
        else:
            self.on_cancel_partitial_process()

        # Search the order in the database
        self.searched_order = self.database.search_order(self.token, order, company)

        # Create new window
        self.new_window = tk.Toplevel(self.main_window_root)
        # Setting the command to run if the user close this window
        self.new_window.protocol("WM_DELETE_WINDOW", self.on_cancel_partitial_process)

        # Set the window to fullscreen
        self.new_window.state('zoomed')

        self.new_window.title('Items')
        self.new_window.title('Seleciona os Itens')
        # self.new_window.iconbitmap("Areco_logo.ico")

        mainframe = ttk.Frame(self.new_window)

        # Create the treeview
        self.partitital_treeview = ttk.Treeview(mainframe, columns=('item', 'reference_code', 'product_description', 'quantity'), show='headings')

        # Defining the heading
        self.partitital_treeview.heading('item', text='Item', anchor='center')
        self.partitital_treeview.heading('reference_code', text='Código', anchor='center')
        self.partitital_treeview.heading('product_description', text='Descrição', anchor='center')
        self.partitital_treeview.heading('quantity', text='Quantidade', anchor='center')

        # Configure the columns
        self.partitital_treeview.column('item', width=100, anchor='center')
        self.partitital_treeview.column('reference_code', width=150, anchor='center')
        self.partitital_treeview.column('product_description', width=550)
        self.partitital_treeview.column('quantity', width=100, anchor='center')

        # insert the searched order into the treeview
        for i, row in self.searched_order.iterrows():
            item_number = row['item_number']
            item_code = str(row['item_code']).strip()
            item_description = str(row['item_description']).strip()
            item_quantity = row['item_quantity']

            self.partitital_treeview.insert('', 'end', values=(item_number, item_code, item_description, 0), tags=(item_number, item_quantity))

        # Defining the key bindings
        self.partitital_treeview.bind('<Key-r>', self.on_key_r)
        self.partitital_treeview.bind('<Key-t>', self.on_key_t)
        self.partitital_treeview.bind('<Key-g>', self.on_key_g)
        self.partitital_treeview.bind('<space>', self.on_space)
        self.new_window.bind('<Escape>', self.on_cancel_partitial_process)
        self.partitital_treeview.bind('<Escape>', self.on_cancel_partitial_process)

        # Configurate the grids
        self.partitital_treeview.grid(row=0, column=0, sticky='ns')

        self.new_window.columnconfigure(0, weight=1)
        self.new_window.rowconfigure(0, weight=1)

        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)
        mainframe.grid(row=0, column=0, sticky='nsew')

    def command_button_reset(self, *args):
        """
        Command that runs when the user press the reset button
        """
        # Drop the items to process dataframe
        self.items_to_process.drop(index=self.items_to_process.index, inplace=True)
        if self.frame_items:
            self.frame_items.destroy()

        # Erase the user imputs
        self.variable_entry_order.set('')

        # Setting the focus to the entry order
        self.entry_order.focus_set()
        
        # Enable the radio buttons
        self.radiobutton_company1.config(state='normal')
        self.radiobutton_company2.config(state='normal')
    
    def command_add_partitial_items(self):
        """
        Command that runs when the user click on add partitial items in the top level


        """
        items = [] # List for the items that the quantity is greater than 0

        # Iterates over the treeview children
        for tree_item in self.partitital_treeview.get_children():

            # Get the quantity of the selected object   
            quantity = float(self.partitital_treeview.item(tree_item, 'values')[3]) 
            if quantity > 0:
                # Get the Item number from the added tag
                item = int(self.partitital_treeview.item(tree_item, 'tags')[0])

                # Change quantity of the searched order item to the entered quantity by the user
                self.searched_order.loc[self.searched_order['item_number'] == item, 'item_quantity'] = quantity

                items.append(item) # Add to the items list
        
        # Delete items from the searched order that are not in the items list
        self.searched_order = self.searched_order.loc[(self.searched_order['item_number'].isin(items))]

        # Add searched order dataframe to the items to process
        self.items_to_process = self.database.concatenate_dataframe(self.token, self.searched_order, self.items_to_process)

        company = self.variable_company.get()

         # If the items to process dataframe is not empty, disable the other radio button to not allow the user change the company
        if not self.items_to_process.empty:
            if company == 1:
                self.radiobutton_company2.config(state='disabled')
            else:
                self.radiobutton_company1.config(state='disabled')

        self.new_window.destroy()  # Close toplevel frame
        self.command_refresh_items_frames(self.token)
    
    def command_add_quantity_item(self, *args):
        """
        Command that runs when the user add the quantity to the partitial toplevel

        Update the quantity of the tree item to the new
        """
        # Change the ',' to '.'
        quantity = float(re.sub('\,', '.', self.variable_entry_quantity.get()))

        # Get the item that user select
        tree_item = self.partitital_treeview.selection()[0]

        # Change quantity
        self.partitital_treeview.set(tree_item, column='quantity', value=quantity)

        self.toplevel_quantity.destroy() # Close window
    
    def command_process_items(self, *args):
        """
        Command that runs when the user press Control + Space

        Process the items in the dataframe
        """
        # Get the entry information
        company = self.variable_company.get()

        # Confirm user choice
        choice = messagebox.askokcancel(title='Processar?', message='Deseja realmente gerar esse saldo?')
        if choice:
            # Start the process to process items
            self.database.process_items(self.token, company, self.items_to_process_grouped)
            messagebox.showinfo(title='Sucesso',message='Processado com Sucesso!!!')
            self.command_button_reset()
            self.command_refresh_items_frames(self.token)
        else:
            messagebox.showerror(title='Não processado',message='Não Processado. Confirme os itens novamente!!!')
    
    def command_refresh_items_frames(self, token):
        """
        Command that refresh the treeview of the items to process

        Refresh the main treeview with the updated dataframe
        """
        if self.database.validade_token(token):
            
            # Destroy frame_items if exists
            if self.frame_items:
                self.frame_items.destroy()

            # Group the items to process by the reference code, product id, product description and date, adding the item amount and the average of the price
            self.items_to_process_grouped = self.items_to_process.groupby(['item_code','item_id','item_description', 'date']).agg({'item_quantity': 'sum', 'item_unit_price': 'mean', 'order_code': lambda x: ', '.join(map(str, set(x))) }).reset_index()

            # Order the dataframe by description
            self.items_to_process_grouped = self.items_to_process_grouped.sort_values(by='item_description', ascending=True)
            
            # Create a new frame
            self.frame_items = ttk.Frame(self.mainframe)
            tree_view_items = ttk.Treeview(self.frame_items, columns=('reference_code', 'product_description', 'quantity', 'orders'), show='headings')

            # Setting the heading
            tree_view_items.heading('reference_code', text='Código', anchor='center')
            tree_view_items.heading('product_description', text='Descricao', anchor='center')
            tree_view_items.heading('quantity', text='Quantidade', anchor='center')
            tree_view_items.heading('orders', text='Pedidos', anchor='center')

            # Configurate the columns
            tree_view_items.column('reference_code', width=150, anchor='center')
            tree_view_items.column('product_description', width=550)
            tree_view_items.column('quantity', width=100, anchor='center')
            tree_view_items.column('orders', width=160, anchor='center')

            # Insert the updated dataframe
            for i, row in self.items_to_process_grouped.iterrows():
                item_code = str(row['item_code']).strip()
                item_description = str(row['item_description']).strip()
                item_quantity = row['item_quantity']
                order_code = row['order_code']

                tree_view_items.insert('', 'end', values=(item_code, item_description, item_quantity, order_code))

            # Configure the gird and layout
            self.frame_items.rowconfigure(0, weight=1)
            self.frame_items.columnconfigure(0, weight=1)

            self.frame_items.grid(row=1, column=0, sticky='ns', pady=50)
            tree_view_items.grid(row=0, column=0, sticky='ns')

            scrollbar = ttk.Scrollbar(self.frame_items, orient='vertical', command=tree_view_items.yview)
            tree_view_items.configure(yscroll=scrollbar.set)
            
            scrollbar.grid(row=0, column=1, sticky='ns')
    
    # Events binding
    def on_key_t(self, event):
        """
        Command that runs when user press T in the partitial treeview.

        Update the tree item to the total quantity
        """
        # Get the tree item
        tree_item = self.partitital_treeview.selection()[0]
        # Get the quantity by the tag
        quantity = float(self.partitital_treeview.item(tree_item, 'tags')[1])
        # Update the tree view
        self.partitital_treeview.set(tree_item, column='quantity', value=quantity)

    def on_key_g(self, event):
        """
        Command that runs when user press G in the partitial treeview.

        Create a new window with a entry to user enter the quantity
        """
        self.toplevel_quantity = tk.Toplevel(self.main_window_root, padx=30, pady=20)

        ttk.Label(self.toplevel_quantity, text='Informe a Quantidade').grid(row=0, column=0)

        self.variable_entry_quantity = tk.StringVar()
        entry_quantity = ttk.Entry(self.toplevel_quantity, width=10, textvariable=self.variable_entry_quantity)
        button_process = ttk.Button(self.toplevel_quantity, text='Processar', command=self.command_add_quantity_item)

        validate_cmd = self.toplevel_quantity.register(self.on_validate_quantity)
        entry_quantity.config(validate='key', validatecommand=(validate_cmd, '%P'))

        entry_quantity.focus_set()
        entry_quantity.bind('<Return>', self.command_add_quantity_item)
        button_process.bind('<Return>', self.command_add_quantity_item)

        entry_quantity.grid(row=1, column=0)
        button_process.grid(row=2, column=0)

    def on_key_r(self, event):
        """
        Command that runs when the user press R in the partitial treeview

        Reset the quantity of the treeview item to 0
        """
        tree_item = self.partitital_treeview.selection()[0]
        self.partitital_treeview.set(tree_item, column='quantity', value=0)

    def on_space(self, event):
        """
        Command that runs when the user press SPACE in the partitial treeview

        Add the partitial items to the items to precess dataframe
        """
        self.enable_buttons()

        self.variable_entry_order.set('')
        self.entry_order.focus_set()

        self.command_add_partitial_items()

    def on_validate_order(self, P):
        """
        Validate the order entry to only allow numbers
        """
        if re.match(r'^\d*$', P):
            return True
        return False

    def on_validate_quantity(self, P):
        """
        Validate the entered quantity by the user
        """
        if re.match(r'^\d*\,?\d*$', P):
            return True
        return False

    def on_cancel_partitial_process(self, *args):
        """
        Command that runs when user cancel the partitial operation
        """
        self.enable_buttons()
        self.new_window.destroy()
        self.command_refresh_items_frames(self.token)

    # Others
    def disable_buttons(self):
        """
        Disable all buttons
        """
        self.button_partial.config(state='disabled')
        self.button_reset.config(state='disabled')
        self.button_total.config(state='disabled')
        self.entry_order.config(state='disabled')
        self.radiobutton_company1.config(state='disabled')
        self.radiobutton_company2.config(state='disabled')

    def enable_buttons(self):
        """
        Enable all buttons
        """
        self.button_partial.config(state='normal')
        self.button_reset.config(state='normal')
        self.button_total.config(state='normal')
        self.entry_order.config(state='normal')
        self.radiobutton_company1.config(state='normal')
        self.radiobutton_company2.config(state='normal')

if __name__ == '__main__':
    system = System()
