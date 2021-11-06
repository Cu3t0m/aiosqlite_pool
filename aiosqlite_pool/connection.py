import aiosqlite
import asyncio

class Connection(aiosqlite.Connection):
    def __init__(self,*args,**kwargs):
        if "pool" in kwargs:
            self._pool = kwargs.pop("pool")
        super().__init__(*args,**kwargs)
    
    async def close(self):
        """
        closes the connection and releasing the connection
        from the pool
        """
        self._pool.release(self)
        await super().close()
         
    async def release(self):
        """
        an alias for close()
        """
        await self.close()