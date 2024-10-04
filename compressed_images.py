from PIL import Image
import heapq
import collections
import psycopg2
import time

# Đường dẫn đến ảnh
image_path = r'C:\Users\HP\Downloads\LE07_L2SP_125052_20181226_20200827_02_T1\LE07_L2SP_125052_20181226_20200827_02_T1_SR_B2.TIF'

# Hàm xây dựng cây Huffman
def build_huffman_tree(data):
    frequency = collections.Counter(data)
    heap = [[weight, [symbol, ""]] for symbol, weight in frequency.items()]
    heapq.heapify(heap)
    
    while len(heap) > 1:
        lo = heapq.heappop(heap)
        hi = heapq.heappop(heap)
        for pair in lo[1:]:
            pair[1] = '0' + pair[1]
        for pair in hi[1:]:
            pair[1] = '1' + pair[1]
        heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
    
    return sorted(heapq.heappop(heap)[1:], key=lambda p: (len(p[-1]), p))

# Hàm mã hóa dữ liệu ảnh bằng cây Huffman
def huffman_encoding(data, huffman_tree):
    huff_dict = {symbol: code for symbol, code in huffman_tree}
    return ''.join(huff_dict[symbol] for symbol in data)

# Hàm giải mã 
def huffman_decoding(encoded_data, huffman_tree):
    reverse_huff_dict = {code: symbol for symbol, code in huffman_tree}
    decoded_data = []
    code = ""
    for bit in encoded_data:
        code += bit
        if code in reverse_huff_dict:
            decoded_data.append(reverse_huff_dict[code])
            code = ""
    return decoded_data

# Đọc ảnh bằng Pillow
try:
    with Image.open(image_path) as img:
        img = img.convert("L")  # Chuyển ảnh sang thang độ xám (1 kênh)
        pixel_data = list(img.getdata())

        # Bắt đầu tính toán thời gian nén
        start_time = time.time()

        # Xây dựng cây Huffman và mã hóa ảnh
        huffman_tree = build_huffman_tree(pixel_data)
        encoded_data = huffman_encoding(pixel_data, huffman_tree)

        # Tính toán thời gian nén
        end_time = time.time()
        compression_time = end_time - start_time  # Thời gian nén (giây)

        # Tính toán kích thước sau khi nén
        compressed_size = len(encoded_data) // 8  # Kích thước sau nén (tính theo byte)

        # Kết nối đến PostgreSQL
        conn = psycopg2.connect(
            dbname="mydb",
            user="postgres",
            password="1234",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()

        # Chèn dữ liệu vào bảng
        cur.execute("""
            INSERT INTO compressed_images (image_data, compression_time, compressed_size)
            VALUES (%s, %s, %s);
        """, (psycopg2.Binary(bytes(encoded_data, 'utf-8')), compression_time, compressed_size))

        # Commit và đóng kết nối
        conn.commit()
        cur.close()
        conn.close()

        print(f"Dữ liệu ảnh đã được nén và lưu vào cơ sở dữ liệu bằng Huffman coding.")
        print(f"Thời gian nén: {compression_time:.4f} giây")
        print(f"Dung lượng sau nén: {compressed_size} byte")

except IOError:
    print(f"Không thể mở ảnh từ đường dẫn: {image_path}")