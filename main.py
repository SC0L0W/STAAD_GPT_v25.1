from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Scrollbar, messagebox
from pathlib import Path
import threading
import logging
from typing import Optional, List, Dict
from core.staad_controller import GeometryController
import re
import webbrowser


# === Configuration ===
class Config:
    """Application configuration"""
    WINDOW_WIDTH = 500
    WINDOW_HEIGHT = 720
    WINDOW_TITLE = "STAAD GPT"
    BG_COLOR = "#FFFFFF"
    TEXT_BG = "#494D55"
    TEXT_FG = "#FFFFFF"
    INPUT_BG = "#B2B6BD"
    INPUT_FG = "#000716"
    LOADING_COLOR = "#FFD580"

    # Text area dimensions
    TEXT_X = 70
    TEXT_Y = 124
    TEXT_WIDTH = 363
    TEXT_HEIGHT = 380

    # Font configurations
    FONT_MAIN = ("Inter", 12)
    FONT_ITALIC = ("Inter", 12, "italic")
    FONT_BOLD = ("Arial", 12, "bold")

    # AI Configuration
    MAX_HISTORY = 10  # Keep last 10 messages for context
    MAX_RETRIES = 2  # Number of retries on failure


# === Setup Logging ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === Paths ===
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets" / "frame0"


def asset(path: str) -> Path:
    """Helper function to fetch asset paths"""
    return ASSETS_DIR / path


class AIProvider:
    """Handles AI API interactions using g4f with ChatGPT web login support"""

    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = (
            "You are an expert assistant for Structural Engineers using STAAD.Pro software. "
            "You have deep knowledge of structural analysis, finite element methods, beam theory, "
            "material properties, load cases, and the OpenSTAAD API. "
            "Provide clear, professional, and accurate responses. "
            "When suggesting code, use Python with the OpenSTAAD API. "
            "Always consider safety factors and engineering best practices. "
            "Keep responses concise but informative."
        )
        self.client = None
        self.current_provider = None
        self.login_attempted = False

    def initialize_g4f(self):
        """Initialize g4f client with multiple provider options"""
        try:
            from g4f.client import Client
            self.client = Client()
            logger.info("g4f client initialized successfully")
            return True

        except ImportError:
            logger.error("g4f library not installed")
            return False
        except Exception as e:
            logger.error(f"Error initializing g4f: {e}")
            return False

    def prompt_chatgpt_login(self):
        """Prompt user to login to ChatGPT for better responses"""
        if self.login_attempted:
            return
        self.login_attempted = True

        response = messagebox.askyesno(
            "Enhanced AI Experience",
            "For better AI responses, you can login to ChatGPT in your browser.\n\n"
            "Would you like to open ChatGPT login page?\n\n"
            "After logging in, restart this application for improved responses.",
            icon='question'
        )

        if response:
            webbrowser.open("https://chat.openai.com/")
            messagebox.showinfo(
                "Login Instructions",
                "1. Login to ChatGPT in the browser that opened\n"
                "2. After successful login, restart this application\n"
                "3. g4f will automatically use your session for better responses\n\n"
                "Note: This is optional. The app works without login too!"
            )

    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > Config.MAX_HISTORY * 2:
            self.conversation_history = self.conversation_history[-Config.MAX_HISTORY * 2:]

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

    def get_response(self, prompt: str) -> str:
        """Get AI response using g4f with multiple fallbacks"""
        if self.client is None:
            if not self.initialize_g4f():
                return (
                    "❌ g4f library is not installed.\n\n"
                    "Please install it using:\n"
                    "pip install -U g4f\n\n"
                    "Then restart the application."
                )

        messages = [{"role": "user", "content": f"{self.system_prompt}\n\nUser question: {prompt}"}]

        if self.conversation_history:
            history_text = "\n\nPrevious conversation:\n"
            for msg in self.conversation_history[-4:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_text += f"{role}: {msg['content'][:100]}...\n"
            messages[0]["content"] = history_text + messages[0]["content"]

        last_error = None
        attempts = 0
        max_attempts = 3

        while attempts < max_attempts:
            try:
                attempts += 1
                logger.info(f"Attempt {attempts}/{max_attempts}")
                response = self.client.chat.completions.create(
                    model="",
                    messages=messages,
                    stream=False
                )

                if response:
                    if hasattr(response, 'choices') and response.choices:
                        content = response.choices[0].message.content.strip()
                    elif isinstance(response, str):
                        content = response.strip()
                    else:
                        content = str(response).strip()

                    if content and len(content) > 5 and "login" not in content.lower():
                        logger.info(f"✓ Success on attempt {attempts}")
                        self.add_to_history("user", prompt)
                        self.add_to_history("assistant", content)
                        return content
                    else:
                        last_error = "Invalid or empty response"

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempts} failed: {e}")
                if attempts < max_attempts:
                    import time
                    time.sleep(1)
                continue

        logger.error(f"All {max_attempts} attempts failed. Last error: {last_error}")

        if "login" in str(last_error).lower() or "authentication" in str(last_error).lower():
            if not self.login_attempted:
                self.prompt_chatgpt_login()
            return (
                "⚠️ Provider requires authentication.\n\n"
                "Would you like to:\n"
                "1. Try again in a moment (providers rotate)\n"
                "2. Update g4f: pip install -U g4f\n"
                "3. Login to ChatGPT for better access (click 'Clear' button)\n\n"
                "The service is free but sometimes busy. Please try again!"
            )

        return (
            "⚠️ AI service temporarily unavailable.\n\n"
            "Quick fixes:\n"
            "1. ✅ Check your internet connection\n"
            "2. ⏰ Wait 30 seconds and try again\n"
            "3. 🔄 Update g4f: pip install -U g4f\n"
            "4. 🌐 Try a VPN if blocked in your region\n\n"
            "g4f uses free providers that can be busy.\n"
            f"Details: {last_error[:200]}"
        )


class STAADCommandParser:
    """Enhanced parser for STAAD-specific commands"""

    @staticmethod
    def parse_node_command(prompt: str) -> Optional[Dict]:
        patterns = {
            'coordinates': r'(?:coordinates?|coords?|position)\s+(?:of\s+)?node\s*[#]?(\d+)',
            'create_node': r'create\s+node\s+at\s+\(?(-?[\d.]+)[,\s]+(-?[\d.]+)[,\s]+(-?[\d.]+)\)?',
            'delete_node': r'delete\s+node\s*[#]?(\d+)',
            'move_node': r'move\s+node\s*[#]?(\d+)\s+to\s+\(?(-?[\d.]+)[,\s]+(-?[\d.]+)[,\s]+(-?[\d.]+)\)?',
        }
        for cmd_type, pattern in patterns.items():
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return {'type': cmd_type, 'params': match.groups()}
        return None

    @staticmethod
    def parse_beam_command(prompt: str) -> Optional[Dict]:
        patterns = {
            'beam_length': r'(?:length\s+of\s+)?beam\s*[#]?(\d+)',
            'selected_beams': r'selected\s+beams?',
            'create_beam': r'create\s+beam\s+(?:from\s+)?node\s*[#]?(\d+)\s+to\s+node\s*[#]?(\d+)',
            'beam_properties': r'(?:properties|props?)\s+(?:of\s+)?beam\s*[#]?(\d+)',
        }
        for cmd_type, pattern in patterns.items():
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return {'type': cmd_type, 'params': match.groups() if match.groups() else None}
        return None

    @staticmethod
    def parse_model_command(prompt: str) -> Optional[Dict]:
        patterns = {
            'last_node': r'last\s+node(?:\s+number)?',
            'last_beam': r'last\s+beam(?:\s+number)?',
            'total_nodes': r'(?:total|count)\s+nodes?',
            'total_beams': r'(?:total|count)\s+beams?',
            'create_file': r'create\s+(?:new\s+)?(?:staad\s+)?file\s+at\s+["\']?(.+\.std)["\']?',
        }
        for cmd_type, pattern in patterns.items():
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return {'type': cmd_type, 'params': match.groups() if match.groups() else None}
        return None

class STAADGPTApp:
    """Main application class for STAAD GPT"""

    def __init__(self):
        self.window = None
        self.canvas = None
        self.text_area = None
        self.loading_label = None
        self.user_input = None
        self.images = {}

        # Initialize AI provider
        self.ai_provider = AIProvider()
        self.command_parser = STAADCommandParser()

        # Initialize STAAD geometry controller
        self.geometry = self._initialize_geometry()

    def _initialize_geometry(self) -> Optional[GeometryController]:
        """Initialize geometry controller with error handling"""
        try:
            return GeometryController()
        except RuntimeError as e:
            logger.warning(f"STAAD connection failed: {e}")
            messagebox.showwarning(
                "STAAD Not Connected",
                "STAAD.Pro is not open or no model is loaded.\n"
                "Some features may be unavailable."
            )
            return None

    def setup_window(self):
        """Initialize and configure the main window"""
        self.window = Tk()
        self.window.title(Config.WINDOW_TITLE)
        self.window.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
        self.window.configure(bg=Config.BG_COLOR)
        self.window.resizable(False, False)

        try:
            self.window.iconbitmap(asset("icon.ico"))
        except Exception as e:
            logger.warning(f"Could not load icon: {e}")

        # Setup canvas
        self.canvas = Canvas(
            self.window,
            bg=Config.BG_COLOR,
            height=Config.WINDOW_HEIGHT,
            width=Config.WINDOW_WIDTH,
            bd=0,
            highlightthickness=0
        )
        self.canvas.place(x=0, y=0)

    def add_image(self, name: str, x: int, y: int):
        """Add an image to the canvas at specified position"""
        try:
            img = PhotoImage(file=asset(name))
            self.images[name] = img
            self.canvas.create_image(x, y, image=img)
        except Exception as e:
            logger.error(f"Failed to load image {name}: {e}")

    def setup_images(self):
        """Load and place all images"""
        image_data = [
            ("image_1.png", 250, 374),
            ("image_2.png", 258, 83),
            ("image_3.png", 249, 708),
            ("image_4.png", 250, 24),
            ("image_5.png", 475, 24)
        ]
        for image, x, y in image_data:
            self.add_image(image, x, y)

    def setup_text_area(self):
        """Configure the text output area with scrollbar"""
        self.text_area = Text(
            self.window,
            bg=Config.TEXT_BG,
            fg=Config.TEXT_FG,
            wrap="word",
            font=Config.FONT_MAIN,
            bd=0,
            highlightthickness=0,
            state="disabled"
        )
        self.text_area.place(
            x=Config.TEXT_X,
            y=Config.TEXT_Y,
            width=Config.TEXT_WIDTH,
            height=Config.TEXT_HEIGHT
        )

        # Add scrollbar
        scrollbar = Scrollbar(self.window, command=self.text_area.yview)
        scrollbar.place(x=435, y=124, height=415)
        self.text_area.config(yscrollcommand=scrollbar.set)

        # Configure text tags
        self.text_area.tag_configure(
            "bold_green",
            font=Config.FONT_BOLD,
            foreground="#A9FFA9"
        )
        self.text_area.tag_configure(
            "bold_blue",
            font=Config.FONT_BOLD,
            foreground="#A0D8FF"
        )
        self.text_area.tag_configure(
            "error",
            font=Config.FONT_BOLD,
            foreground="#FF6B6B"
        )
        self.text_area.tag_configure(
            "warning",
            font=Config.FONT_BOLD,
            foreground="#FFD580"
        )

    def setup_loading_label(self):
        """Configure the loading indicator"""
        self.loading_label = Text(
            self.window,
            bg=Config.TEXT_BG,
            fg=Config.LOADING_COLOR,
            font=Config.FONT_ITALIC,
            bd=0,
            wrap="word",
            highlightthickness=0,
            state="disabled"
        )
        self.loading_label.place(x=70, y=470, width=363, height=25)

    def setup_input_field(self):
        """Configure the user input field"""
        self.user_input = Entry(
            self.window,
            bd=0,
            bg=Config.INPUT_BG,
            fg=Config.INPUT_FG,
            highlightthickness=0
        )
        self.user_input.place(x=70, y=500, width=363, height=40)
        self.user_input.bind("<Return>", lambda e: self.send_message())

    def setup_buttons(self):
        """Configure application buttons"""
        try:
            btn1 = PhotoImage(file=asset("button_1.png"))
            Button(
                self.window,
                image=btn1,
                bd=0,
                relief="flat",
                command=self.clear_conversation
            ).place(x=219, y=566, width=66, height=20)
            self.images["button_1"] = btn1

            btn2 = PhotoImage(file=asset("button_2.png"))
            Button(
                self.window,
                image=btn2,
                bd=0,
                relief="flat",
                command=self.send_message
            ).place(x=150, y=601, width=200, height=50)
            self.images["button_2"] = btn2
        except Exception as e:
            logger.error(f"Failed to load buttons: {e}")

    def show_loading(self):
        """Display loading indicator"""
        self.loading_label.config(state="normal")
        self.loading_label.delete("1.0", "end")
        self.loading_label.insert("end", "Getting response from AI...")
        self.loading_label.config(state="disabled")

    def hide_loading(self):
        """Hide loading indicator"""
        self.loading_label.config(state="normal")
        self.loading_label.delete("1.0", "end")
        self.loading_label.config(state="disabled")

    def display_message(self, sender: str, message: str, tag: str):
        """Display a message in the text area"""
        self.text_area.config(state="normal")
        self.text_area.insert("end", f"{sender}: ", tag)
        self.text_area.insert("end", f"{message}\n\n")
        self.text_area.config(state="disabled")
        self.text_area.yview_moveto(1.0)

    def execute_staad_command(self, command_dict: Dict) -> Optional[str]:
        """Execute STAAD commands based on parsed input"""
        if not self.geometry:
            return "⚠️ STAAD.Pro is not connected. Please open STAAD and load a model."

        try:
            cmd_type = command_dict['type']
            params = command_dict.get('params')

            # Node commands
            if cmd_type == 'coordinates':
                node = int(params[0])
                x, y, z = self.geometry.get_node_coordinates(node)
                return f"📍 Node {node} Coordinates:\n  X = {x:.3f} m\n  Y = {y:.3f} m\n  Z = {z:.3f} m"

            elif cmd_type == 'last_node':
                return f"🔢 Last Node Number: {self.geometry.get_last_node_no()}"

            # Beam commands
            elif cmd_type == 'selected_beams':
                beams = self.geometry.get_selected_beams()
                if not beams:
                    return "⚠️ No beams are currently selected."
                result = "📏 Selected Beams:\n"
                for beam in beams:
                    length = self.geometry.get_beam_length(beam)
                    result += f"  • Beam {beam}: {length:.3f} m\n"
                return result

            elif cmd_type == 'beam_length':
                beam = int(params[0])
                length = self.geometry.get_beam_length(beam)
                return f"📏 Beam {beam} Length: {length:.3f} m"

            # File operations
            elif cmd_type == 'create_file':
                file_path = params[0]
                return self.geometry.create_new_staad_file(file_path)

            return None

        except Exception as e:
            logger.error(f"Error executing STAAD command: {e}")
            return f"❌ Error executing command: {str(e)}"

    def get_ai_response(self, prompt: str) -> str:
        """Process user input and get appropriate response"""
        # First, try to parse as STAAD command
        for parser_func in [
            self.command_parser.parse_node_command,
            self.command_parser.parse_beam_command,
            self.command_parser.parse_model_command
        ]:
            command = parser_func(prompt)
            if command:
                result = self.execute_staad_command(command)
                if result:
                    return result

        # If not a direct STAAD command, enhance prompt with context
        enhanced_prompt = prompt
        if self.geometry:
            enhanced_prompt = f"{prompt}\n\n[Context: STAAD.Pro is connected and active]"

        # Get AI response
        return self.ai_provider.get_response(enhanced_prompt)

    def handle_ai_response(self, message: str, reply: str):
        """Handle and display AI response"""
        if "❌" in reply or "error" in reply.lower():
            self.display_message("System", reply, "error")
        elif "⚠️" in reply or "warning" in reply.lower():
            self.display_message("System", reply, "warning")
        else:
            self.display_message("System", reply, "bold_blue")
        self.user_input.delete(0, "end")
        self.hide_loading()

    def send_message(self):
        """Send user message and get AI response"""
        message = self.user_input.get().strip()
        if not message:
            return

        self.user_input.delete(0, "end")
        self.show_loading()
        self.display_message("User", message, "bold_green")

        def run():
            reply = self.get_ai_response(message)
            self.window.after(0, lambda: self.handle_ai_response(message, reply))

        threading.Thread(target=run, daemon=True).start()

    def clear_conversation(self):
        """Clear conversation history and offer login option"""
        # Clear history
        self.ai_provider.clear_history()
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", "end")
        self.text_area.config(state="disabled")

        # Show options dialog
        response = messagebox.askyesnocancel(
            "Clear Conversation",
            "Conversation cleared!\n\n"
            "Would you like to login to ChatGPT for enhanced AI responses?\n\n"
            "• Yes - Open ChatGPT login page\n"
            "• No - Continue without login\n"
            "• Cancel - Just cleared conversation",
            icon='question'
        )

        if response is True:  # Yes clicked
            self.ai_provider.prompt_chatgpt_login()
        elif response is False:  # No clicked
            self.display_message(
                "System",
                "Continuing with standard g4f providers. You can login anytime by clicking Clear again.",
                "bold_blue"
            )

        logger.info("Conversation cleared")

    def run(self):
        """Initialize and run the application"""
        self.setup_window()
        self.setup_images()
        self.setup_text_area()
        self.setup_loading_label()
        self.setup_input_field()
        self.setup_buttons()

        # Display welcome message
        welcome_msg = (
            "Welcome to STAAD GPT! 🏗️\n\n"
            "I'm your AI assistant for structural engineering powered by g4f.\n"
            "Ask me anything about STAAD.Pro or structural analysis!\n\n"
            "💡 Tips:\n"
            "• Ask specific questions about beams, nodes, or analysis.\n"
            "• Request sample STAAD command file codes.\n"
            "• This tool is free, so responses may be slow — feel free to enhance it directly in the code."

        )
        self.display_message("System", welcome_msg, "bold_blue")

        logger.info("Application started with g4f")
        self.window.mainloop()


def main():
    """Application entry point"""
    try:
        app = STAADGPTApp()
        app.run()
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        messagebox.showerror("Critical Error", f"Application failed to start: {e}")


if __name__ == "__main__":
    main()