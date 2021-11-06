from .connection import Connection
from .exceptions import *
import sqlite3
from .pool import Pool

__author__='RouterGTX'
__all__ = (
	'Pool',
	'Error',
	'PoolError',
	'InvalidConnection',
	'PoolClosing',
)

def _connect(database,iter_chunk_size=64,**kwargs):
    
    def connector():
        if isinstance(database, str):
            loc = database
        elif isinstance(database, bytes):
            loc = database.decode("utf-8")
        else:
            loc = str(database)
        return sqlite3.connect(loc,**kwargs)
 
    return Connection(connector,iter_chunk_size)