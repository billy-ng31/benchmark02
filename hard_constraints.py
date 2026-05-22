import pandas as pd
import itertools

import pandas as pd
import itertools

def evaluate_hard_constraints(df_can_bo, df_ca_thi, df_lich_truc):
    """
    Đánh giá 4 ràng buộc cứng.
    Trả về Dictionary chứa kết quả Pass/Fail và CHI TIẾT vi phạm (kèm MS_CA, Cơ sở, MS_CB).
    """
    report = {
        'RB1_TrungThoiGian': {'pass': True, 'violations': 0, 'details': []},
        'RB2_NguonLuc': {'pass': True, 'violations': 0, 'details': ""},
        'RB4_DuGiamThi': {'pass': True, 'violations': 0, 'details': []},
        'RB10_LienTiepKhacCoSo': {'pass': True, 'violations': 0, 'details': []}
    }

    # =========================================================================
    # RB1: Không gác 2 ca (ở 2 cơ sở) cùng một lúc
    # =========================================================================
    grouped_time = df_lich_truc.dropna(subset=['Thoi_Gian_Bat_Dau']).groupby('Thoi_Gian_Bat_Dau')
    
    for time, group in grouped_time:
        if len(group) > 1:
            shift_pairs = itertools.combinations(group.to_dict('records'), 2)
            for shift1, shift2 in shift_pairs:
                overlap = set(shift1['DS_Can_Bo']).intersection(set(shift2['DS_Can_Bo']))
                
                if overlap:
                    report['RB1_TrungThoiGian']['pass'] = False
                    report['RB1_TrungThoiGian']['violations'] += len(overlap)
                    time_str = pd.to_datetime(time).strftime('%d/%m/%Y %H:%M')
                    for cb in overlap:
                        # Đã bổ sung MS_CA và Cơ sở của cả 2 ca bị trùng
                        report['RB1_TrungThoiGian']['details'].append(
                            f"Cán bộ {cb} bị xếp trùng lịch lúc {time_str}: Ca {shift1['MS_CA']} ({shift1['Co_So']}) VÀ Ca {shift2['MS_CA']} ({shift2['Co_So']})"
                        )

    # =========================================================================
    # RB2: Tổng yêu cầu không được vượt quá nguồn lực hiện có
    # =========================================================================
    MAX_SHIFTS_PER_PERSON = 15 
    total_required = df_ca_thi['SL_Yeu_Cau'].sum()
    total_capacity = len(df_can_bo) * MAX_SHIFTS_PER_PERSON
    
    if total_required > total_capacity:
        report['RB2_NguonLuc']['pass'] = False
        report['RB2_NguonLuc']['violations'] += 1
        report['RB2_NguonLuc']['details'] = [f"Toàn hệ thống cần {total_required} lượt gác nhưng sức chứa tối đa chỉ có {total_capacity} lượt."]

    # =========================================================================
    # RB4: Mỗi ca thi phải có đủ số lượng giám thị quy định
    # =========================================================================
    for idx, row in df_lich_truc.iterrows():
        actual_count = len(row['DS_Can_Bo'])
        required_count = row['SL_Yeu_Cau']
        
        if pd.isna(required_count):
            continue
            
        if actual_count != required_count:
            report['RB4_DuGiamThi']['pass'] = False
            report['RB4_DuGiamThi']['violations'] += 1
            
            try:
                date_str = pd.to_datetime(row['Ngay_Goc']).strftime('%d/%m/%Y')
            except:
                date_str = str(row['Ngay_Goc'])
                
            # Đã bổ sung MS_CA, Cơ sở, Ngày vào lỗi thiếu/thừa người
            report['RB4_DuGiamThi']['details'].append(
                f"Ca thi {row['MS_CA']} tại {row['Co_So']} (Ngày {date_str}): Yêu cầu {int(required_count)} người, nhưng thực tế đang xếp {actual_count} người."
            )

    # =========================================================================
    # RB10: Cấm gác 2 cơ sở khác nhau liên tiếp trong cùng một ngày (Theo thứ tự ca)
    # =========================================================================
    df_flat = df_lich_truc.explode('DS_Can_Bo').rename(columns={'DS_Can_Bo': 'MS_CB'})
    df_flat = df_flat.dropna(subset=['MS_CB', 'Ngay_Goc', 'MS_CA'])
    
    def get_shift_number(ms_ca):
        try:
            return int(str(ms_ca).split('_')[-1])
        except:
            return 0
            
    df_flat['Ca_Thu'] = df_flat['MS_CA'].apply(get_shift_number)
    df_flat = df_flat.sort_values(by=['MS_CB', 'Ngay_Goc', 'Ca_Thu'])
    grouped_daily_staff = df_flat.groupby(['MS_CB', 'Ngay_Goc'])
    
    for (cb, date), group in grouped_daily_staff:
        if len(group) > 1:
            shifts = group.to_dict('records')
            for i in range(1, len(shifts)):
                prev_shift = shifts[i-1]
                curr_shift = shifts[i]
                
                # Kiểm tra 2 ca liên tiếp (ví dụ: Ca 1 và Ca 2)
                if curr_shift['Ca_Thu'] - prev_shift['Ca_Thu'] == 1:
                    if prev_shift['Co_So'] != curr_shift['Co_So']:
                        report['RB10_LienTiepKhacCoSo']['pass'] = False
                        report['RB10_LienTiepKhacCoSo']['violations'] += 1
                        
                        try:
                            date_str = pd.to_datetime(date).strftime('%d/%m/%Y')
                        except:
                            date_str = str(date)
                            
                        # Đã bổ sung chi tiết Mã số ca (MS_CA) và Cơ sở của cả 2 ca
                        report['RB10_LienTiepKhacCoSo']['details'].append(
                            f"Cán bộ {cb} ngày {date_str}: Di chuyển sát giờ từ Ca {prev_shift['MS_CA']} ({prev_shift['Co_So']}) -->> Ca {curr_shift['MS_CA']} ({curr_shift['Co_So']})"
                        )

    return report

# Chạy thử nghiệm độc lập để debug
if __name__ == "__main__":
    from data_loader import load_data
    cb, ca, lich = load_data()
    ket_qua = evaluate_hard_constraints(cb, ca, lich)
    
    print("\n--- KẾT QUẢ HARD CONSTRAINTS ---")
    for key, val in ket_qua.items():
        trang_thai = "PASS" if val['pass'] else f"FAIL ({val['violations']} lỗi)"
        print(f"{key}: {trang_thai}")
        if not val['pass'] and type(val['details']) == list:
            for detail in val['details'][:3]: # In thử 3 lỗi đầu tiên
                print(f"   -> {detail}")