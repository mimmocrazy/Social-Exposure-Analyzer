import os
import warnings
import easyocr
from backend.core.logger import logger

# Ignora i fastidiosi warning di PyTorch sull'uso della CPU al posto della GPU
warnings.filterwarnings("ignore", category=UserWarning, module="torch.utils.data.dataloader")

_reader = None

def get_reader():
    """Carica EasyOCR in modalità lazy per ridurre il memory footprint."""
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['it', 'en'], gpu=False)
    return _reader

def extract_text_from_image(image_path: str) -> str:
    """
    Processa l'immagine per estrarre testo in chiaro (es. da screenshot o foto profilo).
    Gestisce la cancellazione sicura post-analisi.
    """
    extracted_text = ""
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Immagine non trovata: {image_path}")
            
        reader = get_reader()
        results = reader.readtext(image_path, detail=0)
        extracted_text = " ".join(results)
        
    except Exception as e:
        # A04: Insecure Design - Logging critico se l'elaborazione fallisce (Possibile Evasione Anti-OCR)
        logger.critical(f"A04: Insecure Design - Estrazione OCR fallita per {image_path}. Potenziale evasione, steganografia o immagine corrotta. Errore: {e}")
        
    finally:
        # Sicurezza: Elimina il file per prevenire storage di materiale PII non autorizzato (Data Leak)
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError as cleanup_error:
                logger.error(f"Impossibile cancellare file OCR temporaneo {image_path}: {cleanup_error}")
                
    return extracted_text
