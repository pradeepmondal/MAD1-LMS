import os

base_dir = os.path.dirname(__file__)
dev_db_dir_path = os.path.join(base_dir, "../databases/development")
prod_db_dir_path = os.path.join(base_dir, "../databases/production")

# configuration for development environment
class DevelopmentConfig():
    DEBUG = True
    DB_DIR = dev_db_dir_path
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + dev_db_dir_path + "/devDB.sqlite3"

# configuration for production environment
class ProductionConfig():
    DEBUG = False
    DB_DIR = prod_db_dir_path
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + prod_db_dir_path + "/prodDB.sqlite3"
