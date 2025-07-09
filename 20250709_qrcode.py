import qrcode
from PIL import Image, ImageDraw, ImageFont
import sys
import os

# 1. QRコードにする文字列を聞く
def get_qr_data():
    for i in range(2):
        data = input("QRコードにしたい文字列を入力してください: ").strip()
        if data:
            return data
        else:
            if i == 0:
                print("文字列が入力されていません。もう一度入力してください。")
    print("文字列が入力されなかったので、プログラムを終了します。")
    sys.exit()

# 3. 中央に表示する文字列を聞く
def get_center_text():
    max_length = 20  # 目安の最大文字数
    for i in range(2):
        text = input(f"QRコード中央に表示したい文字列を入力してください（最大{max_length}文字程度）: ").strip()
        if not text:
            return None
        if len(text) <= max_length:
            return text
        else:
            print(f"文字列が長すぎます（{len(text)}文字）。最大{max_length}文字程度にしてください。")
    print("文字列が長すぎたので、そのまま表示しますが、必要なら自動で改行します。")
    return text

# OSにありそうなフォントを順に探す
def get_japanese_font(size=40):
    candidate_paths = [
        # Windows
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/msgothic.ttc",
        # macOS
        "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
        "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc",
        # Linux例
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    for path in candidate_paths:
        if os.path.exists(path):
            print(f"使用フォント: {path}")
            return ImageFont.truetype(path, size=size)

    print("日本語フォントが見つからなかったので標準フォントを使います（日本語は表示できない可能性あり）")
    return ImageFont.load_default()

# テキストをできるだけ改行せずに分割
def split_text_to_fit(draw, text, font, max_width):
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
    return lines

# メイン処理
def main():
    data = get_qr_data()
    center_text = get_center_text()

    # QRコード生成
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # ロゴ・文字乗せ用に高め
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    if center_text:
        draw = ImageDraw.Draw(img)
        font = get_japanese_font(size=40)

        # QR画像の幅に合わせて自動改行
        img_width, img_height = img.size
        max_text_width = img_width * 0.8  # 幅の80%以内にする

        lines = split_text_to_fit(draw, center_text, font, max_text_width)

        # 行サイズ計算
        line_sizes = [draw.textbbox((0, 0), line, font=font) for line in lines]
        line_heights = [bbox[3] - bbox[1] for bbox in line_sizes]
        line_widths = [bbox[2] - bbox[0] for bbox in line_sizes]

        text_width = max(line_widths)
        text_height = sum(line_heights) + (len(lines) - 1) * 5

        # 背景の四角
        padding = 10
        position_x = (img_width - text_width) // 2
        position_y = (img_height - text_height) // 2
        rect_start = (position_x - padding, position_y - padding)
        rect_end = (position_x + text_width + padding, position_y + text_height + padding)
        draw.rectangle([rect_start, rect_end], fill="white")

        # 行を順に描画
        y_offset = position_y
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (img_width - line_width) // 2
            draw.text((x, y_offset), line, fill="black", font=font)
            y_offset += line_heights[i] + 5

    img.save("qrcode.png")
    print("QRコードを 'qrcode.png' として保存しました！")

if __name__ == "__main__":
    main()
