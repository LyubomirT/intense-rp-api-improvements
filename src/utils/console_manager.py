"""
Console management module for IntenseRP API
Handles console window creation, styling, and output redirection
"""

import sys
import tkinter as tk
from typing import Dict, Any, Optional, Callable
import utils.gui_builder as gui_builder


class ConsoleRedirector:
    """Redirects stdout/stderr to console window"""
    
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback

    def write(self, text: str) -> None:
        if text and text.strip():
            try:
                self.callback(text.rstrip('\n')) 
            except Exception:
                pass
    
    def flush(self) -> None:
        pass


class ConsoleColorPalettes:
    """Predefined color palettes for the console"""
    
    # Current palette (modern/muted)
    MODERN = {
        "red": "#ff6b6b",
        "green": "#51cf66", 
        "yellow": "#ffd43b",
        "blue": "#74c0fc",
        "cyan": "#66d9ef",
        "white": "#f8f9fa",
        "purple": "#d084f5",
        "orange": "#ff8c42",
        "pink": "#f783ac",
        "gray": "#adb5bd"
    }
    
    # Original IntenseRP palette
    CLASSIC = {
        "red": "red",
        "green": "#13ff00",
        "yellow": "yellow",
        "blue": "blue",
        "cyan": "cyan",
        "white": "white",
        "purple": "#e400ff",
        "orange": "orange",
        "pink": "pink",
        "gray": "#adb5bd"
    }

    # New bright palette
    BRIGHT = {
        "red": "#ff3333",
        "green": "#00ff88", 
        "yellow": "#ffdd00",
        "blue": "#3399ff",
        "cyan": "#00ffff",
        "white": "#ffffff",
        "purple": "#bb44ff",
        "orange": "#ff7722",
        "pink": "#ff66cc",
        "gray": "#888888"
    }
    
    @classmethod
    def get_palette(cls, name: str) -> Dict[str, str]:
        """Get palette by name"""
        palettes = {
            "Modern (Redesigned)": cls.MODERN,
            "Classic (OG IntenseRP)": cls.CLASSIC,
            "Bright (New Palette)": cls.BRIGHT
        }
        return palettes.get(name, cls.MODERN)
    
    @classmethod
    def get_palette_names(cls) -> list[str]:
        """Get list of available palette names"""
        return ["Modern (Redesigned)", "Classic (OG IntenseRP)", "Bright (New Palette)"]


class ConsoleSettings:
    """Console configuration settings"""
    
    # Cross-platform font families
    FONT_FAMILIES = [
        "Consolas",      # Windows default, good monospace
        "Monaco",        # Mac default monospace
        "DejaVu Sans Mono",  # Linux common
        "Courier New",   # Cross-platform monospace
        "Arial",         # Cross-platform sans-serif
        "Times New Roman", # Cross-platform serif
        "Lucida Console" # Windows monospace alternative
    ]
    
    # Font size options
    FONT_SIZES = [8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 22, 24]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        console_config = config.get("console", {}) if config else {}
        
        self.font_family = console_config.get("font_family", "Consolas")
        self.font_size = console_config.get("font_size", 12)
        self.color_palette = console_config.get("color_palette", "Modern")
        self.word_wrap = console_config.get("word_wrap", True)
        
        # Ensure valid values
        if self.font_family not in self.FONT_FAMILIES:
            self.font_family = "Consolas"
        if self.font_size not in self.FONT_SIZES:
            self.font_size = 12
        if self.color_palette not in ConsoleColorPalettes.get_palette_names():
            self.color_palette = "Modern"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "color_palette": self.color_palette,
            "word_wrap": self.word_wrap
        }
    
    def get_font_tuple(self) -> tuple:
        """Get font as tuple for tkinter"""
        return (self.font_family, self.font_size)
    
    def get_color_map(self) -> Dict[str, str]:
        """Get color mapping for current palette"""
        return ConsoleColorPalettes.get_palette(self.color_palette)


class CustomConsoleTextbox(gui_builder.CustomTextbox):
    """Console textbox with customizable styling"""
    
    def __init__(self, parent, settings: ConsoleSettings, **kwargs):
        self.settings = settings
        
        # Apply console-specific styling
        console_kwargs = {
            "state": "disabled",
            "font": self.settings.get_font_tuple(),
            "wrap": "word" if self.settings.word_wrap else "none",
            "border_width": 1,
            "border_color": ("gray60", "gray40"),
            "corner_radius": 4,
            "fg_color": ("gray10", "gray5"),
            "text_color": ("gray90", "gray90"),
            "scrollbar_button_color": ("gray70", "gray30"),
            "scrollbar_button_hover_color": ("gray60", "gray40")
        }
        
        # Override with any provided kwargs
        console_kwargs.update(kwargs)
        
        super().__init__(parent, **console_kwargs)
        
        # Apply custom color palette
        self.apply_color_palette()
    
    def apply_color_palette(self) -> None:
        """Apply the selected color palette"""
        self._color_map = self.settings.get_color_map()
        
        # Configure color tags
        for tag, color in self._color_map.items():
            self.tag_config(tag, foreground=color)
    
    def update_settings(self, settings: ConsoleSettings) -> None:
        """Update console settings and refresh appearance"""
        self.settings = settings
        
        # Update font
        self.configure(font=self.settings.get_font_tuple())
        
        # Update word wrap
        self.configure(wrap="word" if self.settings.word_wrap else "none")
        
        # Update color palette
        self.apply_color_palette()


class ConsoleManager:
    """Manages console window and related functionality"""
    
    def __init__(self, state_manager, storage_manager):
        self.state_manager = state_manager
        self.storage_manager = storage_manager
        self.console_window = None
        self.console_textbox = None
        self.menu_frame = None
        self.settings = None
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def initialize(self, config: Dict[str, Any], icon_path: Optional[str] = None) -> None:
        """Initialize console with configuration"""
        self.settings = ConsoleSettings(config)
        self._create_console_window(icon_path)
        
    def _create_console_window(self, icon_path: Optional[str] = None) -> None:
        """Create the console window"""
        try:
            console_window = gui_builder.ConsoleWindow()
            console_window.create(
                visible=False,
                title="Console Output",
                width=700,
                height=400,
                min_width=400,
                min_height=250,
                icon=icon_path
            )
            console_window.protocol("WM_DELETE_WINDOW", lambda: None)
            
            # Create main container frame
            main_frame = gui_builder.ctk.CTkFrame(console_window, fg_color="transparent")
            main_frame.pack(expand=True, fill="both", padx=2, pady=2)
            main_frame.grid_rowconfigure(0, weight=1)  # Console textbox gets full height
            main_frame.grid_rowconfigure(1, weight=0)  # Menu frame fixed height
            main_frame.grid_columnconfigure(0, weight=1)
            
            # Create custom textbox with settings
            console_textbox = CustomConsoleTextbox(
                main_frame,
                self.settings
            )
            console_textbox.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            
            # Create menu frame if needed
            menu_frame = self._create_menu_frame_if_needed(main_frame)
            if menu_frame:
                menu_frame.grid(row=1, column=0, sticky="ew", padx=2, pady=(2, 0))
            
            # Store references
            self.console_window = console_window
            self.console_textbox = console_textbox
            self.menu_frame = menu_frame
            
            # Update state manager
            self.state_manager.console_window = console_window
            
            # Setup output redirection
            self._setup_output_redirection()
            
            print("[color:green]Console window created and ready.")
            
        except Exception as e:
            print(f"Error creating console window: {e}")
    
    def _create_menu_frame_if_needed(self, parent) -> Optional:
        """Create menu frame if any menu-triggering settings are enabled"""
        try:
            # Check if console dumping is enabled using the proper StateManager method
            dump_enabled = self.state_manager.get_config_value('console.dump_enabled', False)
            
            # If no menu options are enabled, don't create menu frame
            if not dump_enabled:
                return None
            
            # Create menu frame
            menu_frame = gui_builder.ctk.CTkFrame(parent, height=40, fg_color=("gray95", "gray15"))
            menu_frame.grid_propagate(False)  # Maintain fixed height
            
            # Create horizontal button container
            button_container = gui_builder.ctk.CTkFrame(menu_frame, fg_color="transparent")
            button_container.pack(expand=True, fill="both", padx=5, pady=5)
            
            button_column = 0
            
            # Add Dump Console button if enabled
            if dump_enabled:
                dump_button = gui_builder.ctk.CTkButton(
                    button_container,
                    text="Dump Console",
                    command=self._dump_console,
                    width=100,
                    height=30,
                    font=("Consolas", 12)
                )
                dump_button.grid(row=0, column=button_column, padx=(0, 5), sticky="w")
                button_column += 1
            
            return menu_frame
            
        except Exception as e:
            print(f"Error creating menu frame: {e}")
            return None
    
    def _dump_console(self) -> None:
        """Dump current console content to a file"""
        try:
            if not self.console_textbox:
                print("[color:red]Error: Console textbox not available")
                return
            
            # Get current console content
            console_content = self.console_textbox.get("1.0", "end-1c")
            
            if not console_content.strip():
                print("[color:yellow]Console is empty - nothing to dump")
                return
            
            # Get dump directory from config
            dump_directory = self.state_manager.get_config_value('console.dump_directory', '').strip()
            
            # Use default directory if not specified
            if not dump_directory:
                import os
                # Get project root directory
                project_root = self.storage_manager.get_base_path()
                dump_directory = os.path.join(project_root, 'condumps')
            
            # Create directory if it doesn't exist
            import os
            os.makedirs(dump_directory, exist_ok=True)
            
            # Generate filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"console_dump_{timestamp}.txt"
            filepath = os.path.join(dump_directory, filename)
            
            # Write console content to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(console_content)
            
            print(f"[color:green]Console dumped successfully to: {filepath}")
            
        except Exception as e:
            print(f"[color:red]Error dumping console: {e}")
    
    def _setup_output_redirection(self) -> None:
        """Setup stdout/stderr redirection to console"""
        try:
            if self.console_textbox:
                # Redirect stdout and stderr to console
                sys.stdout = ConsoleRedirector(self.console_textbox.colored_add)
                sys.stderr = ConsoleRedirector(
                    lambda text: self.console_textbox.colored_add(f"[color:red]ERROR: {text}")
                )
                
                # Also try to capture subprocess and webdriver outputs
                self._setup_enhanced_logging()
                
        except Exception as e:
            print(f"Error setting up output redirection: {e}")
            # Restore original streams on error
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
    
    def _setup_enhanced_logging(self) -> None:
        """Set up enhanced logging to catch webdriver/subprocess errors"""
        try:
            import logging
            import subprocess
            
            # Create a custom log handler that writes to console
            class ConsoleLogHandler(logging.Handler):
                def __init__(self, console_callback):
                    super().__init__()
                    self.console_callback = console_callback
                
                def emit(self, record):
                    try:
                        msg = self.format(record)
                        level_colors = {
                            'ERROR': 'red',
                            'WARNING': 'yellow',
                            'INFO': 'cyan',
                            'DEBUG': 'gray'
                        }
                        color = level_colors.get(record.levelname, 'white')
                        self.console_callback(f"[color:{color}]LOG {record.levelname}: {msg}")
                    except Exception:
                        pass
            
            # Add handler to root logger
            root_logger = logging.getLogger()
            console_handler = ConsoleLogHandler(self.console_textbox.colored_add)
            console_handler.setLevel(logging.DEBUG)
            root_logger.addHandler(console_handler)
            root_logger.setLevel(logging.DEBUG)
            
            # Also add to selenium/webdriver loggers specifically
            selenium_logger = logging.getLogger('selenium')
            selenium_logger.addHandler(console_handler)
            selenium_logger.setLevel(logging.DEBUG)
            
            webdriver_logger = logging.getLogger('webdriver')
            webdriver_logger.addHandler(console_handler)
            webdriver_logger.setLevel(logging.DEBUG)
            
            # Store handlers for cleanup
            self._log_handlers = [console_handler]
            
            print("[color:cyan]Enhanced logging set up - webdriver errors should now appear in console")
            
        except Exception as e:
            print(f"Error setting up enhanced logging: {e}")
    
    def restore_output_streams(self) -> None:
        """Restore original stdout/stderr"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
    
    def update_settings(self, new_settings: ConsoleSettings) -> None:
        """Update console settings"""
        self.settings = new_settings
        
        if self.console_textbox:
            self.console_textbox.update_settings(new_settings)
        
        # Refresh menu in case dump settings changed
        self._refresh_menu()
    
    def _refresh_menu(self) -> None:
        """Refresh the console menu based on current settings"""
        try:
            if not self.console_window:
                return
            
            # Get the main frame (parent of textbox and menu)
            main_frame = None
            for child in self.console_window.winfo_children():
                if isinstance(child, gui_builder.ctk.CTkFrame):
                    main_frame = child
                    break
            
            if not main_frame:
                return
            
            # Remove existing menu frame if it exists
            if self.menu_frame:
                self.menu_frame.destroy()
                self.menu_frame = None
            
            # Create new menu frame if needed
            new_menu_frame = self._create_menu_frame_if_needed(main_frame)
            if new_menu_frame:
                new_menu_frame.grid(row=1, column=0, sticky="ew", padx=2, pady=(2, 0))
            
            self.menu_frame = new_menu_frame
            
        except Exception as e:
            print(f"Error refreshing console menu: {e}")
    
    def show(self, show: bool, root_window=None, center: bool = True) -> None:
        """Show or hide console window"""
        if self.console_window:
            self.console_window.show(show, root_window, center)
    
    def is_visible(self) -> bool:
        """Check if console window is visible"""
        if self.console_window:
            return self.console_window.winfo_viewable() == 1
        return False
    
    def clear(self) -> None:
        """Clear console content"""
        if self.console_textbox:
            self.console_textbox.clear()
    
    def add_message(self, text: str) -> None:
        """Add message to console"""
        if self.console_textbox:
            self.console_textbox.colored_add(text)
    
    def get_settings_dict(self) -> Dict[str, Any]:
        """Get current settings as dictionary"""
        return self.settings.to_dict() if self.settings else {}
    
    def cleanup(self) -> None:
        """Cleanup console resources"""
        # Clean up logging handlers
        if hasattr(self, '_log_handlers'):
            import logging
            root_logger = logging.getLogger()
            for handler in self._log_handlers:
                root_logger.removeHandler(handler)
        
        self.restore_output_streams()
        
        if self.console_window:
            try:
                self.console_window.destroy()
            except Exception:
                pass
            
        self.console_window = None
        self.console_textbox = None
        self.menu_frame = None