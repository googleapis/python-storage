import abc


class AsyncAbstractObjectStream(abc.ABC):
    """
    Class for both ReadObjectStream as well as WriteObjectStream.

    Attributes will include
    1. bucket_name
    2. object_name
    3. generation_number (if given)


    """

    def __init__(self, bucket_name, object_name, generation_number=None):
        super().__init__()
        self.bucket_name = bucket_name
        self.object_name = object_name
        self.generation_number = generation_number

    @abc.abstractmethod
    async def open(self):
        raise NotImplementedError("Subclasses should implement this method.")

    @abc.abstractmethod
    async def close(self):
        raise NotImplementedError("Subclasses should implement this method.")

    @abc.abstractmethod
    async def send(self):
        raise NotImplementedError("Subclasses should implement this method.")

    @abc.abstractmethod
    async def recv(self):
        raise NotImplementedError("Subclasses should implement this method.")
