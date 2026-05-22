import os

# ==========================================
# CẤU HÌNH ĐƯỜNG DẪN VÀ TÊN FILE DỮ LIỆU
# ==========================================
# Khai báo đường dẫn tương đối đến thư mục data
DATA_DIR = "data"

# Khai báo tên các file Excel đầu vào
FILE_CAN_BO = "can_bo.xlsx"
FILE_CA_THI = "ca_thi.xlsx"
FILE_LICH_TRUC = "Ket_Qua_Xep_Lich.xlsx"

# Tạo đường dẫn tuyệt đối (an toàn hơn khi chạy code từ các thư mục khác nhau)
PATH_CAN_BO = os.path.join(DATA_DIR, FILE_CAN_BO)
PATH_CA_THI = os.path.join(DATA_DIR, FILE_CA_THI)
PATH_LICH_TRUC = os.path.join(DATA_DIR, FILE_LICH_TRUC)

# ==========================================
# CẤU HÌNH TRỌNG SỐ ĐIỂM PHẠT (PENALTIES)
# ==========================================
# Trọng số càng cao thể hiện tiêu chí càng quan trọng. 
# Lịch trình tốt là lịch trình có tổng điểm phạt càng thấp.

WEIGHT_FAIRNESS = 1                 # Phạt nếu số ca trực chênh lệch so với mức trung bình
WEIGHT_DISTANCE = 0.1                 # Phạt dựa trên tổng khoảng cách di chuyển
WEIGHT_SAME_DAY_DIFF_FACILITY = 1   # Phạt nếu gác >2 ca/ngày mà phải di chuyển 2 cơ sở khác nhau
WEIGHT_MIN_SHIFT = 1                # Phạt nếu có cán bộ không được gác ca nào (số ca = 0)
WEIGHT_CONSECUTIVE_SHIFTS = 1       # Phạt nếu 2 ca xếp quá gần nhau (thời gian nghỉ ngắn)
WEIGHT_AGE_PRIORITY = 1             # Phạt nếu xếp nhiều ca cho người lớn tuổi (>45 tuổi)
WEIGHT_PARTNER_DIVERSITY = 1        # Phạt nếu 2 người gác chung với nhau quá nhiều lần
WEIGHT_WEEKEND = 1                  # Phạt nếu phải gác vào ngày nghỉ (Thứ 7, Chủ Nhật)
WEIGHT_GENDER_BALANCE = 0.1           # Phạt nếu số lượng nữ gác quá nhiều

# ==========================================
# CÁC HẰNG SỐ LOGIC KHÁC (Tùy chọn)
# ==========================================
AGE_THRESHOLD = 45                  # Ngưỡng tuổi để tính ưu tiên
MIN_REST_HOURS = 3                  # Thời gian nghỉ tối thiểu giữa 2 ca (đơn vị: giờ)
MAX_PARTNER_REPETITION = 4          # Số lần tối đa 2 người được gác chung trước khi bị phạt