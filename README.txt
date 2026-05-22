```python
readme_content = """# Hệ thống Benchmark & Đánh giá Lịch Coi Thi (HCMUT)

Dự án này là công cụ hỗ trợ phân tích, đánh giá chất lượng lịch xếp ca thi tự động dựa trên các ràng buộc cứng (Hard Constraints) và ràng buộc mềm (Soft Constraints), tích hợp giao diện Web Dashboard chuyên nghiệp bằng Streamlit.

## 🚀 Tính năng chính
- **Đánh giá tự động:** Kiểm tra tính hợp lệ của lịch dựa trên yêu cầu học thuật.
- **Phân tích Soft Constraints:** Tính toán điểm phạt dựa trên độ công bằng, quãng đường, thời gian nghỉ và các yêu cầu thực tế.
- **Dashboard trực quan:** Giao diện Web tương tác, xem nhanh tổng quan lỗi và phân tích chi tiết.
- **Xuất báo cáo:** Hỗ trợ xem Log chi tiết và tải xuống dữ liệu báo cáo.

## 📂 Cấu trúc dự án
```text
benchmark/
├── .venv/                # Môi trường ảo (Virtual Environment)
├── data/                 # Thư mục chứa các file Excel đầu vào
├── output/               # Thư mục chứa các báo cáo kết quả
├── app.py                # File giao diện Web chính (Streamlit)
├── data_loader.py        # Module đọc và xử lý dữ liệu Excel
├── hard_constraints.py   # Logic kiểm tra ràng buộc cứng
├── soft_constraints.py   # Logic tính toán điểm phạt (Soft)
├── config.py             # Cấu hình trọng số và tham số hệ thống
└── README.md             # Tài liệu hướng dẫn này

```

## 🛠 Cách thiết lập & Chạy dự án

### 1. Yêu cầu cài đặt

* Python 3.x
* Cài đặt các thư viện cần thiết:
```bash
pip install streamlit pandas openpyxl

```

```markdown
## 🛠 Cách thiết lập & Chạy dự án

### 1. Thiết lập môi trường ảo (Virtual Environment)
Khuyến nghị thiết lập môi trường ảo để tránh xung đột thư viện với các dự án khác trên máy.
- **Bước 1:** Mở Terminal tại thư mục `benchmark/` và tạo môi trường ảo:
  ```bash
  python -m venv .venv

```

* **Bước 2:** Kích hoạt môi trường ảo (Terminal sẽ hiện `(.venv)` ở đầu dòng):
* Trên Windows (PowerShell/VS Code):
```bash
.\.venv\Scripts\Activate.ps1

```


* Trên macOS/Linux:
```bash
source .venv/bin/activate

```




* **Bước 3:** Cài đặt các thư viện bắt buộc vào môi trường ảo:
```bash
python -m pip install pandas openpyxl streamlit

```



### 2. Cách chạy chương trình

Dự án hỗ trợ 2 chế độ hoạt động tùy theo nhu cầu sử dụng của bạn:

**Cách 1: Chạy ngầm qua Terminal (Chế độ CLI)**
Phù hợp để kỹ thuật viên kiểm tra nhanh hệ thống, in lỗi trực tiếp trên màn hình đen và tự động xuất file log.

* Mở Terminal (đã kích hoạt `.venv`) và chạy lệnh:
```bash
python main.py

```


* *Kết quả:* Điểm số sẽ in ra Terminal, đồng thời xuất file `Bao_Cao_Benchmark.xlsx` và `Benchmark_Log.txt` vào thư mục `output/`.

**Cách 2: Chạy giao diện Web tương tác (Chế độ Streamlit)**
Phù hợp để demo, báo cáo trực quan cho người dùng cuối với các biểu đồ và thao tác click dễ dàng.

* Mở Terminal (đã kích hoạt `.venv`) và chạy lệnh:
```bash
streamlit run app.py

```


* *Kết quả:* Trình duyệt sẽ tự động mở trang web tại địa chỉ `http://localhost:8501`. Bạn có thể upload file và xem lỗi chi tiết trực tiếp trên giao diện này.

```

Phần **`## ⚙️ Hướng dẫn sử dụng`** và các phần bên dưới của bạn đã rất ổn, bạn cứ giữ nguyên không cần thay đổi gì thêm.

```


4. Truy cập địa chỉ `http://localhost:8501` trên trình duyệt để sử dụng.

## ⚙️ Hướng dẫn sử dụng

1. **Upload dữ liệu:** Tại sidebar, tải lên file `can_bo.xlsx`, `ca_thi.xlsx` và `Ket_Qua_Xep_Lich.xlsx`.
2. **Benchmark:** Nhấn nút **"🚀 Chạy Đánh Giá"**.
3. **Xem kết quả:**
* **Dashboard:** Kiểm tra điểm phạt và các biểu đồ phân tích lỗi.
* **Chi tiết:** Sử dụng các tab để xem cụ thể lỗi ở từng loại ràng buộc.
* **Log:** Xem chi tiết log vi phạm và tải về file `.txt` để lưu trữ.
