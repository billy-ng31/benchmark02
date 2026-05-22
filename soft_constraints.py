import pandas as pd
import itertools
from collections import Counter
import config

def evaluate_soft_constraints(df_can_bo, df_ca_thi, df_lich_truc):
    """
    Tính toán điểm phạt (Penalty) dựa trên các ràng buộc mềm.
    Trả về (Tổng điểm, Chi tiết từng hạng mục)
    """
    print("[INFO] Đang tính toán điểm phạt (Soft Constraints)...")
    
    report = {}
    total_penalty = 0
    
    # =========================================================================
    # TIỀN XỬ LÝ: Tạo bảng dữ liệu trải phẳng (Flattened Data)
    # =========================================================================
    # 1. Trải phẳng danh sách cán bộ
    df_flat = df_lich_truc.explode('DS_Can_Bo').rename(columns={'DS_Can_Bo': 'MS_CB'})
    df_flat = df_flat.dropna(subset=['MS_CB'])
    
    # 2. Map thông tin từ file Cán bộ (Tuổi, Giới tính, Khoảng cách) vào df_flat
    df_flat = pd.merge(df_flat, df_can_bo, on='MS_CB', how='left')
    
    # Đếm số ca của từng người (Series)
    shift_counts = df_flat['MS_CB'].value_counts()
    
    # Chỉ số cơ bản
    total_shifts = len(df_flat)
    total_staff = len(df_can_bo)
    mu = total_shifts / total_staff if total_staff > 0 else 0

    # =========================================================================
    # RB8 (9đ): Công bằng - Độ lệch so với trung bình (mu)
    # =========================================================================
    # Tính số ca cho cả những người = 0 (bằng cách reindex)
    all_shift_counts = shift_counts.reindex(df_can_bo['MS_CB'], fill_value=0)
    
    total_deviation = abs(all_shift_counts - mu).sum()
    penalty_rb8 = total_deviation * config.WEIGHT_FAIRNESS
    
    total_penalty += penalty_rb8
    report['RB8_CongBang'] = {
        'score': round(penalty_rb8, 2), 
        'details': f"Tổng độ lệch: {round(total_deviation, 2)} ca (Trung bình mu = {round(mu, 2)})"
    }

    # =========================================================================
    # RB3 (6đ): Ít nhất 1 ca - Bỏ sót người
    # =========================================================================
    staff_with_zero_shifts = (all_shift_counts == 0).sum()
    penalty_rb3 = staff_with_zero_shifts * config.WEIGHT_MIN_SHIFT
    
    total_penalty += penalty_rb3
    report['RB3_ItNhat1Ca'] = {
        'score': penalty_rb3,
        'details': f"Có {staff_with_zero_shifts} cán bộ không được phân công ca nào."
    }

    # =========================================================================
    # RB7 (8đ): Khoảng cách di chuyển
    # =========================================================================
    def get_distance(row):
        if row['Co_So'] == 'Cơ sở 1': return row['KC_CS1']
        if row['Co_So'] == 'Cơ sở 2': return row['KC_CS2']
        return 0

    df_flat['Khoang_Cach_Ca'] = df_flat.apply(get_distance, axis=1)
    total_distance = df_flat['Khoang_Cach_Ca'].sum()
    penalty_rb7 = total_distance * config.WEIGHT_DISTANCE
    
    total_penalty += penalty_rb7
    report['RB7_KhoangCach'] = {
        'score': round(penalty_rb7, 2),
        'details': f"Tổng quãng đường di chuyển: {round(total_distance, 2)} km."
    }

    # =========================================================================
    # RB9 (7đ): Cùng cơ sở nếu gác nhiều ca/ngày
    # =========================================================================
    penalty_rb9 = 0
    rb9_violations = 0
    grouped_daily = df_flat.groupby(['MS_CB', 'Ngay_Goc'])
    
    for (cb, date), group in grouped_daily:
        if len(group) >= 2:
            unique_facilities = group['Co_So'].nunique()
            if unique_facilities > 1:
                rb9_violations += 1
                penalty_rb9 += config.WEIGHT_SAME_DAY_DIFF_FACILITY
                
    total_penalty += penalty_rb9
    report['RB9_NhieuCaCungNgayKhacCoSo'] = {
        'score': penalty_rb9,
        'details': f"Vi phạm {rb9_violations} lần (gác >= 2 ca/ngày nhưng phải chạy khác cơ sở)."
    }

    # =========================================================================
    # RB11 (5đ): Tránh 2 ca quá gần nhau (nghỉ < 2 tiếng)
    # =========================================================================
    penalty_rb11 = 0
    rb11_violations = 0
    
    # Sort data lại theo thời gian để so sánh ca trước/sau
    df_sorted = df_flat.sort_values(by=['MS_CB', 'Ngay_Goc', 'Thoi_Gian_Bat_Dau'])
    grouped_sorted = df_sorted.groupby(['MS_CB', 'Ngay_Goc'])
    
    for (cb, date), group in grouped_sorted:
        if len(group) >= 2:
            shifts = group.to_dict('records')
            for i in range(1, len(shifts)):
                prev_end = shifts[i-1]['Thoi_Gian_Ket_Thuc']
                curr_start = shifts[i]['Thoi_Gian_Bat_Dau']
                
                # Tính khoảng cách nghỉ (giờ)
                rest_gap = (curr_start - prev_end).total_seconds() / 3600.0
                if rest_gap < config.MIN_REST_HOURS:
                    rb11_violations += 1
                    penalty_rb11 += config.WEIGHT_CONSECUTIVE_SHIFTS

    total_penalty += penalty_rb11
    report['RB11_NghiNgoiChuaDu'] = {
        'score': penalty_rb11,
        'details': f"Vi phạm {rb11_violations} lần (thời gian nghỉ giữa 2 ca < {config.MIN_REST_HOURS} tiếng)."
    }

    # =========================================================================
    # RB6 (4đ): Ưu tiên người lớn tuổi (> 45 tuổi không nên gác nhiều hơn mu)
    # =========================================================================
    penalty_rb6 = 0
    rb6_violations = 0
    
    for cb_row in df_can_bo.to_dict('records'):
        if cb_row['Tuoi'] > config.AGE_THRESHOLD:
            cb_id = cb_row['MS_CB']
            ca_thuc_te = all_shift_counts.get(cb_id, 0)
            if ca_thuc_te > mu:
                extra_shifts = ca_thuc_te - mu
                rb6_violations += 1
                penalty_rb6 += extra_shifts * config.WEIGHT_AGE_PRIORITY
                
    total_penalty += penalty_rb6
    report['RB6_UuTienNguoiLonTuoi'] = {
        'score': round(penalty_rb6, 2),
        'details': f"Có {rb6_violations} cán bộ >{config.AGE_THRESHOLD}t bị xếp quá số ca trần."
    }

    # =========================================================================
    # RB13 (3đ): Đa dạng cộng sự (Hạn chế 2 người gác chung >= 3 lần)
    # =========================================================================
    all_pairs = []
    for ds in df_lich_truc['DS_Can_Bo']:
        if len(ds) >= 2:
            # Sắp xếp để cặp (A, B) và (B, A) được tính là một
            sorted_ds = sorted(ds)
            all_pairs.extend(itertools.combinations(sorted_ds, 2))
            
    pair_counts = Counter(all_pairs)
    frequent_pairs = {pair: count for pair, count in pair_counts.items() if count >= config.MAX_PARTNER_REPETITION + 1}
    
    rb13_violations = len(frequent_pairs)
    penalty_rb13 = rb13_violations * config.WEIGHT_PARTNER_DIVERSITY
    
    total_penalty += penalty_rb13
    report['RB13_DaDangCongSu'] = {
        'score': penalty_rb13,
        'details': f"Có {rb13_violations} cặp đôi phải gác chung với nhau >= 3 lần."
    }

    # =========================================================================
    # RB14 (2đ): Hạn chế gác Thứ 7, Chủ Nhật
    # =========================================================================
    weekend_shifts = df_flat[df_flat['Thu'].isin(['Thứ 7', 'Chủ Nhật'])]
    total_weekend_assignments = len(weekend_shifts)
    penalty_rb14 = total_weekend_assignments * config.WEIGHT_WEEKEND
    
    total_penalty += penalty_rb14
    report['RB14_HanCheCuoiTuan'] = {
        'score': penalty_rb14,
        'details': f"Tổng số lượt cán bộ phải gác vào Thứ 7/Chủ Nhật: {total_weekend_assignments} lượt."
    }

    # =========================================================================
    # RB5 (1đ): Hạn chế nữ
    # =========================================================================
    '''
    female_shifts = df_flat[df_flat['Gioi_Tinh'] == 'Nữ']
    total_female_assignments = len(female_shifts)
    penalty_rb5 = total_female_assignments * config.WEIGHT_GENDER_BALANCE
    
    total_penalty += penalty_rb5
    report['RB5_HanCheNu'] = {
        'score': penalty_rb5,
        'details': f"Tổng số lượt cán bộ Nữ phải gác: {total_female_assignments} lượt."
    } '''

    return total_penalty, report

# Khối chạy thử độc lập
if __name__ == "__main__":
    from data_loader import load_data
    cb, ca, lich = load_data()
    diem_phat, bao_cao = evaluate_soft_constraints(cb, ca, lich)
    
    print("\n=== KẾT QUẢ SOFT CONSTRAINTS ===")
    for rule, info in bao_cao.items():
        print(f"[-] {rule:<30} | Phạt: {info['score']:>7} điểm | {info['details']}")
    print("-" * 50)
    print(f"TỔNG ĐIỂM PHẠT: {round(diem_phat, 2)}")