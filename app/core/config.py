from pydantic_settings import BaseSettings
from pydantic import computed_field

class Settings(BaseSettings):

    # Cấu hình app name
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Facebook Clone"
    ENVIRONMENT: str

    #Cấu hình database
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_SERVER: str
    MYSQL_PORT: int
    MYSQL_DB: str
    MYSQL_ASYNC_PREFIX: str = "mysql+aiomysql://"
    MYSQL_SYNC_PREFIX: str = "mysql+pymysql://"

    # Cấu hình Mongo
    MONGO_CONNECTION_STRING: str
    MONGO_DB_NAME: str
    MONGO_USER: str
    MONGO_PASSWORD: str

    #Build URLs tự động
    @computed_field
    def DATABASE_URL(self) -> str:
        return f"{self.MYSQL_ASYNC_PREFIX}{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

    @computed_field
    def DATABASE_URL_SYNC(self) -> str:
        return f"{self.MYSQL_SYNC_PREFIX}{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

    # Cấu hình JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_SECONDS: int

    # Cấu hình email
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_FROM_NAME: str = PROJECT_NAME

    # Địa chỉ url back-end
    SERVER_BASE_URL: str

    # Địa chỉ url front-end tạo link trong email
    CLIENT_BASE_URL: str

    # OAUTH2
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    FACEBOOK_CLIENT_ID: str
    FACEBOOK_CLIENT_SECRET: str

    # Cấu hình cài đặt Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_DB: int

    # Cấu hình cài đặt Redis
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "10/minute"

    # Cloudy
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: int
    CLOUDINARY_API_SECRET: str

    @computed_field
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
