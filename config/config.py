import os


def _getenv(key, default=None, mandatory=True):
    if mandatory:
        if key in os.environ or default is not None:
            return os.getenv(key, default)
        raise KeyError("environment variable '%s' not set" % key)
    return os.getenv(key, default)


ENVIRONMENT         = _getenv('ENVIRONMENT',    default='dev')
PORT                = _getenv('PORT', default=5001)

JWT_SECRET_KEY      = _getenv('JWT_SECRET_KEY', mandatory=True)

DB_CONFIG = {
    'drivername':   _getenv('DB_DRIVER',    default='mysql+pymysql'),
    'host':         _getenv('DB_HOSTNAME',  default='localhost'),
    'port':         _getenv('DB_PORT',      default='3306'),
    'database':     _getenv('DB_NAME',      default='OPENXECO'),
    'username':     _getenv('DB_USERNAME',  default='openxeco'),
    'password':     _getenv('DB_PASSWORD',  mandatory=True),
    'query':        {'charset': _getenv('DB_CHARSET', default='utf8mb4')},
}

HTTP_PROXY          = _getenv('HTTP_PROXY', mandatory=False)

CORS_DOMAINS        = _getenv('CORS_DOMAINS',    default="localhost:\\d*")
# remove extra spaces, remove empty items
domains = filter(len, map(str.strip, CORS_DOMAINS.split(",")))
# pylint: disable=unnecessary-lambda
CORS_ORIGINS = list(map(lambda d: r'((http|https)://)?(.*\.)?{}'.format(d), domains))
