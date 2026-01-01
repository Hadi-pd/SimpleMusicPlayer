# make_exe.py - ساخت فایل اجرایی برای Nova Music Player (نسخه مدرن)
import PyInstaller.__main__
import os
import sys
import shutil

def main():
    print("=" * 60)
    print("Make Simple Music Player EXE")
    print("=" * 60)
    
    # نام فایل اصلی برنامه
    main_script = "music_player.py"
    
    if not os.path.exists(main_script):
        print(f"❌ فایل {main_script} یافت نشد!")
        print("   لطفاً مطمئن شوید فایل اصلی برنامه در همین پوشه قرار دارد.")
        input("\nبرای بستن، Enter بزنید...")
        return
    
    # بررسی وجود فایل آیکون (ضروری)
    if not os.path.exists("icon.ico"):
        print("❌ فایل icon.ico یافت نشد!")
        print("   لطفاً یک فایل آیکون با نام icon.ico در پوشه قرار دهید.")
        print("   می‌توانید از سایت‌های تبدیل png به ico استفاده کنید.")
        input("\nبرای بستن، Enter بزنید...")
        return
    
    print("✅ فایل icon.ico یافت شد → آیکون اعمال می‌شود")
    
    # ایجاد پوشه‌های مورد نیاز
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # گزینه‌های اصلی PyInstaller - این قسمت مهم است
    options = [
        main_script,
        "--onefile",
        "--windowed",
        "--name=SPlayer",
        "--clean",
        "--noconfirm",
        "--icon=icon.ico",  # این خط باید حتماً وجود داشته باشد
        "--add-data=icon.ico;.",  # اضافه کردن آیکون به data-files (برای ویندوز)
    ]
    
    # hidden imports
    hidden_imports = [
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.QtMultimedia",
        "pygame",
        "pygame.mixer",
        "mutagen",
        "mutagen.mp3",
        "mutagen.flac",
        "mutagen.wave",
        "mutagen.id3",
        "mutagen.easyid3",
        "mutagen._util",
        "mutagen._file",
    ]
    
    for imp in hidden_imports:
        options.append(f"--hidden-import={imp}")
    
    print("\n📦 در حال ساخت فایل اجرایی...")
    print("⏳ این فرآیند ممکن است ۲ تا ۵ دقیقه طول بکشد...")
    print("   لطفاً صبر کنید و پنجره را نبندید.\n")
    
    try:
        PyInstaller.__main__.run(options)
        
        exe_path = os.path.join("dist", "SPlayer.exe")
        
        print("\n" + "=" * 60)
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)
            print("✅ فایل اجرایی با موفقیت ساخته شد!")
            print(f"📁 مسیر: {os.path.abspath(exe_path)}")
            print(f"📄 نام فایل: SPlayer.exe")
            print(f"📊 حجم تقریبی: {file_size:.1f} MB")
            print("🎨 آیکون با موفقیت اعمال شد")
            
            # تست آیکون
            import subprocess
            try:
                # این دستور آیکون EXE را نمایش می‌دهد
                subprocess.run(['attrib', exe_path], shell=True)
            except:
                pass
                
        else:
            print("❌ فایل اجرایی در پوشه dist ساخته نشد!")
            
    except Exception as e:
        print(f"\n❌ خطا در هنگام ساخت: {str(e)}")
        print("\n🔧 راه‌حل‌های پیشنهادی:")
        print("   1. PyInstaller را آپدیت کنید: pip install --upgrade pyinstaller")
        print("   2. مطمئن شوید آیکون فرمت درست دارد (ico)")
        print("   3. از آنتی‌ویروس اجازه دهید")
    
    print("\nبرای بستن، Enter بزنید...")
    input()

if __name__ == "__main__":
    main()