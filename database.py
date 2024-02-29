from sqlalchemy.engine import URL
from sqlalchemy import create_engine, Table, MetaData, select, func, and_, not_, text
from dotenv import load_dotenv
import os, pandas as p
import jwt, datetime, pyodbc

load_dotenv()

class CONNECTION:
    """
    Class defining a database.
    """
    def __init__(self):
        self.metadata = MetaData()

    def login(self, UID, PWD):
        """
        Establish connection with the database if the user and password are correct
        """
        # Take the user and password typed by user and create the engine
        connection_string2 = f"DRIVER={{{os.getenv('DRIVER')}}};SERVER={os.getenv('SERVER')};DATABASE={os.getenv('DATABASE2')};UID={UID};PWD={PWD}"
        connection_url2 = URL.create('mssql+pyodbc', query={'odbc_connect': connection_string2})
        engine_configuration = create_engine(connection_url2)

        try:
            # Try to establish connection
            with engine_configuration.connect() as conn: 
                # If user and password are correct, the engine is saved on the class.    
                self.engine_configuration = engine_configuration # Engine_configuration is where the configuration data is saved

                # Create a new engine where the database's information is.
                connection_string = f"DRIVER={{{os.getenv('DRIVER')}}};SERVER={os.getenv('SERVER')};DATABASE={os.getenv('DATABASE')};UID={UID};PWD={PWD}"
                connection_url = URL.create('mssql+pyodbc', query={'odbc_connect': connection_string})
                self.engine_information = create_engine(connection_url) # Engine_information is where the data it is

                # Table where Users are
                user_table = self.get_table('TABLE_USERS', self.engine_configuration)

                # Query to search the user who logged in
                stmt = select(
                    self.get_table_column(user_table, 'COLUMN_TABLE_USERS_FIRST_NAME').label('user_first_name'),
                    self.get_table_column(user_table, 'COLUMN_TABLE_USERS_LAST_NAME').label('user_last_name')
                ).where(
                    self.get_table_column(user_table, 'COLUMN_TABLE_USERS_LOGIN') == UID
                )

                # onvert to dataframe
                user_dataframe = p.read_sql_query(stmt, self.engine_configuration)

                # Get name and Lastname
                name = str(user_dataframe.loc[0,'user_first_name']).strip()
                lastname = str(user_dataframe.loc[0,'user_last_name']).strip()

                # Create jwt token
                token = self.create_jwt_token(name, lastname, UID, 4)

                # Function to load the orders into class attribute
                self.load_orders(token)

                # Return token to main application
                return token
            
        except Exception as e:
            # If the user or password is incorret, the program raise a exceptiom
            raise Exception('Usuario ou senha Incorreto', e)

    def get_table(self, table, engine):
        return Table(os.getenv(table), self.metadata, autoload_with=engine)
    
    def get_table_column(self, table, column):
        return getattr(table.c, os.getenv(column))
    
    def create_jwt_token(self, name, lastname, login, expiration_time_hour):
        """
        Create a JWT Token
        """
        payload = { 'name': name, 'lastname': lastname, 'login': login }
        expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours = expiration_time_hour)
        token = jwt.encode({'exp': expiration_time, **payload}, os.getenv('SECRET_KEY'), algorithm='HS256') 

        return token
    
    def get_user_informations(self, token):
        """
        Return the user information if the token is valid
        """
        validated_token = self.validade_token(token)
        if validated_token:
            return {
                'name': validated_token.get('name'),
                'lastname': validated_token.get('lastname'),
                'login': validated_token.get('login')
            }
        
        return False

    def validade_token(self, token):
        """
        Validate the JWT token
        """
        try:
            decoded_token = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=['HS256'])
            return decoded_token
        
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError('Token Expirado. Faça login novamente')
        
        except jwt.InvalidTokenError:
            raise jwt.InvalidTokenError('Token Invalido. Faça login Novamente')
        
    def load_orders(self, token):
        """
        Load orders into the class if the token is valid
        """
        if self.validade_token(token):
            # Definition of the tables
            orders = self.get_table('TABLE_ORDERS', self.engine_information)
            orders_items = self.get_table('TABLE_ORDERS_ITEMS', self.engine_information)
            items = self.get_table('TABLE_ITEMS', self.engine_information)
            entity = self.get_table('TABLE_ENTITY', self.engine_information)

            # SQL Statement
            stmt = select(
                self.get_table_column(entity, 'COLUMN_TABLE_ENTITY_ID').label('company_id'), # Id of the company
                self.get_table_column(orders, 'COLUMN_TABLE_ORDERS_CODE').label('order_code'), # Order code
                self.get_table_column(orders, 'COLUMN_TABLE_ORDERS_STATUS').label('order_status'), # Order status
                func.row_number().over(partition_by=self.get_table_column(orders_items, 'COLUMN_TABLE_ORDERS_ITEMS_ID'), order_by=self.get_table_column(orders_items, 'COLUMN_TABLE_ORDERS_ITEMS_ID_ORDER_ITEM')).label('item_number'),  # Get the order item order
                self.get_table_column(items, 'COLUMN_TABLE_ITEMS_ID').label('item_id'), # Get the item id
                self.get_table_column(items, 'COLUMN_TABLE_ITEMS_CODE').label('item_code'), # Get the item code
                self.get_table_column(items, 'COLUMN_TABLE_ITEMS_DESCRIPTION').label('item_description'), # Get product description
                self.get_table_column(orders_items, 'COLUMN_TABLE_ORDERS_ITEM_QUANTITY').label('item_quantity'), # Get item quantity
                self.get_table_column(orders_items, 'COLUMN_TABLE_ORDERS_ITEM_UNIT_PRICE').label('item_unit_price'), # Get the unit price
                func.current_date().label('date') # Get current date
            ).select_from(
                orders.join(
                    orders_items, 
                    self.get_table_column(orders, 'COLUMN_TABLE_ORDERS_ID') == self.get_table_column(orders_items, 'COLUMN_TABLE_ORDERS_ITEMS_ID')
                ).join(
                    items, 
                    self.get_table_column(orders_items, 'COLUMN_TABLE_ORDERS_ITEMS_ID_ITEM') == self.get_table_column(items, 'COLUMN_TABLE_ITEMS_ID')
                ).join(
                    entity, 
                    self.get_table_column(entity, 'COLUMN_TABLE_ENTITY_ID') == self.get_table_column(orders, 'COLUMN_TABLE_ORDERS_ID_COMPANY')
                )
            ).where(
                and_(
                    self.get_table_column(orders, 'COLUMN_OBJ_STATUS') == os.getenv('VALUE_OBJ_STATUS_ACTIVE'),
                    self.get_table_column(orders_items, 'COLUMN_OBJ_STATUS') == os.getenv('VALUE_OBJ_STATUS_ACTIVE'),
                    not_(self.get_table_column(orders, 'COLUMN_TABLE_ORDERS_STATUS').in_(['CAN', 'DIG']))
                )
            )

            # Read statment using pandas to convert to a dataframe, and save the information into class attribute
            self.orders = p.read_sql_query(stmt, self.engine_information)
    
    def search_order(self, token, order, company):
        """
        Search order if the token is valid
        """
        if self.validade_token(token):
            company = 887 if company == 2 else 1
            return self.orders.loc[(self.orders['order_code'] == order) & (self.orders['company_id'] == company)]
        
    def concatenate_dataframe(self, token, dataframe, dataframe2):
        """
        Concatenate 2 dataframes
        """
        if self.validade_token(token):
            if isinstance(dataframe2, p.DataFrame):
                return p.concat((dataframe, dataframe2))
            else:
                return dataframe
            
    def process_items(self, token, company, dataframe):
        """
        Create the batch if does not exist, the stock movement and the batch movement.
        """
        if self.validade_token(token):
            try:
                with self.engine_information.connect() as conn:
                    company_number = 887 if company == 2 else 1
                    for i, row in dataframe.iterrows(): # Iterate over the dataframe

                        # Get information
                        date = row['date']
                        product_id = row['item_id']
                        quantity = row['item_quantity']
                        price = row['item_unit_price']
                        
                        # Create the batch number given the order list
                        batch = f'P{self.get_batch_from_orders(row["order_code"])}'
                        
                        # Here we start the creation of the batch, stock movement and the batch movement
                        batch_id = self.search_batch(batch, product_id, company_number, date, conn) # Search the batch_id for the batch number. if does not exist, it creates a new one
                        stock_movement_id = self.create_stock_movement(company_number, product_id, date, quantity, price, conn) # Create the stock movement
                        batch_movement_id = self.create_batch_movement(company_number, batch_id, date, quantity, stock_movement_id, conn) # Create the batch movement

                        print(product_id, str(row['item_code']).strip(), batch , batch_id, stock_movement_id, batch_movement_id)

                        # Save changes
                        conn.commit()

            except Exception as e:
                print(e)

    def search_batch(self, batch_number, product_id, company, date, conn):
        """
        Search the batch number in the database. Case does not exist, it creates a new one
        """
        # Database table
        batch_table = self.get_table('TABLE_BATCH', self.engine_information)

        # SQL Statement
        stmt = select(  
            self.get_table_column(batch_table, 'COLUMN_TABLE_BATCH_ID').label('batch_id'), 
            self.get_table_column(batch_table, 'COLUMN_TABLE_BATCH_NUMBER').label('batch_number'),
            self.get_table_column(batch_table, 'COLUMN_TABLE_BATCH_ITEM_ID').label('item_id')
        ).where(
            and_(
                self.get_table_column(batch_table, 'COLUMN_TABLE_BATCH_NUMBER') == batch_number,
                self.get_table_column(batch_table, 'COLUMN_TABLE_BATCH_ITEM_ID') == product_id
            )
        )

        # Read the sql statement using pandas to convert into dataframe
        batch = p.read_sql_query(stmt, self.engine_information)
        if batch.empty:
            batch_id = self.create_batch(0, batch_number, product_id, company, date, conn) # Create a new batch if does not exist

            return batch_id
        else:
            batch_id = batch.loc[0, 'batch_id']

            return batch_id.item()

    def get_batch_from_orders(self, orders):
        """
        Take the orders, split them and join again using '_'
        """
        orders_list = str(orders).split(', ')
        sorted_orders_list = sorted(map(int, orders_list))

        return '_'.join(map(str, sorted_orders_list))
    
    def create_batch(self, id_batch, batch_number, id_product, company, date_number, conn):
        """
        Create the batch in the database
        """
        stmt = os.getenv('SP_CREATE_BATCH')
        params = dict(batch_id = id_batch, batch = batch_number, product_id = id_product, company_number = company, date = date_number)

        result = conn.execute(text(stmt), params).scalar()
        return result
    
    def create_stock_movement(self, company, product_id, date, quantity, price, conn):
        """
        Create the stock movement in the database
        """
        storehouse = 5 if company == 887 else 1

        stmt = os.getenv('SP_CREATE_STOCK_MOVEMENT')
        params = dict(company = company, storehouse = storehouse, product_id = product_id, obs=f'{company}, Pedidos', date = date, quantity = quantity, price = price)

        result = conn.execute(text(stmt), params).scalar()
        return result
    
    def create_batch_movement(self, company, batch_id, date, quantity, stock_movement_id, conn):
        """
        Create the batch movement in the database
        """
        storehouse_id = 5 if company == 887 else 1

        stmt = os.getenv('SP_CREATE_BATCH_MOVEMENT')
        params = dict(batch_id = batch_id, storehouse_id = storehouse_id, date = date, quantity = quantity, stock_movement_id = stock_movement_id)

        result = conn.execute(text(stmt), params).scalar()
        return result
