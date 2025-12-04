try:
    import onnxruntime as ort
    ONNXRUNTIME_AVAILABLE = True
except ImportError:
    ONNXRUNTIME_AVAILABLE = False
    ort = None

def get_gpu_info():
    """
    Returns a tuple (is_available, device_name)
    """
    if not ONNXRUNTIME_AVAILABLE:
        # Fallback: check for CUDA via torch if available
        try:
            import torch
            if torch.cuda.is_available():
                return True, f"NVIDIA CUDA ({torch.cuda.get_device_name(0)})"
        except:
            pass
        return False, "CPU Mode"
    
    providers = ort.get_available_providers()
    
    if 'CUDAExecutionProvider' in providers:
        return True, "NVIDIA CUDA"
    elif 'DmlExecutionProvider' in providers:
        return True, "DirectML (Windows)"
    elif 'CoreMLExecutionProvider' in providers:
        return True, "CoreML (macOS)"
    else:
        return False, "CPU Mode"
