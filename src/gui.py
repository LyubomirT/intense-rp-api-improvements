import threading, webbrowser, api, sys, re, platform, tkinter as tk
import utils.response_utils as response_utils
import utils.deepseek_driver as deepseek
import utils.process_manager as process
import utils.gui_builder as gui_builder
import utils.console_manager as console_manager
import utils.webdriver_utils as selenium
from packaging import version
from core import get_state_manager, StateEvent

# New modular config system imports
from config.config_manager import ConfigManager
from config.config_ui_generator import ConfigUIGenerator

__version__ = "2.7.0"

# Local GUI state (not shared across modules)
root = None
storage_manager = None
config_manager = None
icon_path = None

# =============================================================================================================================
# Modal Window Management
# =============================================================================================================================

def make_window_modal(window, parent_window):
    """
    Make a window modal in a cross-platform way that preserves Mica effect on Windows 11.
    On Windows, we avoid using transient() to preserve the Mica backdrop effect.
    """
    is_windows = platform.system() == "Windows"
    
    if not is_windows:
        # On non-Windows platforms, use traditional transient approach
        window.transient(parent_window)
        window.grab_set()
    else:
        # On Windows, we use alternative approach to preserve Mica effect
        # This makes the window always on top and handle focus manually
        window.attributes("-topmost", True)
        window.grab_set()
        
        # Bind focus events to maintain modal behavior
        def on_parent_focus(_event=None):
            if window.winfo_exists():
                window.focus_force()
                window.lift()
        
        binding_id = parent_window.bind("<FocusIn>", on_parent_focus)
        
        # Store the binding ID and parent for cleanup
        setattr(window, '_parent_focus_binding_id', binding_id)
        setattr(window, '_parent_window', parent_window)

        # UNFORTUNATELY, this also means that all of the normal built-in modal behaviors
        # ... now must be written manually. Tell Microsoft I want to have my cake and eat it too.
        #                                                                           - Lyubomir
        #
        #
        # If you're reading this, it's likely I've been hunted down by Microsoft for this comment.
        
        # Override destroy to clean up bindings
        original_destroy = window.destroy
        def cleanup_and_destroy():
            try:
                if hasattr(window, '_parent_window') and hasattr(window, '_parent_focus_binding_id'):
                    parent = getattr(window, '_parent_window')
                    binding_id = getattr(window, '_parent_focus_binding_id')
                    
                    if parent.winfo_exists():
                        parent.unbind("<FocusIn>", binding_id)
            except (AttributeError, tk.TclError):
                pass
            finally:
                original_destroy()
        
        window.destroy = cleanup_and_destroy
    
    # Common modal setup
    window.focus_force()
    window.lift()

# =============================================================================================================================
# Console Window
# =============================================================================================================================

def create_console_window() -> None:
    """Create console window using the new console manager"""
    state = get_state_manager()
    
    try:
        # Initialize console manager
        console_mgr = console_manager.ConsoleManager(state, storage_manager)
        console_mgr.initialize(config_manager.get_all(), icon_path)
        
        # Store console manager in state
        state.console_manager = console_mgr
        
    except Exception as e:
        print(f"Error creating console window: {e}")

def start_services() -> None:
    state = get_state_manager()
    
    try:
        state.clear_messages()
        state.show_message("[color:green]Please wait...")
        threading.Thread(target=api.run_services, daemon=True).start()
    except Exception as e:
        state.clear_messages()
        state.show_message("[color:red]Selenium failed to start.")
        print(f"Error starting services: {e}")

# =============================================================================================================================
# Config Window - Now Using Modular System
# =============================================================================================================================

def on_console_toggle(value: bool) -> None:
    """Handle console window toggle"""
    state = get_state_manager()
    
    try:
        if hasattr(state, 'console_manager') and state.console_manager:
            state.console_manager.show(value, root, center=True)
    except Exception as e:
        print(f"Error when toggling console visibility: {e}")

def preview_console_changes() -> None:
    """Preview console settings changes"""
    state = get_state_manager()
    
    try:
        if hasattr(state, 'console_manager') and state.console_manager:
            # Get current values from config manager
            new_settings = console_manager.ConsoleSettings(config_manager.get_all())
            
            # Apply settings
            state.console_manager.update_settings(new_settings)
            
    except Exception as e:
        print(f"Error applying console settings: {e}")

def clear_browser_data() -> None:
    """Clear browser data (cookies, cache, etc.)"""
    global config_manager
    
    try:
        # Get current browser setting
        browser = config_manager.get("browser", "Chrome").lower()
        
        # Only works for Chromium browsers
        if browser in ("chrome", "edge"):
            success = selenium.clear_browser_data(browser)
            if success:
                print(f"[color:green]Browser data cleared for {browser.title()}")
            else:
                print(f"[color:red]Failed to clear browser data for {browser.title()}")
        else:
            print(f"[color:yellow]Browser data clearing not supported for {browser.title()}")
            
    except Exception as e:
        print(f"[color:red]Error clearing browser data: {e}")

def open_config_window() -> None:
    """Open configuration window using the new modular system"""
    global root, config_manager
    state = get_state_manager()
    
    try:
        # Set up command handlers for special actions
        command_handlers = {
            'on_console_toggle': on_console_toggle,
            'preview_console_changes': preview_console_changes,
            'clear_browser_data': clear_browser_data,
        }
        
        # Create UI generator
        ui_generator = ConfigUIGenerator(config_manager, command_handlers)
        
        # Create and show window
        config_window = ui_generator.create_config_window(icon_path)
        make_window_modal(config_window, root)
        config_window.center(root)
        
        # Store in state for reference
        state.config_window = config_window
        
        print("Settings window created with new modular system.")
        
    except Exception as e:
        print(f"Error opening config window: {e}")

# =============================================================================================================================
# Credits
# =============================================================================================================================

def open_credits() -> None:
    try:
        webbrowser.open("https://linktr.ee/omega_slender")
        print("Credits link opened.")
    except Exception as e:
        print(f"Error opening credits: {e}")

# =============================================================================================================================
# Update Window
# =============================================================================================================================

def create_update_window(last_version: str) -> None:
    global root, icon_path
    try:
        update_window = gui_builder.UpdateWindow()
        update_window.create(
            visible=True,
            title=f"New version available",
            width=250,
            height=110,
            icon=icon_path
        )
        update_window.resizable(False, False)
        # Use cross-platform modal approach that preserves Mica on Windows
        make_window_modal(update_window, root)
        update_window.center(root)
        update_window.grid_columnconfigure(0, weight=1)

        update_window.create_title(id="title", text=f"VERSION {last_version} AVAILABLE", row=0, row_grid=True)
        update_window.create_button(id="download", text="Download", command=lambda: open_github(update_window), row=1, row_grid=True)
        update_window.create_button(id="close", text="Close", command=update_window.destroy, row=2, row_grid=True)

        print("Update window created.")
    except Exception as e:
        print(f"Error opening update window: {e}")

def open_github(update_window: gui_builder.UpdateWindow) -> None:
    try:
        webbrowser.open("https://github.com/omega-slender/intense-rp-api")
        update_window.destroy()
        print("Github link opened.")
    except Exception as e:
        print(f"Error opening github: {e}")

# =============================================================================================================================
# Root Window
# =============================================================================================================================

def on_close_root() -> None:
    global root, storage_manager
    state = get_state_manager()
    
    try:
        # Restore console streams using console manager
        if hasattr(state, 'console_manager') and state.console_manager:
            state.console_manager.cleanup()
        else:
            # Fallback to manual restoration
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

        api.close_selenium()
        process.kill_driver_processes()

        temp_files = storage_manager.get_temp_files()
        if temp_files:
            for file in temp_files:
                storage_manager.delete_file("temp", file)

        if root:
            root.destroy()

        print("The program was successfully closed.")
    except Exception as e:
        print(f"Error closing root: {e}")

def create_gui() -> None:
    global __version__, root, storage_manager, config_manager, icon_path
    state = get_state_manager()
    
    try:
        # Initialize storage manager and config system
        import utils.storage_manager as storage
        import utils.logging_manager as logging_manager
        
        storage_manager = storage.StorageManager()
        
        # Initialize new config system
        config_manager = ConfigManager(storage_manager)
        
        logging_manager_instance = logging_manager.LoggingManager(storage_manager)
        icon_path = storage_manager.get_existing_path(path_root="base", relative_path="newlogo.ico")

        # Set up state manager with config manager
        state.set_config_manager(config_manager)
        state.logging_manager = logging_manager_instance

        # Configure external dependencies
        deepseek.manager = storage_manager
        response_utils.__version__ = __version__
        
        gui_builder.apply_appearance()
        root = gui_builder.RootWindow()
        root.create(
            title=f"INTENSE RP API V{__version__}",
            width=400,
            height=500,
            min_width=250,
            min_height=250,
            icon=icon_path
        )
        
        root.grid_columnconfigure(0, weight=1)
        root.protocol("WM_DELETE_WINDOW", on_close_root)
        root.center()
        
        root.create_title(id="title", text=f"INTENSE RP API V{__version__}", row=0)
        textbox = root.create_textbox(id="textbox", row=1, row_grid=True, bg_color="#272727")
        root.create_button(id="start", text="Start", command=start_services, row=2)
        root.create_button(id="settings", text="Settings", command=open_config_window, row=3)
        root.create_button(id="credits", text="Credits", command=open_credits, row=4)
        
        textbox.add_colors()
        
        # Update state with UI components
        state.textbox = textbox
        
        # Create console window after config is loaded
        create_console_window()
        
        # Initialize logging with config data
        logging_manager_instance.initialize(config_manager.get_all())
        
        if config_manager.get("check_version", True):
            current_version = version.parse(__version__)
            last_version = storage_manager.get_latest_version()
            if last_version and version.parse(last_version) > current_version:
                root.after(200, lambda: create_update_window(last_version))
        
        # Show console if configured to do so
        if config_manager.get("show_console", False) and hasattr(state, 'console_manager') and state.console_manager:
            root.after(100, lambda: state.console_manager.show(True, root, center=True))
        
        print("Main window created with new modular config system.")
        print(f"Executable path: {storage_manager.get_executable_path()}")
        print(f"Base path: {storage_manager.get_base_path()}")
        
        root.mainloop()
    except Exception as e:
        print(f"Error creating GUI: {e}")