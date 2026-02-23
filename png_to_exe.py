import os
import shutil
import subprocess
from pathlib import Path

# Thư mục chứa ảnh PNG
image_folder = Path(r"D:\StickmanGame")  # sửa đường dẫn theo bạn

# Thư mục tạm để tạo script
temp_folder = image_folder / "temp_build"
temp_folder.mkdir(exist_ok=True)

# Lặp qua tất cả ảnh PNG trong folder
for img_file in image_folder.glob("*.png"):
    name_stem = img_file.stem  # tên file không có .png
    print(f"Đang tạo EXE cho: {img_file.name}")

    # Tạo script Python riêng cho mỗi ảnh
    script_file = temp_folder / f"{name_stem}.py"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(f"""
import sys
from pathlib import Path
from PIL import Image

# Lấy đường dẫn ảnh
if getattr(sys, 'frozen', False):
    img_path = Path(sys.executable).with_suffix('.png')
else:
    img_path = Path(__file__).with_suffix('.png')

img = Image.open(img_path)
img.show()
input("Nhấn Enter để đóng...")  # giữ cửa sổ mở
""")

    # Copy ảnh sang temp folder, trùng tên với script
    shutil.copy(img_file, temp_folder / img_file.name)

    # Chạy PyInstaller để tạo EXE
    subprocess.run([
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", name_stem,
        str(script_file)
    ], cwd=temp_folder)

    # Copy EXE ra thư mục chính
    exe_path = temp_folder / "dist" / f"{name_stem}.exe"
    if exe_path.exists():
        shutil.copy(exe_path, image_folder / exe_path.name)

# Dọn dẹp thư mục temp nếu muốn
shutil.rmtree(temp_folder)
print("Hoàn tất tất cả EXE!")
