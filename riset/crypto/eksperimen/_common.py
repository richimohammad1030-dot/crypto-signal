"""Muat data + replay juara (di-cache) untuk skrip eksperimen. Argumen skrip: <repo> <data_dir>."""
import os, sys, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _replay as rp

def setup():
    repo, data_dir = sys.argv[1], sys.argv[2]
    rp.load(repo, data_dir)
    cache = os.path.join(data_dir, "champ_replay.pkl")
    if os.path.exists(cache):
        champ = pickle.load(open(cache, "rb"))
    else:
        champ = rp.replay(lambda *a: True)        # kendali: gerbang selalu mengizinkan
        pickle.dump(champ, open(cache, "wb"))
    return rp, champ[0], data_dir
