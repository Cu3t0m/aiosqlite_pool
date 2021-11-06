


class Error(Exception):
	"""
	Base Error
	"""
	pass

class PoolError(Error):
	"""
	Base Error related to the pool
	"""
	pass

class InvalidConnection(PoolError):
	"""
	raises if the connection provided is not a valid connection
	"""
	pass

class PoolClosing(PoolError):
	"""
	raises when the pool is closing and something is trying to acquire connection
	"""
	pass

class PoolClosed(PoolError):
	"""
	raises when something is trying acquire a connection while the pool is closed
	"""