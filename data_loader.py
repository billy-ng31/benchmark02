import pandas as pd
import os
import config

def clean_staff_list(staff_str):
    """
    Hàm phụ trợ để biến đổi chuỗi cán bộ 'CB028, CB045' thành list ['CB028', 'CB045']
    """
    if pd.isna(staff_str):
        return []
    # Tách bằng dấu phẩy, loại bỏ khoảng trắng thừa ở hai đầu từng mã cán bộ
    return [cb.strip() for cb in str(staff_str).split(',') if cb.strip()]

def parse_exam_datetime(date_val, time_str):
    """
    Hàm phụ trợ gộp Ngày và Giờ (dạng '18g15' hoặc '09g30') thành một đối tượng datetime chuẩn
    """
    try:
        # Chuyển đổi date_val về chuỗi định dạng YYYY-MM-DD
        date_str = pd.to_datetime(date_val).strftime('%Y-%m-%d')
        
        # Làm sạch chuỗi giờ (đổi '18g15' thành '18:15')
        time_clean = str(time_str).strip().lower().replace('g', ':')
        
        # Gộp lại và ép kiểu sang datetime
        return pd.to_datetime(f"{date_str} {time_clean}")
    except Exception:
        return pd.NaT

def load_data():
    """
    Hàm chính thực hiện nạp, làm sạch và chuẩn hóa cấu trúc dữ liệu từ các file Excel
    """
    print("[INFO] Đang nạp dữ liệu từ các file Excel...")
    
    # 1. Đọc dữ liệu thô từ Excel
    df_can_bo = pd.read_excel(config.PATH_CAN_BO)
    df_ca_thi = pd.read_excel(config.PATH_CA_THI)
    df_lich_truc = pd.read_excel(config.PATH_LICH_TRUC, sheet_name="Ca Thi")
    
    # 2. Chuẩn hóa tên cột của file Cán Bộ
    # Đổi 'MS của CÁN BỘ COI THI' hoặc các biến thể tương tự thành 'MS_CB'
    df_can_bo.columns = [col.strip() for col in df_can_bo.columns]
    df_can_bo = df_can_bo.rename(columns={
        'MS của CÁN BỘ COI THI': 'MS_CB',
        'Giới tính': 'Gioi_Tinh',
        'Tuổi': 'Tuoi',
        'Khoảng cách đến Cơ sở 1 (km)': 'KC_CS1',
        'Khoảng cách đến Cơ sở 2 (km)': 'KC_CS2'
    })
    
    # 3. Chuẩn hóa tên cột của file Ca Thi
    df_ca_thi.columns = [col.strip() for col in df_ca_thi.columns]
    df_ca_thi = df_ca_thi.rename(columns={
        'MS Ca thi': 'MS_CA',
        'Cơ sở': 'Co_So',
        'Số lượng cán bộ cần thiết': 'SL_Yeu_Cau',
        'Ngày': 'Ngay_Goc',
        'GIỜ': 'Gio_Goc',
        'Thứ': 'Thu'
    })
    
    # 4. Chuẩn hóa dữ liệu lịch trực thực tế (lich_truc_final)
    df_lich_truc.columns = [col.strip() for col in df_lich_truc.columns]
    df_lich_truc = df_lich_truc.rename(columns={
        'MS Ca thi': 'MS_CA',
        'Cơ sở': 'Co_So',
        'Danh_sách_CB_Phân_công': 'DS_Can_Bo_Raw'
    })
    
    df_lich_truc['DS_Can_Bo'] = df_lich_truc['DS_Can_Bo_Raw'].apply(clean_staff_list)
    
    # 5. Tạo Data Structure hợp nhất
    # BẮT BUỘC: Thêm 'Co_So' vào các cột cần giữ lại để mang đi merge
    cols_to_keep = ['MS_CA', 'Co_So', 'DS_Can_Bo']
    df_lich_truc_clean = df_lich_truc[cols_to_keep].copy()
    
    # SỬA DÒNG NÀY: Tiến hành merge dựa trên cả 2 điều kiện: Mã ca VÀ Cơ sở
    df_merged_lich = pd.merge(df_lich_truc_clean, df_ca_thi, on=['MS_CA', 'Co_So'], how='left')
    
    # 6. Parse thời gian chuẩn phục vụ tính toán khoảng cách ca gác liên tiếp
    df_merged_lich['Thoi_Gian_Bat_Dau'] = df_merged_lich.apply(
        lambda row: parse_exam_datetime(row['Ngay_Goc'], row['Gio_Goc']), axis=1
    )
    
    # Tính thêm thời gian kết thúc (mỗi ca mặc định kéo dài 150 phút = 2.5 giờ theo file gốc)
    df_merged_lich['Thoi_Gian_Ket_Thuc'] = df_merged_lich['Thoi_Gian_Bat_Dau'] + pd.to_timedelta(150, unit='m')
    
    print(f"[SUCCESS] Đã xử lý xong dữ liệu.")
    print(f"          - Số lượng cán bộ hệ thống: {len(df_can_bo)}")
    # Trả về các DataFrame sạch cho các module sau sử dụng
    return df_can_bo, df_ca_thi, df_merged_lich

# Khối lệnh chạy thử nghiệm độc lập để debug module 2 nếu cần
if __name__ == "__main__":
    # Đảm bảo bạn đứng ở thư mục gốc iap_benchmark khi chạy lệnh test này
    cb, ca, lich = load_data()
    print("\n--- TEST DỮ LIỆU CÁN BỘ VỪA LÀM SẠCH ---")
    print(cb[['MS_CB', 'Gioi_Tinh', 'Tuoi']].head(3))
    print("\n--- TEST FILE LỊCH ĐÃ MERGE VÀ PARSE DATETIME ---")
    print(lich[['MS_CA', 'Co_So', 'Thoi_Gian_Bat_Dau', 'DS_Can_Bo']].head(3))