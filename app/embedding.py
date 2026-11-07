from functools import cached_property
from app.config import Settings

class Embedder:
    def __init__(self, cfg: Settings): self.cfg = cfg
    @cached_property
    def model(self):
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(self.cfg.embedding_model, revision=self.cfg.embedding_revision, device=self.cfg.embedding_device)
        model.max_seq_length = min(model.max_seq_length, 512)
        return model
    @property
    def tokenizer(self): return self.model.tokenizer
    def count(self, text): return len(self.tokenizer.encode(text, add_special_tokens=True))
    def encode(self, texts, kind="passage"):
        prefixed = [f"{kind}: {t}" for t in texts]
        for t in prefixed:
            if self.count(t) > self.model.max_seq_length:
                raise ValueError("Embedding input exceeds model limit; split it before encoding.")
        return self.model.encode(prefixed, normalize_embeddings=True, batch_size=16, show_progress_bar=kind=="passage").tolist()
    def identity(self):
        commit = getattr(self.model[0].auto_model.config, "_commit_hash", None)
        if not commit:
            from huggingface_hub import try_to_load_from_cache
            from pathlib import Path
            cached=try_to_load_from_cache(self.cfg.embedding_model,"config.json",revision=self.cfg.embedding_revision)
            if isinstance(cached,str): commit=Path(cached).parent.name
        return {"model":self.cfg.embedding_model, "revision":self.cfg.embedding_revision, "resolved_revision":commit,
                "dimensions":self.model.get_sentence_embedding_dimension(), "normalized":True, "metric":"cosine",
                "max_tokens":self.model.max_seq_length, "preprocessing":"arabic-v2", "chunk_tokens":self.cfg.chunk_tokens,
                "overlap":self.cfg.chunk_overlap}
