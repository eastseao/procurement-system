from PIL import Image, ImageDraw
assets = r'I:\采购管理系统\采购管理系统V2.3.1\assets'
sz = 64
c = (123, 165, 181)

# 线性版
img = Image.new('RGBA', (sz, sz), (0,0,0,0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([12,6,52,32], radius=5, outline=c, width=2)
d.line([20,14,44,14], fill=c, width=2)
d.line([14,42,50,42], fill=c, width=2)
d.line([14,50,50,50], fill=c, width=2)
d.line([14,58,42,58], fill=c, width=2)
img.save(assets + '/nav