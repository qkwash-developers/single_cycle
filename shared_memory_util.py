import mmap
import posix_ipc
import struct

# A dictionary to store shared memory objects
shared_memory_objects = {}

def create_shared_memory(name, size):
    """
    Create shared memory object for the given name and size (in bytes).
    If the shared memory already exists, open it; otherwise, create it.
    """
    try:
        # If shared memory does not exist, create it
        shm = posix_ipc.SharedMemory(name, flags=posix_ipc.O_CREX, size=size)
        shared_memory_objects[name] = shm
    except posix_ipc.ExistentialError:
        # If it exists, just open it
        shm = posix_ipc.SharedMemory(name)
        shared_memory_objects[name] = shm

    return shm

def write_data_to_shared_memory(name, data):
    """
    Write data to shared memory using the given name.
    Data will be packed into bytes before writing.
    """
    # Get the shared memory object by name
    shm = shared_memory_objects.get(name)
    if not shm:
        # If the shared memory object is not already created, create it
        shm = create_shared_memory(name, 4)

    byte_data = struct.pack('f', data)  # Pack data as a float
    with mmap.mmap(shm.fd, shm.size) as mem:
        mem.seek(0)  # Seek to the start of shared memory
        mem.write(byte_data)

def read_data_from_shared_memory(name):
    """
    Read data from shared memory using the given name.
    It assumes the data is packed as a float.
    """
    # Get the shared memory object by name
    shm = shared_memory_objects.get(name)
    if not shm:
        # If the shared memory object is not already created, create it
        shm = create_shared_memory(name, 4)

    with mmap.mmap(shm.fd, shm.size) as mem:
        mem.seek(0)  # Seek to the start of shared memory
        byte_data = mem.read(4)  # Read 4 bytes
        data = struct.unpack('f', byte_data)[0]  # Unpack as a float
        return data

def modify_shared_memory(name, modify_func):
    """
    Read current value from shared memory, modify it using the provided function,
    and write it back to shared memory.
    """
    current_data = read_data_from_shared_memory(name)
    modified_data = modify_func(current_data)
    write_data_to_shared_memory(name, modified_data)

def cleanup_shared_memory():
    """
    Cleanup all shared memory objects created in this program.
    This should be called before the program exits to release resources.
    """
    for name, shm in shared_memory_objects.items():
        try:
            shm.unlink()  # Unlink the shared memory object
        except Exception as e:
            print(f"Error cleaning up shared memory '{name}': {e}")
