import json
from google.cloud import secretmanager
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy

def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    credentials = get_cloud_sql_credentials()
    instance_connection_name = credentials['INSTANCE_CONNECTION_NAME']
    db_user = credentials["DB_USER"]
    db_pass = credentials["DB_PASS"]
    db_name = 'nueces_superfruit'

    ip_type = IPTypes.PUBLIC

    connector = Connector(ip_type)

    def getconn() -> pymysql.connections.Connection:
        conn: pymysql.connections.Connection = connector.connect(
            instance_connection_name,
            "pymysql",
            user=db_user,
            password=db_pass,
            db=db_name,
        )
        return conn

    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn
    )
    return pool

def get_cloud_sql_credentials():
    client = secretmanager.SecretManagerServiceClient()
    secret_name = "projects/913436042986/secrets/cloud_sql_credentials/versions/latest"
    
    response = client.access_secret_version(name=secret_name)
    secret_data = response.payload.data.decode("UTF-8")

    credentials = json.loads(secret_data)
    return credentials

def insert_row_to_table(data_dict, table):
    pool = connect_with_connector()
    ctx = pool.connect()

    data_dict = {**{k.upper(): v for k, v in data_dict.items()}}
    
    user_table = sqlalchemy.Table(table.upper(), sqlalchemy.MetaData(), autoload_with=ctx)

    stmt = sqlalchemy.insert(user_table).values(data_dict)
    ctx.execute(stmt)
    ctx.commit()
    ctx.close()

    return True