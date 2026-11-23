import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "audit"))
# H9: import HF first
from tokenizers import Tokenizer as HFTokenizer  # noqa
import common
# patch target
common.EXISTING_TARGET_BYTES = 200000
from prepare_corpus import collect_existing, store_domain
docs = collect_existing("web", refresh=False)
stats = store_domain("web", docs, 9999, 50)
print(stats)
