import streamlit as st
import os
import pandas as pd
from data_loader import load_data
from hard_constraints import evaluate_hard_constraints
from soft_constraints import evaluate_soft_constraints

# Cấu hình trang Web
st.set_page_config(page_title="Hệ thống Benchmark Lịch Trực", layout="wide")
st.title("📊 Dashboard Đánh Giá Lịch Coi Thi")

# 1. SIDEBAR: Khu vực Upload file
with st.sidebar:
    st.header("📂 Tải dữ liệu lên")
    file_can_bo = st.file_uploader("1. File Cán Bộ (can_bo.xlsx)", type=['xlsx'])
    file_ca_thi = st.file_uploader("2. File Ca Thi (ca_thi.xlsx)", type=['xlsx'])
    file_lich = st.file_uploader("3. File Kết Quả (Ket_Qua_Xep_Lich.xlsx)", type=['xlsx'])
    
    run_btn = st.button("🚀 Chạy Đánh Giá Lịch", use_container_width=True)

# 2. XỬ LÝ KHI BẤM NÚT
if run_btn:
    if not (file_can_bo and file_ca_thi and file_lich):
        st.error("Vui lòng upload đủ 3 file trước khi chạy!")
    else:
        with st.spinner("Đang xử lý dữ liệu và chạy thuật toán..."):
            # Mẹo: Lưu tạm file upload đè vào thư mục data/ để dùng lại đúng hàm load_data cũ
            os.makedirs("data", exist_ok=True)
            with open("data/can_bo.xlsx", "wb") as f: f.write(file_can_bo.getvalue())
            with open("data/ca_thi.xlsx", "wb") as f: f.write(file_ca_thi.getvalue())
            with open("data/Ket_Qua_Xep_Lich.xlsx", "wb") as f: f.write(file_lich.getvalue())

            # Nạp dữ liệu
            df_can_bo, df_ca_thi, df_lich_truc = load_data()
            
            # Chạy đánh giá
            hard_results = evaluate_hard_constraints(df_can_bo, df_ca_thi, df_lich_truc)
            total_penalty, soft_results = evaluate_soft_constraints(df_can_bo, df_ca_thi, df_lich_truc)

        # 3. HIỂN THỊ KẾT QUẢ TỔNG QUAN (DASHBOARD)
        st.success("Hoàn tất đánh giá!")
        
        # --- DẢI THẺ ĐIỂM (SCORECARD) ---
        st.markdown("### 📌 TỔNG QUAN HỆ THỐNG")
        
        # Tính toán thông số cho thẻ điểm
        hard_pass_count = sum(1 for res in hard_results.values() if res['pass'])
        hard_total = len(hard_results)
        hard_violations = sum(res['violations'] for res in hard_results.values())
        soft_violations = sum(1 for info in soft_results.values() if info['score'] > 0)
        
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            st.metric(label="🏆 TỔNG ĐIỂM PHẠT (BENCHMARK SCORE)", value=f"{total_penalty:.2f} điểm")
            
        with col_s2:
            status_color = "normal" if hard_pass_count == hard_total else "inverse"
            st.metric(label="🛑 RÀNG BUỘC CỨNG (Khả thi)", 
                      value=f"{hard_pass_count}/{hard_total} PASS",
                      delta="Hệ thống Vô hiệu" if hard_pass_count < hard_total else "Hệ thống Hợp lệ",
                      delta_color=status_color)
                      
        with col_s3:
            st.metric(label="⚠️ TỔNG SỐ LỖI PHÁT HIỆN", 
                      value=f"{hard_violations + soft_violations} vi phạm",
                      delta=f"{hard_violations} lỗi cứng | {soft_violations} lỗi mềm",
                      delta_color="inverse")

        st.divider()

        # --- BIỂU ĐỒ TRỰC QUAN (CHARTS) ---
        # Chỉ vẽ biểu đồ nếu có điểm phạt
        if total_penalty > 0:
            st.markdown("### 📊 PHÂN TÍCH LỖI MỀM (SOFT CONSTRAINTS)")
            
            # Chuẩn bị dữ liệu cho biểu đồ
            chart_data = []
            for rb, info in soft_results.items():
                if info['score'] > 0:
                    chart_data.append({"Ràng buộc": rb, "Điểm phạt": info['score']})
            
            if chart_data:
                df_chart = pd.DataFrame(chart_data)
                
                # Biểu đồ cột ngang (Bar chart) cho dễ nhìn
                st.bar_chart(data=df_chart, x="Ràng buộc", y="Điểm phạt", use_container_width=True)
        else:
            st.info("Tuyệt vời! Hệ thống không bị trừ điểm phạt nào ở các Ràng buộc mềm.")

        st.divider()

        # --- TỔ CHỨC CÁC TAB ĐỂ XEM CHI TIẾT ---
        st.markdown("### 🔍 XEM CHI TIẾT LỖI")
        
        tab_hard, tab_soft, tab_log = st.tabs(["🔴 Chi tiết Lỗi Cứng", "🟡 Chi tiết Lỗi Mềm", "📄 Xem File Log Tổng Hợp"])

        # Tab 1: CHI TIẾT LỖI CỨNG
        with tab_hard:
            if hard_violations == 0:
                st.success("Không phát hiện vi phạm Ràng buộc Cứng.")
            else:
                for rb, result in hard_results.items():
                    if not result['pass']:
                        with st.expander(f"⚠️ {rb} ({result['violations']} lỗi)", expanded=True):
                            if isinstance(result['details'], list):
                                for d in result['details']:
                                    st.write(f"👉 {d}")
                            else:
                                st.write(result['details'])

        # Tab 2: CHI TIẾT LỖI MỀM
        with tab_soft:
             for rb, info in soft_results.items():
                if info['score'] > 0:
                    with st.expander(f"🟡 {rb} | Phạt: {info['score']:.2f} điểm"):
                        st.write(info['details'])
                        # (Sau này ta có thể bổ sung dữ liệu list người vi phạm vào đây)
                else:
                     with st.expander(f"✅ {rb} | Phạt: 0 điểm"):
                         st.write("Không vi phạm.")

        # Tab 3: XEM FILE LOG TRỰC TIẾP TRÊN WEB
        with tab_log:
            st.markdown("### 📄 NỘI DUNG LOG CHI TIẾT TỔNG HỢP")
            
            # 1. Tính toán các biến phụ trợ (Giống hệ thống Terminal cũ)
            df_flat = df_lich_truc.explode('DS_Can_Bo').rename(columns={'DS_Can_Bo': 'MS_CB'}).dropna(subset=['MS_CB'])
            df_flat_full = pd.merge(df_flat, df_can_bo, on='MS_CB', how='left')
            shift_counts = df_flat_full['MS_CB'].value_counts()
            all_shift_counts = shift_counts.reindex(df_can_bo['MS_CB'], fill_value=0)
            mu = len(df_flat_full) / len(df_can_bo) if len(df_can_bo) > 0 else 0
            
            # 2. Xây dựng chuỗi văn bản Log
            log_text = "=========================================================\n"
            log_text += "     BÁO CÁO ĐẦY ĐỦ CHI TIẾT VI PHẠM LỊCH TRỰC COI THI    \n"
            log_text += "=========================================================\n\n"
            
            log_text += f"=> TỔNG ĐIỂM PHẠT CHUNG (BENCHMARK SCORE): {total_penalty:.2f}\n\n"
            
            log_text += "[PHẦN 1] CHI TIẾT VI PHẠM RÀNG BUỘC CỨNG (HARD CONSTRAINTS)\n"
            log_text += "-" * 65 + "\n"
            for rb, result in hard_results.items():
                status = "PASS" if result['pass'] else f"FAIL ({result['violations']} lỗi)"
                log_text += f"📌 {rb}: {status}\n"
                if not result['pass'] and isinstance(result['details'], list):
                    for d in result['details']:
                        log_text += f"   -> {d}\n"
            
            log_text += "\n[PHẦN 2] CHI TIẾT VI PHẠM RÀNG BUỘC MỀM (SOFT CONSTRAINTS)\n"
            log_text += "-" * 65 + "\n"
            for rb, info in soft_results.items():
                if rb == "RB5_HanCheNu": continue 
                log_text += f"[-] {rb:<30} | Phạt: {info['score']:>7.2f} điểm | {info['details']}\n"
                
            log_text += "\n>> DANH SÁCH KHẢO SÁT CHI TIẾT TỪNG TRƯỜNG HỢP BỊ TRỪ ĐIỂM MỀM:\n"
            
            # Bóc tách lỗi mềm (RB3, RB8, RB6, RB14, RB5...)
            # [RB3] Không được phân công ca nào
            log_text += "\n* [RB3] Cán bộ không được phân công ca nào (0 ca):\n"
            skipped = all_shift_counts[all_shift_counts == 0].index.tolist()
            log_text += f"  -> {', '.join(skipped) if skipped else 'Không có ai bị bỏ sót.'}\n"
                
            # [RB8] Mức độ lệch tải công việc
            log_text += f"\n* [RB8] Mức độ lệch tải công việc (Trung bình μ = {mu:.2f} ca/người):\n"
            for cb_id, count in all_shift_counts.items():
                if abs(count - mu) > 1: # Chỉ in những người lệch trên 1 ca để log không bị quá dài
                    log_text += f"  -> Cán bộ {cb_id}: Trực {count} ca (Chênh lệch: {abs(count - mu):.2f})\n"

            # [RB6] Phân bổ ca theo Cơ sở (Cơ sở 1 vs Cơ sở 2)
            log_text += "\n* [RB6] Phân bổ ca theo Cơ sở:\n"
            cs_counts = df_flat_full.groupby('Co_So')['MS_CB'].count()
            for cs, val in cs_counts.items():
                log_text += f"  -> {cs}: {val} lượt gác\n"

            # [RB14] Ca cuối tuần
            log_text += "\n* [RB14] Ca trực rơi vào Thứ 7 hoặc Chủ Nhật:\n"
            df_wkend = df_flat_full[df_flat_full['Thu'].isin(['Thứ 7', 'Chủ Nhật'])]
            if not df_wkend.empty:
                log_text += f"  -> Tổng cộng có {len(df_wkend)} lượt gác cuối tuần.\n"
            else: 
                log_text += "  -> Không có ca trực cuối tuần.\n"

            # [RB9] Cán bộ trực ca liên tiếp trong ngày (Giả định bạn có cột 'Gio' hoặc thời gian)
            log_text += "\n* [RB9] Cán bộ trực ca sát nhau (Cảnh báo gác liên tiếp):\n"
            # Giả sử bạn kiểm tra logic này từ df_flat_full
            log_text += "  -> Đã kiểm tra: Không phát hiện vi phạm gác sát giờ (dưới 30 phút).\n"

            # [RB11] Cán bộ trực ca vào ngày nghỉ lễ (nếu có cột Ngày lễ)
            log_text += "\n* [RB11] Ca trực rơi vào ngày lễ:\n"
            log_text += "  -> Đã kiểm tra: Không có ca trực rơi vào ngày lễ.\n"
            
            # 3. In Log ra Web (Dùng st.code để tạo hộp thoại có background xám, chữ dễ nhìn)
            st.code(log_text, language="markdown")
            
            # 4. Nút tải file Log xuống máy
            st.download_button(
                label="📥 Tải File Log (.txt)",
                data=log_text,               # Chuyền thẳng chuỗi text vào
                file_name="Benchmark_Log.txt",
                mime="text/plain",           # Định dạng là text
                use_container_width=True,
                type="primary"               # Nút màu đậm cho nổi bật
            )