from sentence_transformers import SentenceTransformer, util

from PIL import Image

class AIComparator:
    def __init__(self):
        self.model = SentenceTransformer('clip-ViT-B-32')
    
    def hitung_vektor(self, image_path):
        """Ubah gambar jadi angka(vektor)"""
        try:
            img = Image.open(image_path)
            return self.model.encode(img)
        except Exception as e:
            print(f"Error AI Encoding: {e}")
            return None
    
    def bandingkan_vektor(self,vektor1,vektor2):
        """Hitung persentase kemiripan konteks (angle berbeda)"""
        if vektor1 is None or vektor2 is None:
            return 0.0
        
        score = util.cos_sim(vektor1,vektor2).item() * 100
        return max(0, min(100, score))