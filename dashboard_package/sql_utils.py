from sqlalchemy import create_engine

# Function to establish a MySQL connection using SQLAlchemy
def establish_mysql_connection(credentials):
    try:
        # Construct the database URI for SQLAlchemy
        db_uri = f"mysql+mysqlconnector://{credentials['user']}:{credentials['password']}@{credentials['host']}:{credentials['port']}/{credentials['database']}"
        
        # Create the SQLAlchemy engine
        engine = create_engine(db_uri)

        return engine   
    except Exception as e:
        print(f"Error connecting to MySQL database: {e}")
        raise e
