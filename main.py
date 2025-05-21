import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont, ExifTags
import datetime
import os
import piexif
import pillow_heif
pillow_heif.register_heif_opener()

def get_exif_datetime(image, image_path):
    ext = image_path.lower().split('.')[-1]
    if ext in ['jpg', 'jpeg']:
        try:
            exif = image._getexif() if hasattr(image, '_getexif') else image.getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag == 'DateTimeOriginal':
                        return value.replace(':', '-', 2)
        except Exception as e:
            print("EXIF 讀取錯誤(JPG)：", e)
    elif ext in ['heic', 'heif']:
        try:
            exif_bytes = image.info.get("exif")
            if exif_bytes:
                exif_dict = piexif.load(exif_bytes)
                dt = exif_dict["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
                if dt:
                    # dt 為 bytes
                    return dt.decode().replace(':', '-', 2)
        except Exception as e:
            print("EXIF 讀取錯誤(HEIF)：", e)
    return None

def get_font_for_text(draw, text, image_width, font_path="arial.ttf", target_ratio=0.2, max_font_size=200, min_font_size=10):
    # 二分搜尋最佳字體大小
    left, right = min_font_size, max_font_size
    best_size = min_font_size
    while left <= right:
        mid = (left + right) // 2
        try:
            font = ImageFont.truetype(font_path, mid)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        if text_width / image_width < target_ratio:
            best_size = mid
            left = mid + 1
        else:
            right = mid - 1
    try:
        font = ImageFont.truetype(font_path, best_size)
    except:
        font = ImageFont.load_default()
    return font

def add_watermark(image_path, timestamp):
    image = Image.open(image_path).convert("RGBA")
    txt = Image.new("RGBA", image.size, (255,255,255,0))
    draw = ImageDraw.Draw(txt)

    # 用自動調整的字體寬度
    font = get_font_for_text(draw, timestamp, image.width)

    bbox = draw.textbbox((0, 0), timestamp, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = 10
    y = image.height - text_height - 18

    draw.rectangle([x-5, y-5, x+text_width+5, y+text_height+5], fill=(0,0,0,128))
    draw.text((x, y), timestamp, font=font, fill=(255,255,255,255))

    watermarked = Image.alpha_composite(image, txt)

    # 檢查副檔名
    ext = os.path.splitext(image_path)[1].lower()
    if ext in [".heic", ".heif", ".jpg", ".jpeg", ".gif"]:
        save_path = os.path.splitext(image_path)[0] + "_watermarked.jpg"
        watermarked = watermarked.convert("RGB")  # 轉成RGB
        watermarked.save(save_path, format="JPEG")
    else:
        save_path = os.path.splitext(image_path)[0] + "_watermarked.png"
        watermarked.convert("RGB").save(save_path)

    messagebox.showinfo("完成", f"浮水印已加上，儲存於：\n{save_path}")


def select_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.heic *.heif")]
    )
    if file_path:
        image = Image.open(file_path)
        exif_time = get_exif_datetime(image, file_path)
        if exif_time:
            time_var.set(exif_time)
        else:
            time_var.set(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        select_file.file_path = file_path  # 記錄目前的檔案路徑

def do_watermark():
    file_path = getattr(select_file, 'file_path', None)
    timestamp = time_var.get()
    if not file_path:
        messagebox.showwarning("提醒", "請先選擇圖片！")
        return
    if not timestamp:
        messagebox.showwarning("提醒", "請輸入時間！")
        return
    add_watermark(file_path, timestamp)

# Tkinter 主介面
root = tk.Tk()
root.title("圖片加時間戳 v1.0 | 安全台灣SaferTW ")
root.geometry("400x160")

frame = tk.Frame(root)
frame.pack(pady=20)

btn_select = tk.Button(frame, text="選擇圖片", command=select_file)
btn_select.grid(row=0, column=0, padx=5, pady=5)

tk.Label(frame, text="時間：").grid(row=1, column=0, padx=5, pady=5)
time_var = tk.StringVar()
entry_time = tk.Entry(frame, textvariable=time_var, width=22)
entry_time.grid(row=1, column=1, padx=5, pady=5)

btn_do = tk.Button(frame, text="加浮水印", command=do_watermark)
btn_do.grid(row=2, column=0, columnspan=2, pady=15)

root.mainloop()
