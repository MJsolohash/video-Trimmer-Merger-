import customtkinter as ctk
from tkinter import filedialog, messagebox
import ffmpeg
import cv2
from PIL import Image, ImageTk
import threading
import os
import tempfile
import subprocess
import re
import shutil

class ProfessionalVideoTrimmer(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Professional Video Trimmer & Merger - Full Control")
        self.geometry("1400x850")
        
        # Variables for Trimmer
        self.video_path = None
        self.total_duration = 0
        self.current_preview_time = 0
        self.start_time = 0
        self.end_time = 0
        self.cap = None
        self.is_playing = False
        self.play_thread = None
        
        # Variables for Merger
        self.merge_folder_path = None
        self.video_files_list = []
        
        self.setup_ui()
        self.bind_events()
        
    def setup_ui(self):
        # Create tabview for Trimmer and Merger
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        self.tabview.add("✂️ Video Trimmer")
        self.tabview.add("🔗 Video Merger")
        
        # ========== TRIMMER TAB ==========
        self.setup_trimmer_tab()
        
        # ========== MERGER TAB ==========
        self.setup_merger_tab()
        
    def setup_trimmer_tab(self):
        trimmer_tab = self.tabview.tab("✂️ Video Trimmer")
        
        # Main container
        main_container = ctk.CTkFrame(trimmer_tab)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Video Preview
        left_frame = ctk.CTkFrame(main_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Video display
        self.video_display = ctk.CTkLabel(left_frame, text="No Video Loaded", width=900, height=506)
        self.video_display.pack(pady=10)
        
        # Preview controls
        preview_controls = ctk.CTkFrame(left_frame)
        preview_controls.pack(fill="x", pady=5)
        
        ctk.CTkButton(preview_controls, text="⏮️ 5s", width=60, command=lambda: self.seek_preview(-5)).pack(side="left", padx=2)
        ctk.CTkButton(preview_controls, text="◀ 0.5s", width=60, command=lambda: self.seek_preview(-0.5)).pack(side="left", padx=2)
        ctk.CTkButton(preview_controls, text="▶ Play", width=60, command=self.toggle_play, fg_color="green").pack(side="left", padx=2)
        ctk.CTkButton(preview_controls, text="0.5s ▶", width=60, command=lambda: self.seek_preview(0.5)).pack(side="left", padx=2)
        ctk.CTkButton(preview_controls, text="5s ▶▶", width=60, command=lambda: self.seek_preview(5)).pack(side="left", padx=2)
        
        self.preview_time_label = ctk.CTkLabel(preview_controls, text="Time: 0.000s", font=("Arial", 12, "bold"))
        self.preview_time_label.pack(side="right", padx=10)
        
        # Right side - Controls
        right_frame = ctk.CTkFrame(main_container, width=450)
        right_frame.pack(side="right", fill="y")
        right_frame.pack_propagate(False)
        
        # File section
        file_section = ctk.CTkFrame(right_frame)
        file_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(file_section, text="📂 Open Video", command=self.open_video, height=45, font=("Arial", 14)).pack(fill="x")
        
        # Video info
        self.video_info = ctk.CTkTextbox(right_frame, height=80)
        self.video_info.pack(fill="x", padx=10, pady=5)
        
        # Manual Time Input
        manual_section = ctk.CTkFrame(right_frame)
        manual_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(manual_section, text="⏰ MANUAL TIME INPUT", font=("Arial", 16, "bold")).pack(pady=5)
        
        # Start Time
        start_frame = ctk.CTkFrame(manual_section)
        start_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(start_frame, text="Start Time:", width=80, font=("Arial", 13)).pack(side="left", padx=5)
        
        self.start_entry = ctk.CTkEntry(start_frame, width=140, font=("Arial", 13))
        self.start_entry.pack(side="left", padx=5)
        self.start_entry.insert(0, "00:00:00.000")
        
        ctk.CTkButton(start_frame, text="Set", width=50, command=self.apply_start_time, fg_color="#2ecc71").pack(side="left", padx=2)
        ctk.CTkButton(start_frame, text="+1s", width=45, command=lambda: self.adjust_start(1)).pack(side="left", padx=2)
        ctk.CTkButton(start_frame, text="-1s", width=45, command=lambda: self.adjust_start(-1)).pack(side="left", padx=2)
        ctk.CTkButton(start_frame, text="← Use Current", width=90, command=self.set_start_to_current).pack(side="left", padx=2)
        
        # End Time
        end_frame = ctk.CTkFrame(manual_section)
        end_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(end_frame, text="End Time:", width=80, font=("Arial", 13)).pack(side="left", padx=5)
        
        self.end_entry = ctk.CTkEntry(end_frame, width=140, font=("Arial", 13))
        self.end_entry.pack(side="left", padx=5)
        self.end_entry.insert(0, "00:00:05.000")
        
        ctk.CTkButton(end_frame, text="Set", width=50, command=self.apply_end_time, fg_color="#e74c3c").pack(side="left", padx=2)
        ctk.CTkButton(end_frame, text="+1s", width=45, command=lambda: self.adjust_end(1)).pack(side="left", padx=2)
        ctk.CTkButton(end_frame, text="-1s", width=45, command=lambda: self.adjust_end(-1)).pack(side="left", padx=2)
        ctk.CTkButton(end_frame, text="Use Current →", width=90, command=self.set_end_to_current).pack(side="left", padx=2)
        
        # Duration display
        duration_frame = ctk.CTkFrame(manual_section)
        duration_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(duration_frame, text="Duration:", font=("Arial", 13, "bold")).pack(side="left", padx=10)
        self.duration_label = ctk.CTkLabel(duration_frame, text="0.000s", font=("Arial", 15, "bold"), text_color="#2ecc71")
        self.duration_label.pack(side="left", padx=5)
        
        # Quick presets
        preset_frame = ctk.CTkFrame(manual_section)
        preset_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(preset_frame, text="Full Video", command=self.set_full_video).pack(side="left", padx=2, fill="x", expand=True)
        ctk.CTkButton(preset_frame, text="5s", command=lambda: self.set_duration_preset(5)).pack(side="left", padx=2, fill="x", expand=True)
        ctk.CTkButton(preset_frame, text="10s", command=lambda: self.set_duration_preset(10)).pack(side="left", padx=2, fill="x", expand=True)
        ctk.CTkButton(preset_frame, text="30s", command=lambda: self.set_duration_preset(30)).pack(side="left", padx=2, fill="x", expand=True)
        ctk.CTkButton(preset_frame, text="60s", command=lambda: self.set_duration_preset(60)).pack(side="left", padx=2, fill="x", expand=True)
        
        # Timeline
        timeline_section = ctk.CTkFrame(right_frame)
        timeline_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(timeline_section, text="📊 TIMELINE", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.timeline_slider = ctk.CTkSlider(timeline_section, from_=0, to=100, command=self.on_timeline_slider, height=15)
        self.timeline_slider.pack(fill="x", pady=5)
        
        slider_labels = ctk.CTkFrame(timeline_section)
        slider_labels.pack(fill="x")
        
        self.slider_start_label = ctk.CTkLabel(slider_labels, text="0:00", font=("Arial", 10))
        self.slider_start_label.pack(side="left")
        
        self.slider_mid_label = ctk.CTkLabel(slider_labels, text="", font=("Arial", 10))
        self.slider_mid_label.pack(side="left", expand=True)
        
        self.slider_end_label = ctk.CTkLabel(slider_labels, text="0:00", font=("Arial", 10))
        self.slider_end_label.pack(side="right")
        
        # Cut Mode
        mode_section = ctk.CTkFrame(right_frame)
        mode_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(mode_section, text="✂️ CUT MODE", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.cut_mode_var = ctk.StringVar(value="Keep Selected Range")
        mode_options = ["Keep Selected Range", "Remove Selected Range"]
        mode_menu = ctk.CTkComboBox(mode_section, values=mode_options, variable=self.cut_mode_var, width=200)
        mode_menu.pack(pady=5)
        
        # Export Options
        export_section = ctk.CTkFrame(right_frame)
        export_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(export_section, text="💾 EXPORT", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.quality_var = ctk.StringVar(value="Lossless (Fastest, No quality loss)")
        quality_menu = ctk.CTkComboBox(export_section, values=[
            "Lossless (Fastest, No quality loss)",
            "High Quality (H.264, Smaller file)",
            "Medium Quality",
            "Low Quality (Smallest file)"
        ], variable=self.quality_var, width=250)
        quality_menu.pack(pady=5)
        
        self.export_btn = ctk.CTkButton(export_section, text="🎬 EXPORT VIDEO", command=self.export_video, height=50, fg_color="#27ae60", font=("Arial", 14, "bold"))
        self.export_btn.pack(fill="x", pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(right_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(right_frame, text="Ready", font=("Arial", 11))
        self.status_label.pack(pady=5)
        
    def setup_merger_tab(self):
        merger_tab = self.tabview.tab("🔗 Video Merger")
        
        # Main container
        main_container = ctk.CTkFrame(merger_tab)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - File list
        left_frame = ctk.CTkFrame(main_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(left_frame, text="📁 Video Files (in merge order)", font=("Arial", 16, "bold")).pack(pady=5)
        
        # File listbox with scrollbar
        list_frame = ctk.CTkFrame(left_frame)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        self.merge_file_listbox = ctk.CTkTextbox(list_frame, height=400)
        self.merge_file_listbox.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(list_frame, orientation="vertical", command=self.merge_file_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.merge_file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Buttons for list management
        list_buttons_frame = ctk.CTkFrame(left_frame)
        list_buttons_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(list_buttons_frame, text="⬆ Move Up", width=80, command=self.move_file_up).pack(side="left", padx=2)
        ctk.CTkButton(list_buttons_frame, text="⬇ Move Down", width=80, command=self.move_file_down).pack(side="left", padx=2)
        ctk.CTkButton(list_buttons_frame, text="🗑 Remove Selected", width=100, command=self.remove_selected_file, fg_color="red").pack(side="left", padx=2)
        
        # Right side - Controls
        right_frame = ctk.CTkFrame(main_container, width=450)
        right_frame.pack(side="right", fill="y")
        right_frame.pack_propagate(False)
        
        # Folder selection
        folder_section = ctk.CTkFrame(right_frame)
        folder_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(folder_section, text="📂 Select Folder with Videos", command=self.select_merge_folder, height=45, font=("Arial", 14)).pack(fill="x")
        
        # Or add files individually
        ctk.CTkButton(folder_section, text="➕ Add Video Files", command=self.add_video_files, height=35, font=("Arial", 12)).pack(fill="x", pady=5)
        
        # Clear button
        ctk.CTkButton(folder_section, text="🗑 Clear All", command=self.clear_merge_list, height=35, fg_color="orange").pack(fill="x")
        
        # Merge options
        options_section = ctk.CTkFrame(right_frame)
        options_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(options_section, text="⚙️ MERGE OPTIONS", font=("Arial", 16, "bold")).pack(pady=5)
        
        # Merge method
        self.merge_method_var = ctk.StringVar(value="Fast Merge (Lossless)")
        method_menu = ctk.CTkComboBox(options_section, values=[
            "Fast Merge (Lossless)",
            "Re-encode Merge (Compatible)"
        ], variable=self.merge_method_var, width=250)
        method_menu.pack(pady=5)
        
        # Output filename
        output_frame = ctk.CTkFrame(options_section)
        output_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(output_frame, text="Output Name:", font=("Arial", 13)).pack(side="left", padx=5)
        self.merge_output_entry = ctk.CTkEntry(output_frame, width=200)
        self.merge_output_entry.pack(side="left", padx=5)
        self.merge_output_entry.insert(0, "merged_video.mp4")
        
        # Merge button
        self.merge_btn = ctk.CTkButton(right_frame, text="🔗 MERGE VIDEOS", command=self.merge_videos, height=50, fg_color="#27ae60", font=("Arial", 14, "bold"))
        self.merge_btn.pack(fill="x", padx=10, pady=10)
        
        # Progress
        self.merge_progress_bar = ctk.CTkProgressBar(right_frame)
        self.merge_progress_bar.pack(fill="x", padx=10, pady=5)
        self.merge_progress_bar.set(0)
        
        self.merge_status_label = ctk.CTkLabel(right_frame, text="Ready", font=("Arial", 11))
        self.merge_status_label.pack(pady=5)
        
        # Info text
        info_text = ctk.CTkTextbox(right_frame, height=150)
        info_text.pack(fill="x", padx=10, pady=10)
        info_text.insert("1.0", "📌 Instructions:\n\n1. Select folder with videos OR add files manually\n2. Files will be sorted by number (1.mp4, 2.mp4...)\n3. Use Move Up/Down to adjust order\n4. Choose merge method:\n   - Fast Merge: No quality loss\n   - Re-encode: Slower but 100% compatible\n5. Click Merge Videos")
        info_text.configure(state="disabled")
        
    # ========== MERGER METHODS ==========
    
    def select_merge_folder(self):
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return
        
        self.merge_folder_path = folder_path
        self.merge_status_label.configure(text=f"Loading videos from: {folder_path}", text_color="blue")
        
        # Get sorted video files
        self.video_files_list = self.get_sorted_video_files(folder_path)
        
        if len(self.video_files_list) < 2:
            self.merge_status_label.configure(text="Need at least 2 video files to merge!", text_color="red")
            messagebox.showwarning("Warning", "Need at least 2 video files to merge!")
            return
        
        # Display in listbox
        self.update_merge_listbox()
        self.merge_status_label.configure(text=f"Loaded {len(self.video_files_list)} videos", text_color="green")
        
    def get_sorted_video_files(self, folder_path):
        """Get video files sorted by numeric order"""
        video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.m4v', '.ts', '.webm')
        files = []
        
        for f in os.listdir(folder_path):
            if f.lower().endswith(video_extensions):
                # Extract number from filename
                match = re.search(r'(\d+)', f)
                if match:
                    num = int(match.group(1))
                    files.append((num, f))
                else:
                    files.append((float('inf'), f))
        
        files.sort(key=lambda x: x[0])
        return [f[1] for f in files]
    
    def add_video_files(self):
        files = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov *.ts *.webm")]
        )
        
        if not files:
            return
        
        for f in files:
            if f not in self.video_files_list:
                self.video_files_list.append(f)
        
        self.update_merge_listbox()
        self.merge_status_label.configure(text=f"Added {len(files)} videos. Total: {len(self.video_files_list)}", text_color="green")
    
    def update_merge_listbox(self):
        self.merge_file_listbox.configure(state="normal")
        self.merge_file_listbox.delete("1.0", "end")
        
        for i, file_path in enumerate(self.video_files_list, start=1):
            filename = os.path.basename(file_path)
            size = os.path.getsize(file_path) / (1024 * 1024)
            self.merge_file_listbox.insert("end", f"{i:3d}. {filename} ({size:.1f} MB)\n")
        
        self.merge_file_listbox.configure(state="disabled")
    
    def move_file_up(self):
        try:
            # Get current selection position
            selection = self.merge_file_listbox.index("insert")
            line_num = int(selection.split('.')[0]) if selection else 0
            
            if line_num > 1 and line_num <= len(self.video_files_list):
                idx = line_num - 1
                # Swap
                self.video_files_list[idx], self.video_files_list[idx-1] = self.video_files_list[idx-1], self.video_files_list[idx]
                self.update_merge_listbox()
        except:
            pass
    
    def move_file_down(self):
        try:
            selection = self.merge_file_listbox.index("insert")
            line_num = int(selection.split('.')[0]) if selection else 0
            
            if line_num >= 1 and line_num < len(self.video_files_list):
                idx = line_num - 1
                # Swap
                self.video_files_list[idx], self.video_files_list[idx+1] = self.video_files_list[idx+1], self.video_files_list[idx]
                self.update_merge_listbox()
        except:
            pass
    
    def remove_selected_file(self):
        try:
            selection = self.merge_file_listbox.index("insert")
            line_num = int(selection.split('.')[0]) if selection else 0
            
            if line_num >= 1 and line_num <= len(self.video_files_list):
                idx = line_num - 1
                del self.video_files_list[idx]
                self.update_merge_listbox()
                self.merge_status_label.configure(text=f"Removed. Total: {len(self.video_files_list)} videos", text_color="blue")
        except:
            pass
    
    def clear_merge_list(self):
        self.video_files_list = []
        self.update_merge_listbox()
        self.merge_status_label.configure(text="List cleared", text_color="blue")
    
    def convert_to_ts(self, folder_path, video_files):
        """Convert all videos to TS format for reliable merging"""
        ts_files = []
        
        for video_file in video_files:
            # Check if it's a full path or just filename
            if os.path.exists(video_file):
                input_path = video_file
            else:
                input_path = os.path.join(folder_path, video_file)
            
            output_ts = os.path.join(folder_path, f"temp_{os.path.basename(video_file)}.ts")
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c', 'copy', '-bsf:v', 'h264_mp4toannexb',
                '-f', 'mpegts', output_ts, '-y'
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                ts_files.append(output_ts)
                self.merge_status_label.configure(text=f"Converting: {os.path.basename(video_file)}...", text_color="blue")
                self.update()
            except subprocess.CalledProcessError as e:
                self.merge_status_label.configure(text=f"Failed to convert {video_file}", text_color="red")
                return None
        return ts_files
    
    def merge_videos_complete(self, folder_path, video_files, output_filename):
        """Complete merge solution using TS format"""
        
        # Create concat file
        concat_file = os.path.join(folder_path, "concat_list.txt")
        
        # Check if files are full paths or just names
        use_full_paths = os.path.exists(video_files[0]) if video_files else False
        
        with open(concat_file, 'w', encoding='utf-8') as f:
            for video_file in video_files:
                if use_full_paths:
                    abs_path = os.path.abspath(video_file).replace('\\', '/')
                else:
                    abs_path = os.path.join(folder_path, video_file).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        
        # Merge files
        output_path = os.path.join(folder_path, output_filename)
        
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            '-y', output_path
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr}")
            return False
        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)
    
    def merge_with_reencoding(self, folder_path, video_files, output_filename):
        """Merge with re-encoding (slower but more reliable)"""
        
        concat_file = os.path.join(folder_path, "concat_list.txt")
        
        use_full_paths = os.path.exists(video_files[0]) if video_files else False
        
        with open(concat_file, 'w', encoding='utf-8') as f:
            for video_file in video_files:
                if use_full_paths:
                    abs_path = os.path.abspath(video_file).replace('\\', '/')
                else:
                    abs_path = os.path.join(folder_path, video_file).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        
        output_path = os.path.join(folder_path, output_filename)
        
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', concat_file,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
            '-c:a', 'aac', '-b:a', '192k',
            '-movflags', '+faststart',
            '-y', output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)
    
    def merge_videos(self):
        """Main merge function"""
        if len(self.video_files_list) < 2:
            messagebox.showwarning("Warning", "Please add at least 2 video files to merge!")
            return
        
        output_filename = self.merge_output_entry.get().strip()
        if not output_filename:
            output_filename = "merged_video.mp4"
        if not output_filename.endswith('.mp4'):
            output_filename += '.mp4'
        
        # Get folder path
        if os.path.exists(self.video_files_list[0]):
            folder_path = os.path.dirname(self.video_files_list[0])
        else:
            folder_path = self.merge_folder_path
        
        if not folder_path or not os.path.exists(folder_path):
            messagebox.showerror("Error", "Invalid folder path!")
            return
        
        # Disable button during merge
        self.merge_btn.configure(state="disabled", text="Merging...")
        self.merge_progress_bar.set(0.2)
        
        def do_merge():
            try:
                method = self.merge_method_var.get()
                
                if method == "Fast Merge (Lossless)":
                    success = self.merge_videos_complete(folder_path, self.video_files_list, output_filename)
                else:
                    success = self.merge_with_reencoding(folder_path, self.video_files_list, output_filename)
                
                self.merge_progress_bar.set(1.0)
                
                if success:
                    output_path = os.path.join(folder_path, output_filename)
                    self.merge_status_label.configure(text=f"✅ Merge completed: {output_filename}", text_color="green")
                    messagebox.showinfo("Success", f"Videos merged successfully!\n\nOutput: {output_path}")
                else:
                    self.merge_status_label.configure(text="❌ Merge failed!", text_color="red")
                    messagebox.showerror("Error", "Merge failed!\n\nTry using Re-encode method.")
            
            except Exception as e:
                self.merge_status_label.configure(text=f"Error: {str(e)}", text_color="red")
                messagebox.showerror("Error", f"Merge failed:\n{str(e)}")
            
            finally:
                self.merge_progress_bar.set(0)
                self.merge_btn.configure(state="normal", text="🔗 MERGE VIDEOS")
        
        thread = threading.Thread(target=do_merge)
        thread.start()
    
    # ========== TRIMMER METHODS (Existing) ==========
    
    def bind_events(self):
        self.start_entry.bind('<Return>', lambda e: self.apply_start_time())
        self.end_entry.bind('<Return>', lambda e: self.apply_end_time())
        self.start_entry.bind('<FocusOut>', lambda e: self.apply_start_time())
        self.end_entry.bind('<FocusOut>', lambda e: self.apply_end_time())
        
    def time_to_seconds(self, time_str):
        if not time_str:
            return 0
        time_str = time_str.strip()
        try:
            return float(time_str)
        except:
            pass
        try:
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 3:
                    hours = float(parts[0])
                    minutes = float(parts[1])
                    seconds = float(parts[2])
                    return hours * 3600 + minutes * 60 + seconds
                elif len(parts) == 2:
                    minutes = float(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
        except:
            pass
        return 0
        
    def seconds_to_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
        
    def apply_start_time(self):
        try:
            time_str = self.start_entry.get()
            new_time = self.time_to_seconds(time_str)
            if new_time < 0:
                new_time = 0
            if new_time >= self.end_time and self.total_duration > 0:
                new_time = self.end_time - 0.1
            if self.total_duration > 0 and new_time > self.total_duration:
                new_time = self.total_duration - 0.1
            self.start_time = new_time
            self.update_display()
            self.update_preview_at_time(self.start_time)
            self.status_label.configure(text=f"Start time set to {self.seconds_to_time(self.start_time)}", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}", text_color="red")
            
    def apply_end_time(self):
        try:
            time_str = self.end_entry.get()
            new_time = self.time_to_seconds(time_str)
            if new_time <= self.start_time:
                new_time = self.start_time + 0.1
            if self.total_duration > 0 and new_time > self.total_duration:
                new_time = self.total_duration
            self.end_time = new_time
            self.update_display()
            self.status_label.configure(text=f"End time set to {self.seconds_to_time(self.end_time)}", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}", text_color="red")
            
    def adjust_start(self, delta):
        new_time = self.start_time + delta
        if new_time < 0:
            new_time = 0
        if new_time >= self.end_time:
            new_time = self.end_time - 0.1
        if self.total_duration > 0 and new_time > self.total_duration:
            new_time = self.total_duration - 0.1
        self.start_time = new_time
        self.update_display()
        self.update_preview_at_time(self.start_time)
        
    def adjust_end(self, delta):
        new_time = self.end_time + delta
        if new_time <= self.start_time:
            new_time = self.start_time + 0.1
        if self.total_duration > 0 and new_time > self.total_duration:
            new_time = self.total_duration
        self.end_time = new_time
        self.update_display()
        
    def set_start_to_current(self):
        self.start_time = self.current_preview_time
        if self.start_time >= self.end_time:
            self.end_time = min(self.start_time + 1, self.total_duration)
        self.update_display()
        self.update_preview_at_time(self.start_time)
        self.status_label.configure(text=f"Start set to current position: {self.seconds_to_time(self.start_time)}")
        
    def set_end_to_current(self):
        self.end_time = self.current_preview_time
        if self.end_time <= self.start_time:
            self.start_time = max(0, self.end_time - 1)
        self.update_display()
        self.status_label.configure(text=f"End set to current position: {self.seconds_to_time(self.end_time)}")
        
    def set_full_video(self):
        if self.total_duration > 0:
            self.start_time = 0
            self.end_time = self.total_duration
            self.update_display()
            self.update_preview_at_time(0)
            self.status_label.configure(text="Set to full video")
            
    def set_duration_preset(self, seconds):
        if self.start_time + seconds <= self.total_duration:
            self.end_time = self.start_time + seconds
        else:
            self.end_time = self.total_duration
            self.start_time = max(0, self.total_duration - seconds)
        self.update_display()
        self.status_label.configure(text=f"Duration set to {seconds}s")
        
    def update_display(self):
        self.start_entry.delete(0, 'end')
        self.start_entry.insert(0, self.seconds_to_time(self.start_time))
        self.end_entry.delete(0, 'end')
        self.end_entry.insert(0, self.seconds_to_time(self.end_time))
        duration = self.end_time - self.start_time
        self.duration_label.configure(text=f"{duration:.3f} seconds")
        if self.total_duration > 0:
            slider_pos = (self.start_time / self.total_duration) * 100
            self.timeline_slider.set(slider_pos)
            self.slider_start_label.configure(text=self.seconds_to_time(self.start_time)[3:])
            self.slider_end_label.configure(text=self.seconds_to_time(self.end_time)[3:])
            mid_time = (self.start_time + self.end_time) / 2
            self.slider_mid_label.configure(text=self.seconds_to_time(mid_time)[3:])
            
    def on_timeline_slider(self, value):
        if self.total_duration > 0:
            self.start_time = (value / 100) * self.total_duration
            if self.start_time >= self.end_time:
                self.end_time = min(self.start_time + 1, self.total_duration)
            self.update_display()
            self.update_preview_at_time(self.start_time)
            
    def seek_preview(self, delta):
        new_time = self.current_preview_time + delta
        if 0 <= new_time <= self.total_duration:
            self.current_preview_time = new_time
            self.update_preview_at_time(self.current_preview_time)
            
    def toggle_play(self):
        if self.is_playing:
            self.is_playing = False
        else:
            self.is_playing = True
            self.play_video()
            
    def play_video(self):
        if not self.is_playing or not self.video_path:
            return
        if self.current_preview_time >= self.total_duration:
            self.current_preview_time = 0
        self.update_preview_at_time(self.current_preview_time)
        self.current_preview_time += 0.033
        self.after(33, self.play_video)
        
    def get_keyframe_times(self, video_path):
        try:
            cmd = [
                'ffprobe', '-select_streams', 'v:0', '-show_frames',
                '-show_entries', 'frame=pkt_pts_time,pict_type',
                '-of', 'csv', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            keyframes = []
            for line in result.stdout.split('\n'):
                if line.startswith('I,'):
                    parts = line.split(',')
                    if len(parts) >= 2:
                        try:
                            time_val = float(parts[1])
                            keyframes.append(time_val)
                        except:
                            pass
            return keyframes
        except:
            return []
            
    def find_nearest_keyframe(self, time_seconds, keyframes):
        if not keyframes:
            return time_seconds
        nearest = min(keyframes, key=lambda x: abs(x - time_seconds))
        if abs(nearest - time_seconds) <= 0.5:
            return nearest
        return time_seconds
        
    def open_video(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.ts *.mts *.webm")]
        )
        if not file_path:
            return
        self.video_path = file_path
        self.status_label.configure(text="Loading video...")
        try:
            probe = ffmpeg.probe(self.video_path)
            self.total_duration = float(probe['format']['duration'])
            self.end_time = self.total_duration
            video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
            if video_stream:
                width = video_stream.get('width', '?')
                height = video_stream.get('height', '?')
                codec = video_stream.get('codec_name', '?')
                fps = video_stream.get('r_frame_rate', '?')
                info = f"📹 Resolution: {width}×{height}\n🎬 Codec: {codec}\n⚡ FPS: {fps}\n⏱️ Duration: {self.seconds_to_time(self.total_duration)}"
                self.video_info.delete("1.0", "end")
                self.video_info.insert("1.0", info)
            self.update_display()
            self.update_preview_at_time(0)
            self.slider_end_label.configure(text=self.seconds_to_time(self.total_duration)[3:])
            self.status_label.configure(text="Video loaded successfully!", text_color="green")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load video: {str(e)}")
            self.status_label.configure(text="Error loading video", text_color="red")
            
    def update_preview_at_time(self, time_seconds):
        if not self.video_path:
            return
        self.preview_time_label.configure(text=f"Time: {time_seconds:.3f}s")
        try:
            cap = cv2.VideoCapture(self.video_path)
            cap.set(cv2.CAP_PROP_POS_MSEC, time_seconds * 1000)
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w = frame_rgb.shape[:2]
                display_width = 900
                display_height = 506
                scale = min(display_width / w, display_height / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                frame_resized = cv2.resize(frame_rgb, (new_w, new_h))
                image = Image.fromarray(frame_resized)
                photo = ImageTk.PhotoImage(image)
                self.video_display.configure(image=photo, text="")
                self.video_display.image = photo
            cap.release()
        except Exception as e:
            pass
            
    def export_video(self):
        if not self.video_path:
            messagebox.showwarning("Warning", "Please load a video first")
            return
        if self.start_time >= self.end_time:
            messagebox.showwarning("Warning", "Start time must be less than end time")
            return
        overwrite = messagebox.askyesno(
            "Save Option",
            f"Do you want to OVERWRITE the original file?\n\n"
            f"Original: {os.path.basename(self.video_path)}\n\n"
            f"⚠️ WARNING: This will PERMANENTLY delete the cut portions!\n"
            f"Click YES to overwrite (permanent cut)\n"
            f"Click NO to save as new file"
        )
        if overwrite:
            output_path = self.video_path
            backup_path = self.video_path + ".backup.mp4"
            shutil.copy2(self.video_path, backup_path)
            self.status_label.configure(text="Creating backup...", text_color="blue")
            self.update()
        else:
            output_path = filedialog.asksaveasfilename(
                defaultextension=".mp4",
                filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
            )
            if not output_path:
                return
            backup_path = None
        thread = threading.Thread(target=self._do_export, args=(output_path, backup_path, overwrite))
        thread.start()
        
    def _do_export(self, output_path, backup_path, overwrite_original):
        try:
            self.progress_bar.set(0.1)
            self.status_label.configure(text="Analyzing video...", text_color="blue")
            keyframes = self.get_keyframe_times(self.video_path)
            adjusted_start = self.find_nearest_keyframe(self.start_time, keyframes)
            adjusted_end = self.find_nearest_keyframe(self.end_time, keyframes)
            quality = self.quality_var.get()
            cut_mode = self.cut_mode_var.get()
            self.progress_bar.set(0.3)
            self.status_label.configure(text="Exporting...", text_color="blue")
            
            if quality == "Lossless (Fastest, No quality loss)":
                if cut_mode == "Keep Selected Range":
                    cmd = [
                        'ffmpeg', '-ss', str(adjusted_start), '-i', self.video_path,
                        '-to', str(adjusted_end - adjusted_start),
                        '-c', 'copy', '-avoid_negative_ts', 'make_zero',
                        '-fflags', '+genpts', output_path, '-y'
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise Exception(f"FFmpeg error: {result.stderr}")
                else:
                    temp_files = []
                    if adjusted_start > 0:
                        temp1 = tempfile.mktemp(suffix='.mp4')
                        temp_files.append(temp1)
                        cmd1 = ['ffmpeg', '-i', self.video_path, '-t', str(adjusted_start),
                                '-c', 'copy', '-avoid_negative_ts', 'make_zero', temp1, '-y']
                        subprocess.run(cmd1, capture_output=True)
                    if adjusted_end < self.total_duration:
                        temp2 = tempfile.mktemp(suffix='.mp4')
                        temp_files.append(temp2)
                        cmd2 = ['ffmpeg', '-ss', str(adjusted_end), '-i', self.video_path,
                                '-c', 'copy', '-avoid_negative_ts', 'make_zero', temp2, '-y']
                        subprocess.run(cmd2, capture_output=True)
                    valid_files = [f for f in temp_files if os.path.exists(f) and os.path.getsize(f) > 1000]
                    if len(valid_files) == 0:
                        raise Exception("No valid video parts created")
                    elif len(valid_files) == 1:
                        shutil.copy2(valid_files[0], output_path)
                    else:
                        concat_file = tempfile.mktemp(suffix='.txt')
                        with open(concat_file, 'w') as f:
                            for file in valid_files:
                                abs_path = os.path.abspath(file).replace('\\', '/')
                                f.write(f"file '{abs_path}'\n")
                        cmd_concat = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file,
                                      '-c', 'copy', output_path, '-y']
                        subprocess.run(cmd_concat, capture_output=True)
                        os.remove(concat_file)
                    for f in temp_files:
                        if os.path.exists(f):
                            os.remove(f)
            else:
                quality_settings = {
                    "High Quality (H.264, Smaller file)": {"crf": 18, "preset": "slow"},
                    "Medium Quality": {"crf": 23, "preset": "medium"},
                    "Low Quality (Smallest file)": {"crf": 28, "preset": "fast"}
                }
                settings = quality_settings.get(quality, {"crf": 23, "preset": "medium"})
                if cut_mode == "Keep Selected Range":
                    cmd = [
                        'ffmpeg', '-ss', str(self.start_time), '-i', self.video_path,
                        '-to', str(self.end_time - self.start_time),
                        '-c:v', 'libx264', '-crf', str(settings['crf']),
                        '-preset', settings['preset'], '-c:a', 'aac', '-b:a', '128k',
                        output_path, '-y'
                    ]
                else:
                    cmd = [
                        'ffmpeg', '-i', self.video_path,
                        '-filter_complex',
                        f"[0:v]trim=start={self.end_time}:end={self.total_duration},setpts=PTS-STARTPTS[v2];"
                        f"[0:v]trim=start=0:end={self.start_time},setpts=PTS-STARTPTS[v1];"
                        f"[v1][v2]concat=n=2:v=1:a=0[outv];"
                        f"[0:a]atrim=start={self.end_time}:end={self.total_duration},asetpts=PTS-STARTPTS[a2];"
                        f"[0:a]atrim=start=0:end={self.start_time},asetpts=PTS-STARTPTS[a1];"
                        f"[a1][a2]concat=n=2:v=0:a=1[outa]",
                        '-map', '[outv]', '-map', '[outa]',
                        '-c:v', 'libx264', '-crf', str(settings['crf']),
                        '-preset', settings['preset'], '-c:a', 'aac',
                        output_path, '-y'
                    ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"FFmpeg error: {result.stderr}")
            
            self.progress_bar.set(1.0)
            if overwrite_original and backup_path and os.path.exists(backup_path):
                os.remove(backup_path)
                self.status_label.configure(text="Original file UPDATED!", text_color="green")
                messagebox.showinfo("Success", "Original file has been permanently updated!")
            else:
                self.status_label.configure(text="Export completed!", text_color="green")
                messagebox.showinfo("Success", f"Video exported successfully!\n{output_path}")
        except Exception as e:
            if overwrite_original and backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, self.video_path)
                os.remove(backup_path)
                self.status_label.configure(text="Export failed! Original restored.", text_color="red")
                messagebox.showerror("Error", f"Export failed!\n\nError: {str(e)}")
            else:
                self.status_label.configure(text="Export failed!", text_color="red")
                messagebox.showerror("Error", f"Export failed:\n{str(e)}")
        finally:
            self.progress_bar.set(0)
            
    def on_closing(self):
        if self.cap:
            self.cap.release()
        self.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = ProfessionalVideoTrimmer()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
