from html import escape

def award_card(container, title, winner, detail, note=None):
    note_html = f'<div style="margin-top:8px;color:#35354d;font-size:.88rem;line-height:1.35;">{escape(str(note))}</div>' if note else ""
    container.markdown(
        f'''<div style="border:5px ridge #d8d8d8;padding:16px;margin:5px 0 16px;min-height:145px;background:#fff;box-shadow:5px 5px 0 #5454a8;overflow-wrap:anywhere;color:#111;">
        <div style="font:700 .92rem 'Courier New';color:#25255f;">{escape(str(title))}</div>
        <div style="font:700 1.65rem 'Trebuchet MS';line-height:1.15;margin:8px 0;color:#111;">{escape(str(winner))}</div>
        <div style="color:#004fbb;font-weight:700;line-height:1.3;">{escape(str(detail))}</div>
        {note_html}</div>''',
        unsafe_allow_html=True,
    )
