import io
import streamlit as st
from utils.ui import inject_global_css, header, section_header

from services.supabase_client import get_current_user, upload_style_file, list_style_files, delete_style_file


def auth_guard():
    user = get_current_user()
    if not user:
        st.error("Please login from the main page.")
        st.stop()
    return user


def _count_samples_in_files(files):
    """Count total samples across all uploaded files"""
    total_samples = 0
    for file_obj in files:
        try:
            # Try to read file content to count samples
            content = file_obj.get("content", "")
            if content:
                # Count lines that look like newsletter samples (non-empty, reasonable length)
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                samples = [line for line in lines if len(line) > 50]  # Reasonable sample length
                total_samples += len(samples)
        except:
            # If we can't read content, estimate based on file size
            file_size = file_obj.get("size", 0)
            estimated_samples = max(1, file_size // 1000)  # Rough estimate
            total_samples += estimated_samples
    return total_samples


def render():
    st.set_page_config(page_title="Style Upload — CreatorPulse", page_icon="📝", layout="wide")
    inject_global_css()
    user = auth_guard()
    header("Style Upload", "Upload .txt or .csv of past newsletters. Used to match your writing style.")

    # Get current files and show progress
    files = list_style_files(user_id=user["id"]) or []
    total_samples = _count_samples_in_files(files)
    
    # Progress meter
    section_header("Style Training Progress")
    target_samples = 20
    progress = min(total_samples / target_samples, 1.0)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(progress)
    with col2:
        st.metric("Samples", f"{total_samples}/{target_samples}")
    
    # Status message
    if total_samples >= target_samples:
        st.success("🎉 Excellent! You have enough style samples for high-quality AI generation.")
    elif total_samples >= 10:
        st.warning("📈 Good progress! Add more samples for even better style matching.")
    elif total_samples >= 5:
        st.info("📝 Getting started! Upload more newsletter samples to improve AI style matching.")
    else:
        st.error("⚠️ Upload at least 5 newsletter samples to enable style matching.")

    # Upload section
    section_header("Upload New Samples")
    uploaded = st.file_uploader("Upload style samples (.txt or .csv)", type=["txt", "csv"], accept_multiple_files=True)
    if uploaded:
        for f in uploaded:
            data = f.read()
            try:
                upload_style_file(user_id=user["id"], filename=f.name, data=data)
                st.success(f"Uploaded {f.name}")
            except Exception as e:
                st.error(f"Upload failed for {f.name}: {e}")
        st.rerun()  # Refresh to update progress

    # File management section
    section_header("Your Style Files")
    if not files:
        st.info("No style files uploaded yet. Upload some newsletter samples to get started!")
    else:
        for obj in files:
            cols = st.columns([3, 1, 1])
            cols[0].write(f"📄 {obj.get('name')}")
            
            # Show file info
            file_size = obj.get('size', 0)
            cols[1].write(f"{file_size:,} bytes")
            
            if cols[2].button("🗑️ Delete", key=f"del_{obj.get('name')}"):
                try:
                    delete_style_file(user_id=user["id"], filename=obj.get("name"))
                    st.success("Deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Delete failed: {e}")


if __name__ == "__main__":
    render()


