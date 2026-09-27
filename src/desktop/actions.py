"""Host actions are only called by the desktop application."""
def open_chatbot(prompt: str, url: str):
    import pyperclip
    import webbrowser
    pyperclip.copy(prompt)
    webbrowser.open(url)
