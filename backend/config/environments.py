"""
Environment-specific configurations
"""
from .config import settings


class DevelopmentConfig:
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    DATABASE_URL = settings.supabase_url


class ProductionConfig:
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    DATABASE_URL = settings.supabase_url


class TestingConfig:
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = settings.supabase_url


# Environment mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}


def get_config(env_name: str = 'development'):
    """Get configuration based on environment name"""
    return config_map.get(env_name, DevelopmentConfig) 