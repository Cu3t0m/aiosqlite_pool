import aiosqlite
import asyncio
import aiosqlite_pool
from .exceptions import PoolError, InvalidConnection, PoolClosing, PoolClosed

class ConnectionContextManager:
    def __init__(self,pool,timeout):
        self.conn = None
        self.pool = pool
        self.timeout = timeout
        self.done = False

    async def __aenter__(self):
        if not self.conn is None or self.done:
            raise PoolError('connection is already acquired')
        self.conn = await self.pool._acquire(self.timeout)
        return self.conn

    async def __aexit__(self,*args):
        self.done = True
        conn = self.conn
        self.conn = None
        await conn.close()

    def __await__(self):
        self.done = True
        return self.pool._acquire.__await__()
 
class Pool:
    def __init__(self,database,max_connection=5,*args,**kwargs):
        self._database = database
        self._max_connection = max_connection
        self.__args = [args,kwargs]
        self._connections = []
        self._waiters = []
        self._loop = asyncio.get_event_loop()
        self._closing = False
        self._closed = False

    async def _acquire(self,timeout):
        if self._closed:
            raise PoolClosed("pool is closed")
        if self._closing:
            raise PoolClosing("pool is closing")
        args,kwargs = self.__args
        if len(self._connections) >= self._max_connection:
            fut = self._loop.create_future()
            self._waiters.append(fut)
            if timeout > 0:
                try:
                    await asyncio.wait_for(fut,timeout=timeout)
                except asyncio.CancelledError as e:
                    if self._closing:
                        raise PoolClosing('pool is closing')
                    raise e
            else:
                try:
                    await fut
                except asyncio.CancelledError as e:
                    if self._closing:
                        raise PoolClosing('pool is closing')
                    raise e
        conn_task = self._loop.create_future()
        conn = aiosqlite_pool._connect(self._database,*args,**kwargs)
        conn._pool_task = conn_task
        conn._pool = self
        self._connections.append(conn)
        return await conn

    def closed(self):
        """
        return True if pool is closed, else False
        """
        return self._closed

    def is_closing(self):
        """
        return True if pool is closing, else False
        """
        return self._closing
    
    def acquire(self,*,timeout=0):
        """
        acquire a connection from the pool, if connections from the pool 
        has hit max_connections
        this function will wait until a connection is released

        parameters:
            `timeout[float]` raises `asyncio.TimeoutError` if timed out 
            while waiting for an open connection,
            if timeout is lower than 0 there is no timeout

        return `ConnectionContextManager`
        """
        ctx = ConnectionContextManager(self,timeout)
        return ctx

    def release(self,conn):
        """
        releases a connection from the pool, this will raise `aiosqlite_pool.exceptions.InvalidConnection` 
        if connection provided doesn't belong to the pool

        parameters:
            `conn[Connection]` the connection to release
        """
        if self._closed:
            raise PoolClosed("pool is closed")
        if not conn in self._connections:
            raise InvalidConnection("connection {} not connected to pool".format(conn))

        try:
            waiter = next(iter(self._waiters))
            if not waiter.done():
                waiter.set_result(True)
            self._waiters.remove(waiter)
        except StopIteration:
            pass
        if not conn._pool_task.done():
            conn._pool_task.set_result(True)
        self._connections.remove(conn)

    async def close(self):
        """
        close the pool and wait until every connection is released,
        any waiter will be cancelled 
        """
        if self._closed:
            return
        self._closing = True
        for waiter in self._waiters:
            waiter.cancel()
        await asyncio.gather(*[i._pool_task for i in self._connections])
        
        self._closing = False
        self._closed = True

    async def terminate(self):
        """
        forcefully closes the pool by releasing the connection,
        ignoring the state of it and cancelling every waiter 
        """
        if self._closed:
            return
        self._closing = True
        for waiter in self._waiters:
            waiter.cancel()

        for conn in self._connections:
            await conn.close()
        
        self._closing = False
        self._closed = True