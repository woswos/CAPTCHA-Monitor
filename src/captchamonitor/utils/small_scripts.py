import pickle

# Deep copies objects
deep_copy = lambda obj: pickle.loads(pickle.dumps(obj))
