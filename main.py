import sys
import os                  # <--- Bổ sung import os
import pandas as pd        # <--- Bổ sung import pandas để fix lỗi "pd is not defined"

from data_loader import load_data
from hard_constraints import evaluate_hard_constraints
from soft_constraints import evaluate_soft_constraints
from excel_exporter import export_to_excel

class TerminalColor:
    HEADER = '\033[95m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def main():
    print(f"{TerminalColor.BOLD}{TerminalColor.HEADER}")
    print("="*65)
    print("   HỆ THỐNG BENCHMARK LỊCH TRỰC COI THI (INTELLIGENT SCORING)")
    print("="*65)
    print(f"{TerminalColor.RESET}")

    # Tạo sẵn thư mục output ở thư mục gốc
    os.makedirs("output", exist_ok=True)

    # BƯỚC 1: NẠP DỮ LIỆU
    print(f"{TerminalColor.CYAN}[1/4] Đang nạp và chuẩn hóa dữ liệu...{TerminalColor.RESET}")
    try:
        df_can_bo, df_ca_thi, df_lich_truc = load_data()
    except Exception as e:
        print(f"{TerminalColor.RED}✘ Lỗi khi đọc dữ liệu: {e}{TerminalColor.RESET}")
        sys.exit(1)

    # BƯỚC 2: ĐÁNH GIÁ RÀNG BUỘC CỨNG (HARD CONSTRAINTS)
    print(f"\n{TerminalColor.BOLD}{TerminalColor.CYAN}[2/4] Đang kiểm tra Ràng buộc cứng...{TerminalColor.RESET}")
    hard_results = evaluate_hard_constraints(df_can_bo, df_ca_thi, df_lich_truc)
    
    for rb_name, result in hard_results.items():
        if result['pass']:
            print(f"{TerminalColor.GREEN}✔ {rb_name}: PASS{TerminalColor.RESET}")
        else:
            print(f"{TerminalColor.RED}✘ {rb_name}: FAIL ({result['violations']} vi phạm){TerminalColor.RESET}")
            if isinstance(result['details'], list):
                for detail in result['details']:  
                    print(f"   {TerminalColor.RED}-> {detail}{TerminalColor.RESET}")

    # BƯỚC 3: ĐÁNH GIÁ RÀNG BUỘC MỀM (SOFT CONSTRAINTS)
    print(f"\n{TerminalColor.BOLD}{TerminalColor.CYAN}[3/4] Đang tính điểm phạt Ràng buộc mềm...{TerminalColor.RESET}")
    total_penalty, soft_results = evaluate_soft_constraints(df_can_bo, df_ca_thi, df_lich_truc)
    
    for rb_name, info in soft_results.items():
        print(f"[-] {rb_name:<30} | {TerminalColor.YELLOW}Phạt: {info['score']:>7.2f} điểm{TerminalColor.RESET} | {info['details']}")

    # BƯỚC 4: TỔNG KẾT VÀ XUẤT EXCEL
    print(f"\n{TerminalColor.BOLD}{TerminalColor.CYAN}[4/4] Đang tổng kết và xuất báo cáo...{TerminalColor.RESET}")
    print(f"{TerminalColor.BOLD}{TerminalColor.HEADER}" + "="*65)
    print(f"🏆 FINAL BENCHMARK SCORE = {total_penalty:.2f}")
    print("="*65 + f"{TerminalColor.RESET}")

    df_flat = df_lich_truc.explode('DS_Can_Bo').rename(columns={'DS_Can_Bo': 'MS_CB'}).dropna(subset=['MS_CB'])
    df_flat_full = pd.merge(df_flat, df_can_bo, on='MS_CB', how='left')
    shift_counts = df_flat_full['MS_CB'].value_counts()
    all_shift_counts = shift_counts.reindex(df_can_bo['MS_CB'], fill_value=0)
    mu = len(df_flat_full) / len(df_can_bo) if len(df_can_bo) > 0 else 0

    try:
        export_to_excel(hard_results, soft_results, total_penalty, df_can_bo, df_lich_truc, all_shift_counts, mu)
    except Exception as e:
        print(f"{TerminalColor.RED}✘ Lỗi khi tạo file Excel: {e}{TerminalColor.RESET}")

    # BƯỚC 5: XUẤT FILE LOG TXT - GHI CHI TIẾT TOÀN BỘ SỰ CỐ CỨNG & MỀM (BẤT KỂ TRỌNG SỐ = 0)
    txt_filename = os.path.join("output", "Benchmark_Log.txt")
    try:
        import itertools
        from collections import Counter

        with open(txt_filename, "w", encoding="utf-8") as f:
            f.write("=========================================================\n")
            f.write("     BÁO CÁO ĐẦY ĐỦ CHI TIẾT VI PHẠM LỊCH TRỰC COI THI    \n")
            f.write("=========================================================\n\n")
            
            f.write(f"=> TỔNG ĐIỂM PHẠT CHUNG (BENCHMARK SCORE): {total_penalty:.2f}\n\n")
            
            f.write("[PHẦN 1] CHI TIẾT VI PHẠM RÀNG BUỘC CỨNG (HARD CONSTRAINTS)\n")
            f.write("-" * 65 + "\n")
            for rb_name, result in hard_results.items():
                status = "PASS" if result['pass'] else f"FAIL ({result['violations']} lỗi)"
                f.write(f"📌 {rb_name}: {status}\n")
                if not result['pass'] and isinstance(result['details'], list):
                    for detail in result['details']:
                        f.write(f"   -> {detail}\n")
            
            f.write("\n[PHẦN 2] CHI TIẾT VI PHẠM RÀNG BUỘC MỀM (SOFT CONSTRAINTS)\n")
            f.write("-" * 65 + "\n")
            for rb_name, info in soft_results.items():
                f.write(f"[-] {rb_name:<30} | Phạt: {info['score']:>7.2f} điểm | {info['details']}\n")
                
            f.write("\n>> DANH SÁCH KHẢO SÁT CHI TIẾT TỪNG TRƯỜNG HỢP BỊ TRỪ ĐIỂM MỀM:\n")
            
            # RB3: Chi tiết bỏ sót người
            f.write("\n* [RB3] Cán bộ không được phân công ca nào (0 ca):\n")
            skipped = all_shift_counts[all_shift_counts == 0].index.tolist()
            f.write(f"  -> {', '.join(skipped) if skipped else 'Không có ai bị bỏ sót.'}\n")
                
            # RB8: Chi tiết phân bổ không đều ca
            f.write(f"\n* [RB8] Mức độ lệch tải công việc (Tiêu chuẩn trung bình μ = {mu:.2f} ca/người):\n")
            for cb_id, count in all_shift_counts.items():
                if count != round(mu, 2):
                    f.write(f"  -> Cán bộ {cb_id}: Trực {count} ca (Chênh lệch: {abs(count - mu):.2f} ca)\n")

            # RB7: Thống kê quãng đường di chuyển thực tế (bất kể bị phạt hay không)
            f.write("\n* [RB7] Chi tiết tổng quãng đường di chuyển của từng cán bộ (km):\n")
            df_flat_full['KC_Tung_Ca'] = df_flat_full.apply(lambda r: r['KC_CS1'] if r['Co_So'] == 'Cơ sở 1' else (r['KC_CS2'] if r['Co_So'] == 'Cơ sở 2' else 0), axis=1)
            staff_dist = df_flat_full.groupby('MS_CB')['KC_Tung_Ca'].sum()
            for cb_id, d in staff_dist.items():
                if d > 0:
                    f.write(f"  -> Cán bộ {cb_id}: Tổng quãng đường đi gác = {d:.2f} km\n")

            # RB9: Chi tiết đổi cơ sở trong cùng một ngày
            f.write("\n* [RB9] Cán bộ trực nhiều ca cùng ngày nhưng phải di chuyển khác cơ sở:\n")
            has_rb9 = False
            
            # Cần sort theo thời gian trước để hiển thị đúng thứ tự di chuyển
            df_sorted_rb9 = df_flat_full.sort_values(by=['MS_CB', 'Ngay_Goc', 'Thoi_Gian_Bat_Dau'])
            
            for (cb, date), group in df_sorted_rb9.groupby(['MS_CB', 'Ngay_Goc']):
                if group['Co_So'].nunique() > 1:
                    # Tạo chuỗi lịch trình trực quan
                    shifts = group.to_dict('records')
                    hanh_trinh = " -->> ".join([f"{s['Co_So']} gác ca {s['MS_CA']}" for s in shifts])
                    
                    # Rút gọn ngày cho dễ nhìn
                    date_str = pd.to_datetime(date).strftime('%d/%m/%Y')
                    
                    f.write(f"  -> Cán bộ {cb} ngày {date_str} di chuyển: {hanh_trinh}\n")
                    has_rb9 = True
                    
            if not has_rb9: f.write("  -> Không có trường hợp vi phạm.\n")
                    
            # RB11: Chi tiết thời gian nghỉ giữa 2 ca sát nút
            f.write("\n* [RB11] Chi tiết các ca xếp sát nhau có thời gian nghỉ ngơi chưa đủ (< 2 tiếng):\n")
            has_rb11 = False
            df_sorted = df_flat_full.sort_values(by=['MS_CB', 'Thoi_Gian_Bat_Dau'])
            for (cb, date), group in df_sorted.groupby(['MS_CB', 'Ngay_Goc']):
                if len(group) >= 2:
                    shifts = group.to_dict('records')
                    for i in range(1, len(shifts)):
                        prev_end = pd.to_datetime(shifts[i-1]['Thoi_Gian_Ket_Thuc'])
                        curr_start = pd.to_datetime(shifts[i]['Thoi_Gian_Bat_Dau'])
                        gap = (curr_start - prev_end).total_seconds() / 3600.0
                        if gap < 2.0:  # Mặc định dưới 2 tiếng là vi phạm
                            f.write(f"  -> Cán bộ {cb}: Ca {shifts[i-1]['MS_CA']} xong lúc {prev_end.strftime('%H:%M')}, ca {shifts[i]['MS_CA']} bắt đầu lúc {curr_start.strftime('%H:%M')} (Nghỉ {gap:.2f} tiếng)\n")
                            has_rb11 = True
            if not has_rb11: f.write("  -> Không có trường hợp vi phạm.\n")

            # RB6: Chi tiết phân bổ quá tải cho người lớn tuổi
            f.write("\n* [RB6] Cán bộ lớn tuổi (>45 tuổi) bị phân phối vượt trần trung bình:\n")
            has_rb6 = False
            for cb_row in df_can_bo.to_dict('records'):
                if cb_row['Tuoi'] > 45:
                    tc = all_shift_counts.get(cb_row['MS_CB'], 0)
                    if tc > mu:
                        f.write(f"  -> Cán bộ {cb_row['MS_CB']} ({cb_row['Tuoi']} tuổi): Trực {tc} ca (Vượt trần {tc - mu:.2f} ca)\n")
                        has_rb6 = True
            if not has_rb6: f.write("  -> Không có trường hợp vi phạm.\n")

            # RB13: Chi tiết cặp đôi trùng lặp đối tác gác thi
            f.write("\n* [RB13] Chi tiết các cặp đôi gác chung với nhau quá nhiều lần (>= 3 lần):\n")
            all_pairs = []
            for ds in df_lich_truc['DS_Can_Bo']:
                if len(ds) >= 2:
                    all_pairs.extend(itertools.combinations(sorted(ds), 2))
            pair_counts = Counter(all_pairs)
            freq_pairs = {p: c for p, c in pair_counts.items() if c >= 3}
            if freq_pairs:
                for pair, count in freq_pairs.items():
                    f.write(f"  -> Cặp ({pair[0]}, {pair[1]}): Gác chung {count} lần\n")
            else: f.write("  -> Không có cặp nào gác chung >= 3 lần.\n")
                
            # RB14: Chi tiết gác ngày nghỉ cuối tuần
            f.write("\n* [RB14] Chi tiết các lượt gác rơi vào Thứ 7 hoặc Chủ Nhật:\n")
            df_wkend = df_flat_full[df_flat_full['Thu'].isin(['Thứ 7', 'Chủ Nhật'])]
            if not df_wkend.empty:
                for _, row in df_wkend.iterrows():
                    f.write(f"  -> Cán bộ {row['MS_CB']} gác ca {row['MS_CA']} vào ngày nghỉ {row['Thu']} ({row['Co_So']})\n")
            else: f.write("  -> Không có ca trực cuối tuần.\n")
                
            # RB5: Chi tiết tải gác của cán bộ Nữ
            f.write("\n* [RB5] Thống kê tần suất gác chi tiết của các cán bộ Nữ:\n")
            df_female = df_flat_full[df_flat_full['Gioi_Tinh'] == 'Nữ']
            if not df_female.empty:
                for cb_id, group in df_female.groupby('MS_CB'):
                    f.write(f"  -> Cán bộ Nữ {cb_id} phải trực {len(group)} ca: {', '.join(group['MS_CA'].tolist())}\n")
            else: f.write("  -> Không có cán bộ nữ tham gia.\n")

        print(f"{TerminalColor.GREEN}✔ Đã cập nhật và lưu vết vi phạm chi tiết 9/9 luật mềm ra file: {txt_filename}{TerminalColor.RESET}\n")
    except Exception as e:
        print(f"{TerminalColor.RED}✘ Lỗi khi ghi file log TXT: {e}{TerminalColor.RESET}")

if __name__ == "__main__":
    main()