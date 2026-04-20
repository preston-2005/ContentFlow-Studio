import gradio as gr

def get_saas_theme():
    """
    Returns a custom Gradio theme inspired by Enterprise B2B SaaS (Notion/Vercel).
    Features: Sleek dark mode, muted grays, and precise neon accents.
    """
    return gr.themes.Soft(
        primary_hue="sky", # Accent Blue (#38bdf8)
        secondary_hue="indigo", # Accent Purple (#818cf8)
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("Fira Code"), "ui-monospace", "SFMono-Regular", "monospace"],
    ).set(
        # Backgrounds
        body_background_fill="#121212",
        block_background_fill="#1E1E1E",
        block_border_color="#333333",
        
        # Accents
        button_primary_background_fill="*primary_500",
        button_primary_background_fill_hover="*primary_600",
        button_primary_text_color="white",
        
        # Text
        body_text_color="#E5E7EB",
        block_title_text_color="#38bdf8", # Sky Blue for titles
        
        # Inputs
        input_background_fill="#000000",
        input_border_color="#333333",
        input_border_color_focus="*primary_500",
        
        # Rounding
        block_radius="12px",
        container_radius="16px"
    )

CSS = """
/* Collapsible Terminal / Intelligence Logs */
.terminal-box {
    background-color: #000 !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
}

.terminal-box textarea {
    font-family: 'Fira Code', monospace !important;
    color: #38bdf8 !important;
    font-size: 0.85rem !important;
    line-height: 1.5 !important;
}

/* Sidebar Styling */
.sidebar-nav {
    border-right: 1px solid #333;
    height: 100vh;
    padding: 20px;
}

/* Script Editor */
.script-editor textarea {
    font-size: 1.1rem !important;
    line-height: 1.7 !important;
}

/* Primary Button Customization */
.primary-btn {
    background: linear-gradient(135deg, #38bdf8, #818cf8) !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(56, 189, 248, 0.2) !important;
}
"""
