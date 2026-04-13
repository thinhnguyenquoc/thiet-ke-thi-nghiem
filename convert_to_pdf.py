import subprocess
import os

def convert_html_to_pdf(input_html, output_pdf):
    # Đường dẫn tới binary Prince thực tế trong thư mục cài đặt
    prince_bin = "./prince-install/lib/prince/bin/prince"
    prince_prefix = "./prince-install/lib/prince"
    
    if not os.path.exists(prince_bin):
        print(f"❌ Lỗi: Không tìm thấy binary Prince tại {prince_bin}")
        print("Vui lòng đảm bảo PrinceXML đã được cài đặt vào thư mục 'prince-install'.")
        return False
    
    if not os.path.exists(input_html):
        print(f"❌ Lỗi: Không tìm thấy file nguồn {input_html}")
        return False
    
    print(f"⏳ Đang chuyển đổi {input_html} sang {output_pdf}...")
    
    try:
        # Gọi lệnh prince để chuyển đổi
        subprocess.run([prince_bin, f"--prefix={prince_prefix}", input_html, "-o", output_pdf], check=True)
        print(f"✅ Thành công! File PDF đã được tạo tại: {output_pdf}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi trong quá trình chuyển đổi: {e}")
        return False

if __name__ == "__main__":
    convert_html_to_pdf("Proposal.html", "Proposal.pdf")
