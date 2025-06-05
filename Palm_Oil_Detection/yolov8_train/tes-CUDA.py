import torch
print(torch.version.cuda)  # Harusnya ada versi, misal '11.8'
print(torch.cuda.is_available())  # Harusnya True jika GPU CUDA tersedia dan PyTorch bisa pakai
print(torch.__version__)
