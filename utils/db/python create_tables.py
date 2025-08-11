from databases.my_sql.user_table import Base
from utils.db.connect_to_my_sql import engine

Base.metadata.create_all(bind=engine)
