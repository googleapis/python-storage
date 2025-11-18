import asyncio

# Ensure there's an event loop in the main thread so grpc.aio.create_channel
# and other code that expects a loop at import/initialization time don't fail.
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
