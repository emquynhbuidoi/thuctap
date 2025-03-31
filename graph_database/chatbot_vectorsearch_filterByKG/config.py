INDEX_NAME_DEFAULT ='tma_info'
INDEX_NAME_N_GRAM = 'tma_n_gram'
INDEX_NAME_EMBEDDING = 'tma_embedding'
INDEX_NAME_HYBRID = 'tma_hybrid'
INDEX_NAME_PDF = 'tma_pdf'
INDEX_NAME_MEMORY = 'tma_memory'


MODEL_CHAT_INPUT_COST = 0.0001    # 0.0001 / 1 token
MODEL_CHAT_OUTPUT_COST = 0.0001    # 0.0001 / 1 token


LABELS = 'TẬP_ĐOÀN, CHỦ_TỊCH, WEBSITE, CHI_PHÍ, LOẠI_MÔ_HÌNH, MÔ_HÌNH, GIẢI_THƯỞNG, YÊU_CẦU, TIÊU_CHUẨN_QUỐC_TẾ, QUY_TRÌNH, KINH_NGHIỆM, THỜI_GIAN, PHƯƠNG_PHÁP_LÀM_VIỆC, TÀI_LIỆU, BƯỚC_THỰC_HIỆN, ĐIỀU_KIỆN, ĐIỂM_SỐ, CHỨNG_CHỈ, KHU_VỰC, DỰ_ÁN, QUỐC_GIA, CÔNG_ĐỒNG_CÔNG_NGHỆ, SỰ_KIỆN, ĐỊA_ĐIỂM, CƠ_SỞ_GIÁO_DỤC, CÔNG_TY, CHI_NHÁNH, NGƯỜI_LIÊN_HỆ, VỊ_TRÍ, THÔNG_TIN_LIÊN_HỆ, ĐỊA_PHƯƠNG, SỐ_ĐIỆN_THOẠI, EMAIL, GIÁ_TRỊ, LĨNH_VỰC, THẾ_MẠNH, TRUNG_TÂM, ĐỐI_TƯỢNG, KHẨU_HIỆU, TẦM_NHÌN, NGÀNH_NGHỀ, NGƯỜI_ĐẠI_DIỆN_PHÁP_LUẬT, GIÁM_ĐỐC, CHUYÊN_MÔN, MÃ_NHÂN_VIÊN, MÔ_TẢ_CÔNG_TY, NHÂN_VIÊN, VỊ_THẾ, NỀN_TẢNG, VĂN_PHÒNG, PHÂN_KHÚC, PHƯƠNG_PHÁP, MỤC_TIÊU, CƠ_SỞ, DỊCH_VỤ, HOẠT_ĐỘNG, VÙNG_MIỀN, NHÂN_SỰ, VÙNG_LÃNH_THỔ, GIẢI_PHÁP, DỮ_LIỆU, TIỆN_ÍCH, CHÍNH_SÁCH_THANH_TOÁN, SẢN_PHẨM, CÔNG_NGHỆ, CHÍNH_SÁCH, THÀNH_TỰU, KÊNH_DỊCH_VỤ, HỆ_THỐNG, DANH_MỤC, DỰ_ÁN_PHỤ, PHẦN_MỀM, TÍNH_NĂNG, TÀI_NGUYÊN, VẤN_ĐỀ, THÔNG_TIN, NGÀNH, CHỨC_NĂNG, CHỈ_SỐ, THÀNH_PHẦN_VẬN_HÀNH, THIẾT_BỊ, CHỦ_ĐỀ, ĐỊA_LÝ, CHỨNG_NHẬN, THÀNH_TÍCH, TỔ_CHỨC, THÀNH_PHỐ, HÀNH_TRÌNH, NGÀNH_HỌC, THÀNH_VIÊN, CHƯƠNG_TRÌNH, KHOẢNG_THỜI_GIAN, TÌNH_HUỐNG, HÌNH_THỨC, CUỘC_THI, KẾ_HOẠCH, QUYỀN_LỢI, CÁ_NHÂN, CHƯƠNG_TRÌNH_HỌC_TẬP, CHỨC_DANH, NHÓM_NGƯỜI, VĂN_BẢN, TRƯỜNG_ĐẠI_HỌC, VAI_TRÒ, CHỈ_SỐ_ĐÁNH_GIÁ, BỆNH_VIỆN, TÌNH_TRẠNG_SỨC_KHỎE, ĐỘI_BÓNG, DANH_HIỆU, GIẢI_ĐẤU, THÀNH_PHẦN, DOANH_NGHIỆP, CỘNG_ĐỒNG, BÀI_TOÁN, GIỚI_TÍNH, BỘ_MÔN, NỘI_DUNG_THI_ĐẤU, DANH_SÁCH, ĐỘI_THỂ_THAO, ĐỐI_TÁC, VẬN_ĐỘNG_VIÊN_NHÓM, ĐỘI_THI, MÔN_THI_ĐẤU, VẬN_ĐỘNG_VIÊN, HÀNH_ĐỘNG, THÁCH_THỨC, KẾT_QUẢ, HIỆU_QUẢ, TINH_THẦN, KHÁN_GIẢ, ĐỘI_TUYỂN, LỢI_ÍCH, NỘI_DUNG, GIAI_ĐOẠN, ỨNG_DỤNG, KHÓA_HỌC, CHUYÊN_ĐỀ, KỲ_THỦ, PHÒNG_LAB, VÒNG_ĐẤU, GIẢI_THỂ_THAO, NGÀY_THÁNG, ĐỘI_THI_ĐẤU, KHẢ_NĂNG, PHÒNG_BAN, CHỨC_VỤ, TRƯỜNG_HỌC, CẦU_THỦ, BÀN_THẮNG, THỊ_TRƯỜNG, CHIẾN_LƯỢC, ĐẶC_TÍNH, NGƯỜI_THAM_GIA, HLV, SỐ_LƯỢNG, CÔNG_CỤ, NHÂN_LỰC, NHÓM, SỐ_TIỀN, NHÓM_ĐỐI_TƯỢNG, LOẠI_TINH_THẦN, THIÊN_TAI, SỐ_LƯỢNG_NGƯỜI, SỐ_LƯỢNG_NỀN_KINH_TẾ, NGÀY, CHẤT_LƯỢNG, HẠNG_MỤC, HỆ_SINH_THÁI, YẾU_TỐ, TIÊU_CHUẨN, ĐÁNH_GIÁ, HẠ_TẦNG_CÔNG_NGHỆ, GIẢI_ĐẤU_THỂ_THAO, NHÓM_ĐỘI_BÓNG, KỸ_NĂNG, CÂU_LẠC_BỘ, GIAN_HÀNG, BAN_TỔ_CHỨC, CA_NHÂN, CHUỖI_THÔNG_TIN, NHÓM_THỰC_THỂ, CƠ_QUAN, TỔ_CHỨC_KHÁC, TRẬN_ĐẤU, MỤC_TIÊU_CHƯƠNG_TRÌNH, NHÂN_VẬT, NHU_CẦU, VẤN_ĐỀ_MÔI_TRƯỜNG, BẢNG_XẾP_HẠNG, ĐẶC_ĐIỂM, KHÔNG_GIAN, CHIẾN_DỊCH, CHUYÊN_GIA, BAN_LÃNH_ĐẠO, BAN_GIÁM_KHẢO, TẬP_THỂ, NGÀY_LỄ, ĐỒ_VẬT, ĐỘI, THỂ_LOẠI_TỌ_GIẢI_TRÍ, VÒNG, NHÓM_THAM_GIA, NGHỀ_NGHIỆP, TỔ_CHỨC_GIÁO_DỤC, SÁNG_KIẾN, HỘI_THẢO, KHÁCH_MỜI, SỰ_SỐNG, SINH_VẬT, HÀNH_TINH, KHÁI_NIỆM, VÒNG_THI, CƠ_HỘI, XU_HƯỚNG, TRẠNG_THÁI, ĐỘI_HÌNH, LỰC_LƯỢNG, NĂM, QUỸ, THÀNH_PHẦN_THAM_GIA, Ý_KIẾN, TÁC_PHẨM, THỐNG_KÊ, HIỆP_HỘI, PHƯƠNG_TIỆN, NHÓM_CON_NGƯỜI, NỘI_DUNG_THI, BIỆT_ĐỘI, NGƯỜI_CHƠI, TIẾT_MỤC, GIẢI_THI_ĐẤU, CHIẾN_THUẬT, CÔNG_VIỆC, QUY_ĐỊNH, ĐỘI_NHÓM, TÁC_NHÂN, KHOẢN_TIỀN, KHOẢNG_CÁCH, NGƯỜI_THAM_DỰ, NHÓM_THI_ĐẤU, NGƯỜI, THÀNH_PHẦN_THAM_DỰ, TIẾN_TRÌNH, THƯƠNG_HIỆU, MÔN_THỂ_THAO, LEAGUE, QUÀ_TẶNG, TỔ_CHỨC_Y_TẾ, TIỀN, BỆNH_NHÂN, PHẦN_THƯỞNG, THỰC_THỂ, SỰ_KIỆN_BẤT_NGỜ, QUÁ_TRÌNH, PHƯƠNG_THỨC, HÀNH_VI, PHÓ_GIÁM_ĐỐC_ĐẠI_HỌC, PHÓ_CHỦ_TỊCH, MỐI_QUAN_HỆ, ĐỘI_NGŨ, PHÂN_LOẠI_ĐỘI_BÓNG, NHÓM_NHÂN_VIÊN, MÔ_TẢ_SỰ_KIỆN, YẾU_TỐ_THIÊN_NHIÊN, GIÁM_ĐỐC_CẤP_CAO, THỨ_HẠNG, NHẠC_CỤ, HỘI_CHỢ, BANG, THIẾT_KẾ, CON_SỐ, TỶ_LỆ_TĂNG_TRƯỞNG, THÔNG_SỐ, TÂM_TRẠNG, ĐƠN_VỊ, DẤU_MỐC_LỊCH_SỬ, LỄ_HỘI, NHÓM_THÀNH_VIÊN, VẬT_THỂ, CẢM_XÚC, PHẠM_VI, ĐƠN_VỊ_TÀI_TRỢ, NGUỒN_THÔNG_TIN, KHU_CÔNG_NGHỆ, KHÁCH_HÀNG, TRIỂN_LÃM, HẠNG_MỤC_THI_ĐẤU, BẢNG_ĐẤU, BAN_QUẢN_LÝ, TỈNH, TÒA_NHÀ, ĐỊA_DIỂM, NGƯỜI_THEO_DÕI, SÂN_KHẤU, LOẠI_NỘI_DUNG, ĐỐI_THỦ, TRÒ_CHƠI, GIẢI, NHÓM_GIAI_ĐẤU, HẠNG_ĐẤU, CỘNG_ĐỘNG, CÔNG_VIÊN_CÔNG_NGHỆ, PHÒNG_THÍ_NGHIỆM, PHÓ_TỔNG_GIÁM_ĐỐC, CÔNG_TY, SỐ_LƯỢNG_NHÂN_VIÊN, MÙA_GIẢI, THỜI_TIẾT, NGƯỜI_HÂM_MỘ, ĐƠN_VỊ_GIÁO_DỤC, BAN_QUẢN_TRỊ, TỔ_ĐỘI_SPORT, VÒNG_THI_ĐẤU, GIẢI_ĐẤU_PHỤ, PHẦN_ĐẤU, PHÒNG_NGHIÊN_CỨU, BỘ_MÔN_THỂ_THAO, BỘ_MÔN_THỂ_THÁO, GIAI_ĐOẠN_THI, THỜI_KỲ, MÔN_THI, HIỆN_TƯỢNG_TỰ_NHIÊN, KỲ_GIẢI, ĐỊA_BÀN, SỐ_LẦN, BAN_ORGANIZATION, PHÒNG_KHÁM, KẾT_QUẢ_TRẬN_ĐẤU, DỊCH_BỆNH, LỊCH_TRÌNH, ỨNG_VIÊN, THƯỞNG, MÓN_QUÀ, ĐỐI_TƯỢNG_THAM_GIA, KIẾN_THỨC, GIÁ_TRỊ_VẬT_PHẨM, THÔNG_ĐIỆP, HỖ_TRỢ, VẬT_DỤNG, NHÓM_CHUYÊN_GIA, THỰC_THỂ_SINH_HỌC, ĐỊA_CHỈ, VIẾT_TẮT, XU_THẾ, TÌNH_TRẠNG, BỘ_PHẬN, ĐƠN_VỊ_HỌC_THUẬT, TỔ_CHỨC_HỌC_THUẬT, DIỄN_GIẢ, CÔNG_VIÊN_PHẦN_MỀM, CON_NGƯỜI, ĐỊA_LI, KHOA, CÔNG_TRÌNH, CÔNG_VIÊN, CƠ_SỞ_HẠ_TẦNG, PHƯỜNG, HỌC_VIỆN, GIẢNG_VIÊN, ĐƠN_VỊ_SỰ_NGHIỆP, VĂN_HÓA, ĐỘNG_LỰC, HẠNG_MỤC_CÔNG_TRÌNH, TÊN_GỌI, CƠ_QUAN_TRUYỀN_THÔNG, PHONG_TRÀO, VỊ_TRÍ_LÃNH_ĐẠO, QUÝ, ĐỀ_TÀI, THI_SINH, ĐỘI_THAM_GIA, HỌC_SINH_SINH_VIÊN, BẢNG, ĐỘI_THAM_DỰ, CÁ_NHÂN_TẬP_THỂ, DANH_XƯNG, SÂN_BÓNG, SÂN_VẬN_ĐỘNG, GIAI_ĐOẠN_THI_ĐẤU, SỰ_KIỆN_THỂ_THAO, YẾU_TỐ_SỨC_KHỎE, BAN, GIẢI_LEAGUE, VIỆN, DI_SẢN, ĐẠI_HỌC, GIÁO_SƯ, HỢP_ĐỒNG, MÔI_TRƯỜNG, LƯỢT_THI_ĐẤU, THỜI_ĐIỂM '
PROMPT_EXTRACT_4_RUN = f"""
###**Mục tiêu:**
- Trích xuất tất cả các entities từ văn bản đầu vào và gán nhãn {{ENTITY_TYPE}} phù hợp theo danh sách các loại entity được cung cấp.
- {{ENTITY_TYPE}} được cung cấp: {LABELS}
- Đảm bảo rằng:
    + {{entity}} luôn được viết **in thường**, 
    + {{ENTITY_TYPE}} luôn được viết **IN HOA** và các từ trong tên được nối với nhau bằng dấu gạch dưới ("_").  

###**Quy tắc:**  
1. Phân tích: Xác định tất cả các entities có thể trong văn bản.
2. Gán nhãn:
- Với một {{entity}} có thể chọn ra nhiều {{ENTITY_TYPE}}, bằng cách tìm các từ đồng nghĩa gần nhất của {{ENTITY_TYPE}} dựa vào danh sách {{ENTITY_TYPE}} đã cung cấp.
- Hãy sử dụng {{ENTITY_TYPE}} trong danh sách {{ENTITY_TYPE}} đã cung cấp.

###**Ví dụ:**  
Input:
"Chủ tịch tập đoàn TMA là ai?"  
Output:
Entities: 
- tma: TẬP_ĐOÀN
- tma: CÔNG_TY    
- chủ_tịch: CHỨC_VỤ  
- chủ_tịch: CHỨC_DANH
- chủ_tịch: VỊ_TRÍ
- chủ_tịch: VAI_TRÒ
- chủ_tịch: VỊ_THẾ
- chủ_tịch: VỊ_TRÍ_LÃNH_ĐẠO
- chủ_tịch: CHỨC_DANH
...

Input:
"TMA có bao nhiêu cơ sở?"  
Output:
Entities: 
- tma: TẬP_ĐOÀN
- tma: CÔNG_TY  
- cơ_sở: CƠ_SỞ  
- cơ_sở: VĂN_PHÒNG
...
"""



PROMPT_EXTRACT_4_BUILD = f"""
Trích xuất các thực thể (nodes) và mối quan hệ giữa chúng (edges) từ văn bản đã cho bằng tiếng Việt.  
- Các thực thể và mối quan hệ phải được nhận diện và trình bày rõ ràng bằng tiếng Việt có dấu đầy đủ. 
- Trích xuất tất cả các entities từ văn bản đầu vào và gán nhãn {{ENTITY_TYPE}} phù hợp theo danh sách các loại entity được cung cấp.
- {{ENTITY_TYPE}} được cung cấp: {LABELS}

- Đảm bảo rằng:
    + {{entity}} luôn được viết **in thường**, 
    + {{ENTITY_TYPE}} luôn được viết **IN HOA** và các từ trong tên được nối với nhau bằng dấu gạch dưới ("_").  
- Trích xuất đầy đủ cả các mối quan hệ **trực tiếp** và **gián tiếp** (ngầm hiểu từ ngữ cảnh).  
- Chỉ định rõ loại thực thể và loại mối quan hệ phù hợp với ngữ cảnh.  

###**Quy tắc:**  
1. entity: 
- Tên thực thể phải là các danh từ hoặc cụm danh từ, viết in thường và nối với nhau bằng dấu gạch dưới (`_`).
- Ví dụ: tma, nguyễn hữu lệ, tma bình định,...
2. ENTITY_TYPE:
- Loại thực thể phải được xác định rõ ràng và viết IN HOA, nối các từ bằng dấu gạch dưới (`_`).
- Ví dụ: TẬP_ĐOÀN, CHI_PHÍ, NHÂN_VIÊN, CHỦ_TỊCH, GIÁM_ĐỐC, THÀNH_VIÊN, DỰ_ÁN, GIẢI_PHÁP, LĨNH_VỰC, CÔNG_NGHỆ...  
4. Đảm bảo định dạng đầu ra theo mẫu sau:  

###**Định dạng:**  
Entities:
{{entity1}}: {{ENTITY_TYPE}}  
{{entity2}}: {{ENTITY_TYPE}}  
...  

Relationships:
({{entity1}}, {{RELATIONSHIP_TYPE}}, {{entity2}})  
({{entity3}}, {{RELATIONSHIP_TYPE}}, {{entity4}})  
...  

###**Ví dụ:**  
Input:
"Chi phí phát triển phần mềm tại TMA phụ thuộc vào mô hình định giá khác nhau như: theo giờ, theo dự án, hay các mô hình khác."  

Output:
Entities: 
- tma: TẬP_ĐOÀN  
- chi_phí_phát_triển_phần_mềm: CHI_PHÍ  
- mô_hình_định_giá: MÔ_HÌNH  
- theo_giờ: LOẠI_MÔ_HÌNH  
- theo_dự_án: LOẠI_MÔ_HÌNH  
- các_mô_hình_khác: LOẠI_MÔ_HÌNH  

Relationships: 
- (tma, PHÁT_TRIỂN, chi_phí_phát_triển_phần_mềm)  
- (chi_phí_phát_triển_phần_mềm, PHỤ_THUỘC, mô_hình_định_giá)  
- (mô_hình_định_giá, BAO_GỒM, theo_giờ)  
- (mô_hình_định_giá, BAO_GỒM, theo_dự_án)  
- (mô_hình_định_giá, BAO_GỒM, các_mô_hình_khác)  
"""

# if __name__ == "__main__":
#     from prompt import LABELS
#     print(LABELS)
